#!/usr/bin/env python3
"""Run a frozen human-GT benchmark evaluation into an immutable result folder."""

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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--split-version", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--prompt-version", default="not_applicable")
    parser.add_argument("--interval-tolerance-m", type=float, default=0.05)
    parser.add_argument(
        "--critical-threshold", action="append", default=[], metavar="FIELD=VALUE",
        help="Optional versioned critical-error threshold; repeat for numeric borehole fields.",
    )
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    arguments = parser.parse_args()
    critical_thresholds = {}
    for specification in arguments.critical_threshold:
        try:
            field, raw_value = specification.split("=", 1)
            value = float(raw_value)
        except ValueError as exc:
            raise ValueError(f"invalid critical threshold: {specification}") from exc
        if not field or value < 0:
            raise ValueError(f"invalid critical threshold: {specification}")
        critical_thresholds[field] = value
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id, "git_commit": commit,
        "date": date.today().isoformat(), "dataset_version": arguments.dataset_version,
        "split_version": arguments.split_version, "model": arguments.model,
        "model_revision": arguments.model_revision, "prompt_version": arguments.prompt_version,
        "seed": None, "hardware": {"device": "cpu_evaluation", "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "ground_truth_path": str(arguments.ground_truth.resolve()),
            "ground_truth_sha256": sha256(arguments.ground_truth),
            "predictions_path": str(arguments.predictions.resolve()),
            "predictions_sha256": sha256(arguments.predictions),
            "interval_matching_tolerance_m": arguments.interval_tolerance_m,
            "boundary_accuracy_tolerances_m": [0.01, 0.05, 0.10],
            "critical_error_thresholds": critical_thresholds or None,
        },
    })
    try:
        metrics, errors = evaluate_benchmark(
            read_jsonl(arguments.ground_truth), read_jsonl(arguments.predictions),
            interval_match_tolerance_m=arguments.interval_tolerance_m,
            critical_error_thresholds=critical_thresholds or None,
        )
    except Exception:
        # Preserve the immutable failed run and make the failure visible.
        (run / "run.log").write_text("status=failed\n", encoding="utf-8")
        raise
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    # Preserve evaluated prediction rows verbatim under the run lineage.
    (run / "predictions.jsonl").write_bytes(arguments.predictions.read_bytes())
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in errors),
        encoding="utf-8",
    )
    (run / "run.log").write_text(
        f"status=completed\ndocuments={metrics['document_count']}\nerrors={len(errors)}\nground_truth_gate=passed\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
