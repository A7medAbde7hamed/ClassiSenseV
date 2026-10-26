"""Durable SQLite outbox; Firebase work happens exclusively in a worker thread."""
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
import uuid


class Outbox:
    def __init__(self, path):
        self.path = str(path)
        self.lock = threading.Lock()
        self.db = sqlite3.connect(self.path, check_same_thread=False, timeout=0.1)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, kind TEXT, payload TEXT, attempts INTEGER DEFAULT 0, due REAL DEFAULT 0)")
        self.db.commit()

    def enqueue(self, kind, payload):
        with self.lock, self.db:
            # Coalesce live status only; logs/alerts remain durable and ordered.
            if kind == "live":
                self.db.execute("DELETE FROM jobs WHERE kind='live'")
            if self.db.execute("SELECT count(*) FROM jobs").fetchone()[0] >= 100000:
                raise RuntimeError("Outbox full: restore connectivity or archive the database")
            event_id = uuid.uuid4().hex
            self.db.execute("INSERT INTO jobs(id,kind,payload) VALUES(?,?,?)", (event_id, kind, json.dumps(payload, allow_nan=False)))
        return event_id

    def next(self, now=None):
        with self.lock:
            row = self.db.execute("SELECT id,kind,payload,attempts FROM jobs WHERE due<=? ORDER BY CASE kind WHEN 'alert' THEN 0 WHEN 'live' THEN 1 ELSE 2 END,rowid LIMIT 1", (time.time() if now is None else now,)).fetchone()
        return (row[0], row[1], json.loads(row[2]), row[3]) if row else None

    def acknowledge(self, event_id):
        with self.lock, self.db:
            self.db.execute("DELETE FROM jobs WHERE id=?", (event_id,))

    def fail(self, event_id, attempts, now=None):
        with self.lock, self.db:
            self.db.execute("UPDATE jobs SET attempts=?, due=? WHERE id=?", (attempts + 1, (time.time() if now is None else now) + min(60, 2 ** min(attempts, 6)), event_id))

    def count(self):
        with self.lock:
            return self.db.execute("SELECT count(*) FROM jobs").fetchone()[0]

    def close(self):
        with self.lock:
            self.db.close()


class FirebaseSink:
    def __init__(self):
        self.db = None

    def __call__(self, kind, event_id, data):
        import firebase_admin
        from firebase_admin import credentials, firestore
        if self.db is None:
            key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", str(Path(__file__).parent / "serviceAccountKey.json"))
            try:
                app = firebase_admin.get_app("classisense")
            except ValueError:
                app = firebase_admin.initialize_app(credentials.Certificate(key), name="classisense")
            self.db = firestore.client(app=app)
        payload = dict(data, updated_at=firestore.SERVER_TIMESTAMP)
        if kind == "live":
            self.db.collection("classroom").document("live_status").set(payload, timeout=5)
        else:
            # Stable event ID makes retry after a lost response idempotent.
            collection = "alerts" if kind == "alert" else "monitoring_logs"
            self.db.collection(collection).document(event_id).set(dict(payload, created_at=firestore.SERVER_TIMESTAMP), timeout=5)


class DatabaseManager:
    def __init__(self, queue_path=None, sink=None, start_worker=True):
        path = Path(queue_path or os.getenv("CLASSISENSE_OUTBOX", str(Path.home() / ".classisense" / "outbox.sqlite3")))
        path.parent.mkdir(parents=True, exist_ok=True)
        self.outbox = Outbox(path)
        self.sink = sink or FirebaseSink()
        self.last_live = None
        self.last_log = None
        self.last_alert = {}
        self._stop = threading.Event()
        self._wake = threading.Event()
        self.last_success = None
        self.last_error = None
        self._thread = None
        if start_worker:
            self._thread = threading.Thread(target=self._run, name="firebase-outbox", daemon=True)
            self._thread.start()

    def process_once(self, now=None):
        job = self.outbox.next(now)
        if not job:
            return False
        event_id, kind, payload, attempts = job
        try:
            self.sink(kind, event_id, payload)
        except Exception as exc:
            self.last_error = type(exc).__name__
            self.outbox.fail(event_id, attempts, now)
        else:
            self.outbox.acknowledge(event_id)
            self.last_error = None
            self.last_success = time.time()
        return True

    def _run(self):
        while not self._stop.is_set():
            if not self.process_once():
                self._wake.wait(0.5)
                self._wake.clear()

    def publish(self, data, now=None):
        now = time.monotonic() if now is None else now
        for kind, attr, interval in (("live", "last_live", 2), ("log", "last_log", 180)):
            previous = getattr(self, attr)
            if previous is None or now - previous >= interval:
                self.outbox.enqueue(kind, data)
                setattr(self, attr, now)
        for field, alert in (("gas_state", "GAS_LEAK"), ("temperature_state", "HIGH_TEMPERATURE")):
            if data.get(field) == "danger" and (alert not in self.last_alert or now-self.last_alert[alert] >= 60):
                self.outbox.enqueue("alert", dict(data, alert_type=alert, severity="CRITICAL"))
                self.last_alert[alert] = now
        self._wake.set()

    def get_hud_status(self):
        return f"Cloud: {'retrying' if self.last_error else 'synced' if self.last_success else 'waiting'} | Queue: {self.outbox.count()}"

    def close(self):
        self._stop.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout=7)
        # If an SDK call is still in progress, leave the DB for that daemon to finish;
        # committed jobs already survive process exit and restart.
        if not self._thread or not self._thread.is_alive():
            self.outbox.close()
