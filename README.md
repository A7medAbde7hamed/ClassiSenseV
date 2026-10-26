# ClassiSenseV · Classroom Observatory

An experimental copy of [WalidAhmed89/ClassiSense](https://github.com/WalidAhmed89/ClassiSense), isolated for review and Vercel testing. The original repository is unchanged.

The application combines a local YOLO/ByteTrack process, an Arduino with an autonomous gas alarm, a durable Firebase upload outbox, and a blue/violet PWA dashboard. Vercel hosts the dashboard and read-only API; video processing and hardware control remain on the classroom computer and Arduino.

## What is implemented

- Arduino-owned MQ-5 buzzer logic. No video frame, cloud request, or computer connection is required for the gas alarm loop.
- Versioned JSON telemetry over USB Serial, handled in a separate Python reader thread.
- Sensor states: `healthy`, `danger`, `disconnected`, `stale`. A missing reading is never presented as safe.
- Durable SQLite outbox with worker-thread uploads, bounded exponential backoff, live-status coalescing, alert priority, and idempotent event IDs.
- Path-independent command-line capture runner; bounded read retries; deterministic cleanup after failure.
- Live data, occupancy history, alert filtering, device freshness, CSV export, password-protected live workspace and explicit demo mode.
- Installable PWA with standalone manifest, regular/maskable icons and an offline interface. API responses, authentication, and live readings are never cached by the service worker.
- Per-frame CSV metrics and count evaluation against manually annotated frames.
- Automated Python, Node, and native firmware simulation tests; CI additionally compiles the sketch for Arduino Uno.

## Quick start: dashboard

Requires Node.js 24. The dashboard and API have no npm runtime dependencies.

```bash
npm ci
npm run dev
# http://localhost:3000
```

Open **Explore demo** for explicitly labelled sample data, or append `?demo=1`. The default workspace shows a setup state until live data is configured. A sample seating schematic does not locate or identify individual students.

```bash
npm run build
npm test
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Connect a TEST Firebase project

1. Create or select a dedicated **test** Firebase project with Cloud Firestore enabled. Do not point this experimental fork at the leader's production database.
2. In Vercel project environment variables, set:
   - `FIREBASE_SERVICE_ACCOUNT_JSON`: the complete service-account JSON, stored as a server-only Secret.
   - `DASHBOARD_PASSWORD`: a long random workspace password, stored as a server-only Secret.
3. Redeploy, then open **Connection settings** and enter the workspace password. Live endpoints fail closed when authentication is missing.
4. On the local CV computer, set `GOOGLE_APPLICATION_CREDENTIALS` to a service-account key for the same test project, outside the repository. The historical fallback path `ai/people-tracking/serviceAccountKey.json` is supported and gitignored.
5. Run the tracker. Live status is queued every 2 seconds, history every 180 seconds, hazards immediately with a 60-second repeat cooldown.

The API uses server-side Google OAuth and Firestore REST. No Firebase service-account key or workspace password is shipped to the browser. Sessions use an eight-hour signed HttpOnly, Secure, SameSite cookie. Use HTTPS (Vercel or another TLS proxy) when testing login; the plain HTTP local dev server is for demo/setup mode.

The client polls every 10 seconds. A last sample older than 15 seconds is shown as stale. Legacy `main` records without `sampled_at` and sensor states are not treated as verified live telemetry. New history starts when the updated tracker begins sending readings.

Suggested Firestore client rules for this server-only access pattern:

```text
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} { allow read, write: if false; }
  }
}
```

Deploy these rules in the **test project** after reviewing them. Admin SDK / service-account access uses IAM, so rules do not restrict that account. For sharing beyond a small test workspace, replace the shared password with per-user authentication, configure edge rate limiting, and assign narrower service-account permissions.

## Upload the Arduino firmware first

**The new Python bridge is incompatible with StandardFirmata.** Upload `firmware/classisense/classisense.ino` with Arduino IDE (Uno or Nano), then close the serial monitor before starting Python. No additional Arduino libraries are required.

| Component | Pin | Notes |
|---|---|---|
| Classroom LED | D2 | Series resistor; use an appropriate driver for larger loads |
| Active buzzer | D3 | Verify electrical requirements for your buzzer |
| MQ-5 DO | D4 | Active LOW; powered from the correct supply |
| LM35 Vout | A0 | 5 V ADC reference configured in the sketch |
| Ground | GND | Common ground |

Serial: **115200 baud**. Protocol v1 emits a full JSON snapshot every 500 ms. The only host command is `OCCUPANCY <integer>\n`; there is deliberately no remote command to silence the gas alarm.

- Gas LOW drives the buzzer immediately, including during warmup.
- Gas HIGH during the first 60 seconds is shown as `stale` (warmup), not healthy. Tune warmup/calibration to the actual sensor and its datasheet; first-use conditioning may take longer.
- No host heartbeat for 15 seconds leaves lighting ON; the local gas loop continues.
- No occupancy for 10 seconds with a connected host turns lighting OFF.
- A digital MQ-5 DO line **cannot reliably distinguish safe HIGH from a disconnected cable**. A real wire/power diagnostic needs additional circuitry and protocol support. The UI discloses this limitation.
- LM35 rail/out-of-range readings are marked disconnected. A floating input can produce plausible values; reliable cable diagnosis also requires hardware design. Do not claim cable-fault coverage from range checking alone.

Prototype sensors and this code are not certified fire/gas safety equipment. Keep any required certified safety system in place.

See [hardware checks](docs/hardware-acceptance.md) before testing with devices.

## Run the local tracker

Python 3.12 is used by CI and the recorded benchmark. Install CPU/GPU PyTorch as appropriate for your machine, then the pinned application requirements:

```bash
python -m venv .venv
# Activate .venv for your platform
python -m pip install -r ai/people-tracking/requirements.txt
python ai/people-tracking/tracker.py --port COM5 --source 0
```

For an offline video test with no Arduino or Firebase:

```bash
python ai/people-tracking/tracker.py --source ai/people-tracking/video.mp4 \
  --no-hardware --no-cloud --headless --max-frames 120 \
  --metrics reports/metrics.csv
```

Paths are resolved against the repository root, regardless of the shell working directory. Cameras default to index 0. Files stop at EOF; `--loop` explicitly enables looping. `--device`, `--confidence`, `--imgsz`, and `--max-frames` are configurable. Press Q in GUI mode or Ctrl+C to stop.

Default input size is 960 with confidence 0.2. The count measures visible detected **people**, including teachers; it does not identify students, register named attendance, or count entry/exit events. FPS is processing throughput, not source video FPS.

## Outbox behavior and recovery

Default database: `~/.classisense/outbox.sqlite3`. Override with `CLASSISENSE_OUTBOX`. Use local durable storage, not a network share.

- Producer transactions only touch SQLite; network calls run in a worker.
- Failed jobs remain committed and are retried with backoff (1–60 seconds).
- Live snapshots coalesce to the latest pending snapshot. Historical samples and alerts retain their event IDs across retries and restarts.
- A successful write is acknowledged only after the server responds. Retrying `.set()` with the same document ID prevents duplicate event documents.
- Queue capacity is 100,000 records. Disk-full/queue-full errors are surfaced rather than silently dropping history. Restore connectivity or archive the database before retrying.
- Shutdown waits up to 7 seconds for the worker. Committed unfinished jobs remain on disk for the next run.

## Firestore data contract

| Path | Purpose |
|---|---|
| `classroom/live_status` | Latest classroom snapshot |
| `monitoring_logs/{event_id}` | Periodic historical samples |
| `alerts/{event_id}` | Hazard snapshots with `alert_type` and `severity` |

Snapshots include `sampled_at` (Unix seconds), `people_count`, `temperature_c` (nullable), `gas_detected` (nullable), `gas_state`, `temperature_state`, `controller_state`, `source_state`, `sensor_age_seconds`, `lights_on` (nullable), `buzzer_on` (nullable), `led_on_seconds`, `fps`, and `inference_ms`. `updated_at`/`created_at` are server timestamps; freshness is determined from sample time so delayed uploads cannot look newly sampled.

The dashboard supports 24h/7d/30d queries, bounded to the most recent 1,000 history documents and 1,000 alerts per request. Truncation is displayed. Larger deployments should add pagination/aggregation and per-room identities.

## Accuracy and performance

See [the benchmark report](docs/benchmark.md) and [manual reference counts](docs/ground-truth-sample.csv). To evaluate your own annotated data:

```bash
python tools/evaluate_counts.py reports/metrics.csv docs/ground-truth-sample.csv \
  --output reports/evaluation.json
```

Reference CSV format: `frame,people_count`. Annotate original frames independently of predictions. This tool reports MAE, RMSE, bias, exact-count rate, within-one rate and median throughput; it does not invent accuracy when reference labels are absent.

## Repository layout

```text
ai/people-tracking/   Local CV runner, serial bridge and Firebase outbox
firmware/classisense/ Standalone Arduino sketch
public/               PWA dashboard and assets
api/                  Vercel read-only data and session endpoints
lib/                  Google OAuth, Firestore decoding, session signing
tests/                Network/sensor/capture/auth tests and firmware simulation
tools/                Dev server, web checks and count evaluation
docs/                 Benchmark, deployment and hardware acceptance notes
```

The original aspirational README is retained in `docs/original-project-vision.md`; its Spring Boot/PostgreSQL and future ML features are not part of this implementation.
