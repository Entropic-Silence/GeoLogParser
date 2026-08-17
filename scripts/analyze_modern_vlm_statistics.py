#!/usr/bin/env python3
"""Compute document-cluster uncertainty for completed modern-VLM runs."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from analyze_california_replication_statistics import bootstrap_delta, bootstrap_metric_intervals, counts, load_jsonl


ROOT = Path(__file__).resolve().parents[1]
RAPIDOCR_PATHS = {
    "California v001": ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_RAPIDOCR_TEST_FORMAL_001/predictions.jsonl",
    "California v002": ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_V002_RAPIDOCR_EXTERNAL_FORMAL_002/predictions.jsonl",
    "California v003": ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_V003_RAPIDOCR_PROSPECTIVE_FORMAL_001/predictions.jsonl",
    "California v004": ROOT / "results/2026-08-15/P1_CALIFORNIA_WCR_V004_RAPIDOCR_PROSPECTIVE_FORMAL_001/predictions.jsonl",
    "California v005": ROOT / "results/2026-08-15/P1_CALIFORNIA_WCR_V005_RAPIDOCR_EXTERNAL_FORMAL_001/predictions.jsonl",
}


def run_rows(entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    path = ROOT / str(entry["result_path"]) / "predictions.jsonl"
    return load_jsonl(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=ROOT / "configs/experiments/paper1_modern_vlm_result_plan_v001.json")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper1/analysis/modern_vlm_statistics_v001.json")
    parser.add_argument("--repetitions", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260817)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    rng = random.Random(args.seed)
    analyses: dict[str, Any] = {}
    for entry in plan["runs"]:
        if entry["status"] != "COMPLETED":
            continue
        rows = run_rows(entry)
        items = [counts(rows[record_id], "predicted_intervals", "matched_interval_count") for record_id in sorted(rows)]
        result: dict[str, Any] = {
            "experiment_id": entry["experiment_id"],
            "cohort": entry["cohort"],
            "model": entry["model"],
            "interface": entry["interface"],
            "document_cluster_metrics": bootstrap_metric_intervals(items, args.repetitions, rng),
        }
        rapid_path = RAPIDOCR_PATHS.get(entry["cohort"])
        if rapid_path is not None and rapid_path.is_file():
            rapid = load_jsonl(rapid_path)
            if set(rapid) != set(rows):
                raise ValueError(f"record IDs differ for {entry['experiment_id']} and RapidOCR {entry['cohort']}")
            qwen_items = [counts(rows[record_id], "predicted_intervals", "matched_interval_count") for record_id in sorted(rows)]
            rapid_items = [counts(rapid[record_id], "predicted_intervals", "matched_interval_count") for record_id in sorted(rapid)]
            result["paired_against_frozen_rapidocr"] = bootstrap_delta(qwen_items, rapid_items, args.repetitions, rng)
        analyses[entry["experiment_id"]] = result
    payload = {
        "analysis_version": "modern_vlm_statistics_v001",
        "method": "nonparametric percentile bootstrap clustered at document level; paired deltas retain document identity",
        "seed": args.seed,
        "bootstrap_repetitions": args.repetitions,
        "analyses": analyses,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
