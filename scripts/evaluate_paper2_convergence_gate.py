#!/usr/bin/env python3
"""Verify the frozen Paper II development gate without reading external labels."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    integrity = []
    for name, artifact in config["frozen_artifacts"].items():
        path = ROOT / artifact["path"]
        actual = sha256(path)
        integrity.append({
            "name": name,
            "path": artifact["path"],
            "expected_sha256": artifact["sha256"],
            "actual_sha256": actual,
            "passed": actual == artifact["sha256"],
        })

    cv_path = ROOT / config["frozen_artifacts"]["bgs_nested_cv_summary"]["path"]
    overall_path = ROOT / config["frozen_artifacts"]["bgs_v028_predictions"]["path"]
    risk_path = ROOT / config["frozen_artifacts"]["risk_router_validation"]["path"]
    cv = json.loads(cv_path.read_text(encoding="utf-8"))
    overall = json.loads(overall_path.read_text(encoding="utf-8"))
    risk = json.loads(risk_path.read_text(encoding="utf-8"))["heldout"]
    thresholds = config["preregistered_development_gate"]

    observed = {
        "nested_boundary_f1_mean": float(cv["boundary_f1_mean"]),
        "nested_interval_f1_mean": float(cv["interval_f1_mean"]),
        "positive_interval_folds": sum(float(row["interval_f1"]) > 0 for row in cv["fold_metrics"]),
        "overall_boundary_cner": float(overall["overall"]["boundary"]["critical_numerical_error_rate"]),
        "independent_selective_precision": float(risk["routed"]["interval"]["precision"]),
        "independent_coverage": float(risk["coverage"]),
        "independent_cner": float(risk["routed"]["boundary"]["critical_numerical_error_rate"]),
    }
    checks = {
        "nested_boundary_f1_mean": observed["nested_boundary_f1_mean"] >= thresholds["minimum_nested_boundary_f1_mean"],
        "nested_interval_f1_mean": observed["nested_interval_f1_mean"] >= thresholds["minimum_nested_interval_f1_mean"],
        "positive_interval_folds": observed["positive_interval_folds"] >= thresholds["minimum_positive_interval_folds"],
        "overall_boundary_cner": observed["overall_boundary_cner"] <= thresholds["maximum_overall_boundary_cner"],
        "independent_selective_precision": observed["independent_selective_precision"] >= thresholds["minimum_independent_selective_precision"],
        "independent_coverage": observed["independent_coverage"] >= thresholds["minimum_independent_coverage"],
        "independent_cner": observed["independent_cner"] <= thresholds["maximum_independent_cner"],
    }
    passed = all(row["passed"] for row in integrity) and all(checks.values())
    report = {
        "experiment_id": "P2_CONVERGED_METHOD_DEVELOPMENT_GATE_001",
        "status": "PASSED" if passed else "FAILED",
        "config": str(args.config),
        "config_sha256": sha256(args.config),
        "artifact_integrity": integrity,
        "thresholds": thresholds,
        "observed": observed,
        "checks": checks,
        "external_authorization": "ONE_TIME_BGS_V003_ALLOWED" if passed else "NOT_ALLOWED",
        "external_data_read": False,
        "limitations": [
            "Swissgeol held-out evidence was previously inspected and is validation, not untouched confirmation.",
            "BGS v001 is development evidence and its source-disjoint folds are small.",
            "Passing this gate authorizes one fixed external evaluation; it does not establish external success.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "observed": observed, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
