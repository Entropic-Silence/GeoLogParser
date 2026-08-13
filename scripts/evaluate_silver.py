#!/usr/bin/env python3
"""Evaluate predictions against an explicit machine-adjudicated Silver reference.

This track intentionally reports agreement-to-Silver, never human accuracy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import date
from pathlib import Path

from geologparser.evaluation import evaluate_benchmark
from geologparser.experiment import create_run_directory

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--split-version", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--prompt-version", default="not_applicable")
    parser.add_argument("--interval-tolerance-m", type=float, default=0.05)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                             capture_output=True, check=True).stdout.strip()
    reference_rows = read_jsonl(args.reference)
    reference_ids = {str(row.get("annotation_id") or row.get("item_id")) for row in reference_rows}
    prediction_rows = [row for row in read_jsonl(args.predictions) if str(row.get("item_id") or row.get("annotation_id")) in reference_ids]
    if {str(row.get("item_id") or row.get("annotation_id")) for row in prediction_rows} != reference_ids:
        raise ValueError("prediction rows do not cover exactly the Silver reference IDs")
    predictions_payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in prediction_rows).encode("utf-8")
    filtered_predictions_path = args.results_root / ".silver_prediction_inputs" / f"{args.experiment_id}.jsonl"
    filtered_predictions_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_predictions_path.write_bytes(predictions_payload)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id, "git_commit": commit,
        "date": date.today().isoformat(), "dataset_version": args.dataset_version,
        "split_version": args.split_version, "model": args.model,
        "model_revision": args.model_revision, "prompt_version": args.prompt_version,
        "seed": None, "hardware": {"device": "cpu_evaluation", "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "reference_path": str(args.reference.resolve()),
            "reference_sha256": sha256(args.reference),
            "ground_truth_path": str(args.reference.resolve()),
            "ground_truth_sha256": sha256(args.reference),
            "predictions_path": str(filtered_predictions_path.resolve()),
            "predictions_sha256": hashlib.sha256(predictions_payload).hexdigest(),
            "predictions_source_path": str(args.predictions.resolve()),
            "predictions_source_sha256": sha256(args.predictions),
            "interval_matching_tolerance_m": args.interval_tolerance_m,
            "boundary_accuracy_tolerances_m": [0.01, 0.05, 0.10],
            "reference_policy": "silver",
        },
    })
    try:
        metrics, errors = evaluate_benchmark(
            reference_rows, prediction_rows,
            interval_match_tolerance_m=args.interval_tolerance_m,
            reference_policy="silver",
        )
    except Exception:
        (run / "run.log").write_text("status=failed\n", encoding="utf-8")
        raise
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run / "predictions.jsonl").write_bytes(predictions_payload)
    (run / "errors.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in errors), encoding="utf-8")
    (run / "run.log").write_text(
        f"status=completed\ndocuments={metrics['document_count']}\nerrors={len(errors)}\nreference_policy=silver\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
