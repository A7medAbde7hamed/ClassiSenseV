# Count / throughput benchmark · 2026-10-26

## Scope and method

A CPU-only smoke benchmark on the repository's `ai/people-tracking/video.mp4`: the first 120 sequential frames (4 seconds at source 30 FPS), model `yolo26n.pt`, ByteTrack, class 0, no hardware/cloud/GUI. Host: Linux x86_64, Python 3.12.14, CPU PyTorch 2.9.0, torchvision 0.24.0, Ultralytics 8.4.0, OpenCV 4.12.0.88, NumPy 2.2.6, lap 0.5.12. The environment is a shared executor, so CPU timing is indicative and not a device guarantee.

Five original frames (0, 30, 60, 90, 119) were inspected and counted manually: **24 visible people per frame**, including the standing teacher. The tiny left-edge partial body without a visible head is excluded. Seated and partially occluded people with visible heads are included. This is a small, single-reviewer reference sample, not a labelled evaluation dataset or student-only ground truth. No automatic model prediction was used as a reference label.

## Measured results

| Configuration | Counts on five reference frames | Mean absolute error | Within ±1 person | Median FPS after first 10 frames |
|---|---|---:|---:|---:|
| Initial 640px, confidence 0.35 | 12, 13, 13, 15, 15 | 10.4 people | 0% | 22.68 |
| Updated 960px, confidence 0.20 | 15, 22, 21, 23, 23 | 3.2 people | 40% | 14.50 |

The larger input reduces undercounting on this clip at a throughput cost. The first frame still undercounts substantially; tracker initialization and distant/occluded people are important failure cases. **Exact-count rate is 0% on this five-frame sample.** This is not evidence that the counting system is ready for attendance or exact capacity enforcement.

The updated default is 960px / 0.20, with command-line overrides. Parameters were explored on this same scene; the updated result is a calibration result, not a held-out accuracy score.

Raw per-frame predictions and exact evaluator outputs are committed under `docs/benchmarks/`. The evaluator's `median_fps` and `p95_inference_ms` use only the five matched annotated frames; the full-run FPS column above uses the 110 non-warmup frames. These are different populations and must not be interchanged.

## Reproduce

```bash
python ai/people-tracking/tracker.py --source ai/people-tracking/video.mp4 \
  --imgsz 640 --confidence 0.35 --no-hardware --no-cloud --headless \
  --max-frames 120 --metrics reports/baseline.csv
python ai/people-tracking/tracker.py --source ai/people-tracking/video.mp4 \
  --imgsz 960 --confidence 0.20 --no-hardware --no-cloud --headless \
  --max-frames 120 --metrics reports/updated.csv
python tools/evaluate_counts.py reports/updated.csv docs/ground-truth-sample.csv
```

Before a real classroom rollout, collect independently annotated held-out video across cameras, lighting, distances, crowding and empty rooms. Report count MAE and bias, frame-level exact/within-one rates and p50/p95 latency on the actual device. Distinguish total people from students. Consider a larger model, camera placement and room-specific fine tuning only after measuring these failures.
