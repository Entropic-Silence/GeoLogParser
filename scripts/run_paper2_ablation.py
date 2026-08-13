#!/usr/bin/env python3
"""Run a human-GT-gated Paper II ablation matrix into immutable results."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import date
from pathlib import Path

from geologparser.evaluation import evaluate_paper2_ablation_matrix
from geologparser.experiment import create_run_directory


ROOT = Path(__file__).resolve().parents[1]


def read_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--matrix-config", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--split-version", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--prompt-version", required=True)
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument("--ground-truth-policy", choices=("human", "synthetic"), default="human")
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    arguments = parser.parse_args()
    config = json.loads(arguments.matrix_config.read_text(encoding="utf-8"))
    variants = {}
    case_files = {}
    for name, spec in config["variants"].items():
        path = Path(spec["cases_path"])
        variants[name] = {
            "disabled_modules": spec.get("disabled_modules", []),
            "cases": read_cases(path),
        }
        case_files[name] = {"path": str(path.resolve()), "sha256": sha256(path)}
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
            "matrix_config_path": str(arguments.matrix_config.resolve()),
            "matrix_config_sha256": sha256(arguments.matrix_config),
            "case_files": case_files, "calibration_bins": arguments.bins,
            "requirement": f"identical {arguments.ground_truth_policy} cases; zero or one disabled module per variant",
            "ground_truth_policy": arguments.ground_truth_policy,
        },
    })
    try:
        metrics = evaluate_paper2_ablation_matrix(variants, bins=arguments.bins, ground_truth_policy=arguments.ground_truth_policy)
    except Exception:
        (run / "run.log").write_text("status=failed\n", encoding="utf-8")
        raise
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    prediction_rows = [
        {"variant": name, "case": case}
        for name, variant in variants.items() for case in variant["cases"]
    ]
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in prediction_rows),
        encoding="utf-8",
    )
    (run / "errors.jsonl").write_text("", encoding="utf-8")
    (run / "run.log").write_text(
        f"status=completed\nvariants={metrics['variant_count']}\ncases={metrics['case_count']}\nground_truth_gate=passed\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
