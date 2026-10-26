"""ClassiSense capture runner. Import-safe; all resources have deterministic cleanup."""
import argparse
import csv
import os
from pathlib import Path
import time
from arduino_controller import ClassroomController
from database import DatabaseManager

ROOT = Path(__file__).resolve().parents[2]


def capture_source(value):
    if value.isdigit():
        return int(value)
    path = Path(value).expanduser()
    return str(path if path.is_absolute() else ROOT / path)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="0", help="Camera index or file path relative to repository root")
    parser.add_argument("--model", default="yolo26n.pt")
    parser.add_argument("--port", default=os.getenv("CLASSISENSE_PORT"))
    parser.add_argument("--no-hardware", action="store_true")
    parser.add_argument("--no-cloud", action="store_true")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--loop", action="store_true", help="Explicitly loop video files")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--confidence", type=float, default=0.2)
    parser.add_argument("--imgsz", type=int, default=960, help="YOLO input size; larger images help small or occluded people")
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--metrics", help="Write per-frame count and FPS as CSV")
    args = parser.parse_args(argv)
    import cv2
    from ultralytics import YOLO
    controller = db = cap = metrics_file = None
    try:
        model = YOLO(str(capture_source(args.model)))
        source = capture_source(args.source)
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {source}")
        controller = ClassroomController(port=args.port, enabled=not args.no_hardware)
        db = None if args.no_cloud else DatabaseManager()
        writer = None
        if args.metrics:
            Path(args.metrics).parent.mkdir(parents=True, exist_ok=True)
            metrics_file = open(args.metrics, "w", newline="", encoding="utf-8")
            writer = csv.writer(metrics_file)
            writer.writerow(["frame", "video_seconds", "people_count", "inference_ms", "fps"])
        frame_number = failures = 0
        last_frame_time = time.monotonic()
        while True:
            success, frame = cap.read()
            if not success:
                failures += 1
                if isinstance(source, str):
                    if args.loop and failures <= 3:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    break
                if failures >= 5:
                    raise RuntimeError("Camera stopped producing frames")
                time.sleep(0.1)
                continue
            failures = 0
            started = time.perf_counter()
            result = model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[0], conf=args.confidence, imgsz=args.imgsz, device=args.device, verbose=False)[0]
            inference_ms = (time.perf_counter()-started)*1000
            count = len(result.boxes) if result.boxes is not None else 0
            now = time.monotonic()
            fps = 1 / max(now-last_frame_time, 0.000001)
            last_frame_time = now
            data = controller.update(count)
            data.update(fps=round(fps, 2), inference_ms=round(inference_ms, 2), source_state="healthy")
            if db:
                db.publish(data)
            if writer:
                writer.writerow([frame_number, cap.get(cv2.CAP_PROP_POS_MSEC)/1000, count, round(inference_ms, 2), round(fps, 2)])
            if not args.headless:
                shown = result.plot()
                lines = [f"Occupancy: {count} | FPS: {fps:.1f}", f"Gas: {data['gas_state']} | Temp: {data['temperature_state']}", db.get_hud_status() if db else "Cloud disabled"]
                for i, line in enumerate(lines):
                    cv2.putText(shown, line, (20, 30+i*30), cv2.FONT_HERSHEY_SIMPLEX, .65, (200, 220, 255), 2)
                cv2.imshow("ClassiSense", shown)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            frame_number += 1
            if args.max_frames and frame_number >= args.max_frames:
                break
    except KeyboardInterrupt:
        pass
    finally:
        if controller and db:
            try:
                state = controller.get_sensor_data()
                state.update(source_state="disconnected", stopped=True)
                db.publish(state, now=float("inf"))
            except Exception as exc:
                print(f"[WARN] Could not queue final status: {type(exc).__name__}")
        # A failure closing one resource must never skip the remaining resources.
        cleanups = [controller.close if controller else None,
                    db.close if db else None,
                    cap.release if cap else None,
                    metrics_file.close if metrics_file else None,
                    cv2.destroyAllWindows if not args.headless else None]
        for cleanup in cleanups:
            if cleanup:
                try:
                    cleanup()
                except Exception as exc:
                    print(f"[WARN] Cleanup failed: {type(exc).__name__}")


if __name__ == "__main__":
    main()
