"""
ClassiSense - نظام المراقبة الذكي للقاعات الدراسية
- الكشف عن الطلاب وتتبعهم وتحديد عددهم عبر نموذج YOLO
- التحكم الذكي في إضاءة القاعة وتشغيل الإنذار عبر Arduino
- قراءة حساسات الحرارة (LM35) والغاز (MQ-5)
- إرسال البيانات دورياً كل 3 دقائق لجدول monitoring_logs
- إرسال تنبيه فوري لجدول alerts عند وجود خطر
"""

import sys
import time
from pathlib import Path
import cv2
from ultralytics import YOLO

# إضافة المسار الحالي لـ sys.path لضمان استيراد الملفات بسلاسة
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from arduino_controller import ClassroomController
from database import DatabaseManager


# ==============================================================================
# 1. إعداد وحدة التحكم بالأردوينو (Arduino Controller)
# ==============================================================================
controller = ClassroomController(
    port="COM5",            # بورت الأردوينو
    led_pins=(2,),          # Pin 2: إضاءة الـ LED
    buzzer_pin=3,           # Pin 3: إنذار الـ Buzzer
    gas_digital_pin=4,      # Pin 4: مستشعر الغاز MQ-5 (طرف DO الرقمي فقط)
    gas_analog_pin=None,    # تم إلغاؤه لأن الحساس موصل ديجيتال فقط (قراءة 0 أو 1)
    temp_pin=0,             # Pin A0: مستشعر الحرارة LM35
    empty_delay=10,         # ثواني الانتظار قبل إطفاء النور بعد خروج الطلاب
    sampling_ms=500,        # أخذ عينات كل نصف ثانية لتهدئة وميض لمبة TX ومنفذ السيريال
    enabled=True            # اجعلها False لو بتجرب بدون توصيل الأردوينو
)

# ==============================================================================
# 2. إعداد قاعدة بيانات Firebase Firestore
# ==============================================================================
db_manager = DatabaseManager()

# ==============================================================================
# 3. تحميل نموذج الذكاء الاصطناعي YOLO
# ==============================================================================
# تحميل الموديل (يبحث في المجلد الحالي أو مجلد المشروع الرئيسي)
model_path = "yolo26n.pt"

# إعدادات الـ Detection (مأخوذة من yolo26.py عشان أدق نتيجة)
IMAGE_SIZE  = 640          # حجم الصورة اللي بيشوفها الموديل
CONFIDENCE = 0.15          # threshold منخفض عشان يديتكت أكتر ناس
TRACKER     = "bytetrack.yaml"  # أفضل tracker للتتبع المتواصل

print(f"[INFO] Loading YOLO model: {model_path}")
model = YOLO(model_path)

# ==============================================================================
# 4. فتح الكاميرا (أو ملف الفيديو)
# ==============================================================================
# 0 للكاميرا، أو مسار ملف فيديو مثل "video.mp4"

# cap = cv2.VideoCapture(0)

# if not cap.isOpened() and (CURRENT_DIR / "video.mp4").exists():
#     print("[WARN] Camera not available, falling back to video.mp4")
#     cap = cv2.VideoCapture(str(CURRENT_DIR / "video.mp4"))

cap = cv2.VideoCapture("ai/people-tracking/video.mp4")

# ==============================================================================
# 5. حلقة المعالجة اللحظية للفيديو (Main Loop)
# ==============================================================================
print("[INFO] Starting Classroom Monitoring (Press Q to quit)...")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        # إعادة تشغيل الفيديو تلقائياً لو كان ملف فيديو
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # 1. تتبع الأشخاص باستخدام YOLO — نفس إعدادات yolo26.py بالظبط
    results = model.track(
        frame,
        persist=True,
        tracker=TRACKER,
        classes=[0],           # نفلتر على الناس مباشرةً داخل الموديل
        conf=CONFIDENCE,       # 0.15 — أحساس أعلى للديتكشن
        imgsz=IMAGE_SIZE,      # 640
        device="cpu",
        verbose=False,
    )

    result     = results[0]
    frame      = result.plot()  # يرسم الـ boxes والـ labels تلقائياً زي yolo26.py
    occupancy_count = len(result.boxes) if result.boxes is not None else 0

    # 2. تحديث الأردوينو (التحكم بالأنوار + قراءة الحساسات)
    controller.update(occupancy_count)
    sensor_data = controller.get_sensor_data()

    temp_val = sensor_data.get("temperature_c")
    gas_detected = sensor_data.get("gas_detected", 0)  # 0: مفيش غاز، 1: فيه تسريب غاز
    gas_danger = bool(gas_detected)
    lights_state = "ON" if sensor_data.get("lights_on") else "OFF"
    led_sec = sensor_data.get("led_on_seconds", 0)

    # 3. إرسال البيانات لقاعدة بيانات MySQL
    # أ) تسجيل دوري في monitoring_logs كل 3 دقائق
    db_manager.check_and_log_monitoring(sensor_data)

    # ب) تسجيل فوري في alerts عند وجود تسريب غاز (1) أو حرارة مرتفعة
    db_manager.check_and_trigger_alerts(gas_danger, temp_val)

    # 4. عرض البيانات على شاشة الكاميرا (HUD)
    cv2.putText(frame, f"Occupancy: {occupancy_count}", (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, f"Temp: {temp_val} C" if temp_val else "Temp: Reading...", (30, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
    cv2.putText(frame, "Gas: DANGER (1)" if gas_danger else "Gas: Safe (0)", (30, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if gas_danger else (0, 255, 0), 2)
    cv2.putText(frame, f"Lights: {lights_state} ({led_sec}s)", (30, 145),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
    cv2.putText(frame, db_manager.get_hud_status(), (30, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 255), 2)

    # عرض الفيديو
    cv2.imshow("ClassiSense - Smart Classroom Monitoring", frame)

    # الخروج بالضغط على Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# تحرير الموارد وإغلاق الاتصال بأمان
cap.release()
cv2.destroyAllWindows()
controller.close()
db_manager.close()
print("[INFO] Application exited cleanly.")
