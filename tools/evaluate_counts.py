"""Join model metrics to manually annotated ground truth by exact frame index."""
import argparse
import csv
import json
from pathlib import Path
import statistics


def evaluate(predictions, truth):
    predicted = {int(r["frame"]): r for r in predictions}
    actual = {int(r["frame"]): int(r["people_count"]) for r in truth}
    common = sorted(predicted.keys() & actual.keys())
    if not common:
        raise ValueError("No matching annotated frames")
    errors = [int(predicted[i]["people_count"])-actual[i] for i in common]
    return {
        "annotated_frames": len(common),
        "missing_predictions": len(actual.keys()-predicted.keys()),
        "mae_people": statistics.mean(abs(e) for e in errors),
        "rmse_people": statistics.mean(e*e for e in errors)**0.5,
        "bias_people": statistics.mean(errors),
        "exact_count_rate": sum(e==0 for e in errors)/len(errors),
        "within_one_rate": sum(abs(e)<=1 for e in errors)/len(errors),
        "median_fps": statistics.median(float(predicted[i]["fps"]) for i in common),
        "p95_inference_ms": sorted(float(predicted[i]["inference_ms"]) for i in common)[max(0, int(len(common)*.95)-1)],
    }


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("predictions")
    parser.add_argument("ground_truth", help="CSV: frame,people_count; manually annotate original frames")
    parser.add_argument("--output")
    args=parser.parse_args()
    with open(args.predictions,newline="") as p, open(args.ground_truth,newline="") as t:
        result=evaluate(csv.DictReader(p),csv.DictReader(t))
    text=json.dumps(result,indent=2)
    print(text)
    if args.output:
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(text+"\n")
