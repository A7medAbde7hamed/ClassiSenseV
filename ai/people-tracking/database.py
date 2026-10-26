"""
ClassiSense - وحدة إدارة قاعدة البيانات السحابية (Firebase Cloud Firestore)
========================================================================
1. تحديث الحالة اللحظية (Live Status) في وثيقة 'classroom/live_status' لتمكين الموقع من التحديث المباشر.
2. تسجيل دوري في مجموعة 'monitoring_logs' كل 3 دقائق (180 ثانية).
3. إرسال إنذار فوري في مجموعة 'alerts' عند وجود خطر (تسريب غاز أو حرارة مرتفعة).
"""

import time
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

# مسار ملف مفتاح الخدمة
CURRENT_DIR = Path(__file__).resolve().parent
KEY_PATH = CURRENT_DIR / "serviceAccountKey.json"

# الفترات الزمنية وحدود الأمان
LOG_INTERVAL = 180       # تسجيل دوري كل 3 دقائق (180 ثانية)
LIVE_SYNC_INTERVAL = 2   # تحديث الحالة اللحظية كل ثانيتين للموقع
TEMP_LIMIT = 45.0        # درجة الحرارة الخطرة (45 مئوية)
ALERT_COOLDOWN = 60      # فترة انتظار (60 ثانية) لمنع تكرار نفس الإنذار


class DatabaseManager:
    def __init__(self):
        self.db = None
        self.last_log_time = 0.0
        self.last_live_sync = 0.0
        self.last_gas_alert = 0.0
        self.last_temp_alert = 0.0
        
        # فتح الاتصال بـ Firebase عند بدء التشغيل
        self.connect()

    def connect(self):
        """فتح الاتصال بـ Firebase Cloud Firestore"""
        if not KEY_PATH.exists():
            print(f"[DB Error] Service account key not found at: {KEY_PATH}")
            self.db = None
            return

        try:
            # تجنب إعادة التهيئة لو تم استدعاؤها مسبقاً
            if not firebase_admin._apps:
                cred = credentials.Certificate(str(KEY_PATH))
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("[DB] Connected to Firebase Firestore successfully.")
        except Exception as e:
            print(f"[DB Error] Failed to connect to Firebase Firestore: {e}")
            self.db = None

    def update_live_status(self, sensor_data):
        """تحديث الحالة الحالية لحظياً للقاعة (Live Document) للموقع"""
        if not self.db:
            return

        now = time.monotonic()
        if now - self.last_live_sync < LIVE_SYNC_INTERVAL:
            return

        try:
            gas_val = sensor_data.get("gas_detected", 0)
            doc_ref = self.db.collection("classroom").document("live_status")
            doc_ref.set({
                "people_count": int(sensor_data.get("people_count", 0)),
                "led_is_on": bool(sensor_data.get("led_is_on", sensor_data.get("lights_on", False))),
                "led_on_seconds": int(sensor_data.get("led_on_seconds", 0)),
                "temperature_c": float(sensor_data.get("temperature_c")) if sensor_data.get("temperature_c") is not None else None,
                "gas_detected": int(gas_val),
                "gas_danger": bool(gas_val),
                "updated_at": firestore.SERVER_TIMESTAMP
            }, merge=True)
            self.last_live_sync = now
        except Exception as e:
            print(f"[DB Live Warning] Failed to update live status: {e}")

    def log_monitoring(self, people_count, led_is_on, led_on_seconds, temp, gas_detected):
        """إدخال سجل دوري جديد في مجموعة monitoring_logs"""
        if not self.db:
            self.connect()
            if not self.db:
                return

        try:
            self.db.collection("monitoring_logs").add({
                "people_count": int(people_count),
                "led_is_on": bool(led_is_on),
                "led_on_seconds": int(led_on_seconds),
                "temperature_c": float(temp) if temp is not None else None,
                "gas_detected": 1 if gas_detected else 0,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            gas_status_str = "DANGER (1)" if gas_detected else "SAFE (0)"
            print(f"[DB Firestore] Logged monitoring record: Students={people_count}, Temp={temp}C, Gas={gas_status_str}")
        except Exception as e:
            print(f"[DB Error] Failed to insert monitoring log to Firestore: {e}")

    def log_alert(self, alert_type, severity, value):
        """إدخال إنذار جديد في مجموعة alerts"""
        if not self.db:
            self.connect()
            if not self.db:
                return

        try:
            self.db.collection("alerts").add({
                "alert_type": str(alert_type),
                "severity": str(severity),
                "measured_value": float(value) if value is not None else None,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            print(f"[DB ALERT Firestore] Hazard alert logged: {alert_type} ({severity}) - Value: {value}")
        except Exception as e:
            print(f"[DB Error] Failed to log alert to Firestore: {e}")

    def check_and_log_monitoring(self, sensor_data):
        """فحص إرسال البيانات الدورية كل 3 دقائق + تحديث الحالة اللحظية"""
        # أولاً: تحديث الحالة اللحظية للموقع
        self.update_live_status(sensor_data)

        # ثانياً: التسجيل الدوري كل 3 دقائق
        now = time.monotonic()
        if self.last_log_time == 0.0 or (now - self.last_log_time >= LOG_INTERVAL):
            self.log_monitoring(
                people_count=sensor_data.get("people_count", 0),
                led_is_on=sensor_data.get("led_is_on", sensor_data.get("lights_on", False)),
                led_on_seconds=sensor_data.get("led_on_seconds", 0),
                temp=sensor_data.get("temperature_c"),
                gas_detected=sensor_data.get("gas_detected", 0)
            )
            self.last_log_time = now

    def check_and_trigger_alerts(self, gas_danger, temperature):
        """فحص المخاطر (تسريب الغاز أو ارتفاع الحرارة) وإرسال التنبيهات لمجموعة alerts"""
        now = time.monotonic()

        # 1. إنذار تسريب الغاز فورياً عند وجود تسريب
        if gas_danger:
            if now - self.last_gas_alert >= ALERT_COOLDOWN:
                self.log_alert("GAS_LEAK", "CRITICAL", 1.0)
                self.last_gas_alert = now

        # 2. إنذار ارتفاع درجة الحرارة
        if temperature is not None and temperature >= TEMP_LIMIT:
            if now - self.last_temp_alert >= ALERT_COOLDOWN:
                self.log_alert("HIGH_TEMPERATURE", "CRITICAL", temperature)
                self.last_temp_alert = now

    def get_hud_status(self):
        """نص حالة قاعدة البيانات لعرضه على شاشة الكاميرا/الفيديو"""
        if not self.db:
            return "Firebase: Offline"
        remaining = max(0, int(LOG_INTERVAL - (time.monotonic() - self.last_log_time)))
        return f"Firebase: Online (Next: {remaining}s)"

    def close(self):
        """إغلاق الموارد عند إنهاء البرنامج"""
        self.db = None
        print("[DB] Firebase session closed.")
