#!/usr/bin/env python3
"""Summarize nested source-disjoint routed-MoE fold evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import statistics
import hashlib


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fold", type=Path, action="append", required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--v024-report", type=Path)
    parser.add_argument("--role-report", type=Path)
    args = parser.parse_args()
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in args.fold]
    boundary = [row["source_disjoint_slice"]["boundary"]["f1"] for row in rows]
    interval = [row["source_disjoint_slice"]["interval"]["f1"] for row in rows]
    summary = {
        "experiment_id": "P2_BGS_ROUTED_MOE_V028_NESTED_CV_SUMMARY",
        "status": "completed_development_summary",
        "fold_artifacts": [str(path) for path in args.fold],
        "fold_count": len(rows),
        "boundary_f1_mean": statistics.mean(boundary),
        "boundary_f1_std_population": statistics.pstdev(boundary),
        "interval_f1_mean": statistics.mean(interval),
        "interval_f1_std_population": statistics.pstdev(interval),
        "fold_metrics": [
            {
                "evaluation_fold": row["evaluation_slice"]["fold"],
                "document_count": row["source_disjoint_slice"]["document_count"],
                "boundary_f1": row["source_disjoint_slice"]["boundary"]["f1"],
                "interval_f1": row["source_disjoint_slice"]["interval"]["f1"],
                "route_counts": row["route_counts_source_disjoint_slice"],
            }
            for row in rows
        ],
        "interpretation": "mean/std describe source-disjoint BGS v001 routing folds; no BGS v003 result was used and the underlying v024 candidate model remains a development artifact",
    }
    if args.manifest and args.v024_report and args.role_report:
        manifest = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        gold = {
            row["record_id"]: sorted({float(interval[key]) for interval in row["intervals"] for key in ("top_depth_m", "bottom_depth_m")})
            for row in manifest
        }
        v024 = json.loads(args.v024_report.read_text(encoding="utf-8"))
        role = json.loads(args.role_report.read_text(encoding="utf-8"))
        baseline = {row["record_id"]: [float(value) for value in row.get("predicted_boundaries_m", [])] for row in v024["predictions"]}
        role_values = {row["record_id"]: [float(item["value_m"]) for item in row.get("sequence_selected", [])] for row in role["predictions"]}
        from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics
        comparisons = {"v024_baseline": [], "semantic_role": []}
        for fold in range(len(rows)):
            ids = [row["record_id"] for row in manifest if int(hashlib.sha256(row["record_id"].encode()).hexdigest()[:8], 16) % len(rows) == fold]
            refs = {record_id: gold[record_id] for record_id in ids}
            for name, values in (("v024_baseline", baseline), ("semantic_role", role_values)):
                comparisons[name].append({
                    "fold": fold,
                    "boundary_f1": boundary_metrics({record_id: values.get(record_id, []) for record_id in ids}, refs, 0.05)["f1"],
                    "interval_f1": interval_metrics({record_id: values.get(record_id, []) for record_id in ids}, refs, 0.05)["f1"],
                })
        summary["comparison_fold_metrics"] = comparisons
        summary["comparison_fold_means"] = {
            name: {
                "boundary_f1_mean": statistics.mean([item["boundary_f1"] for item in values]),
                "interval_f1_mean": statistics.mean([item["interval_f1"] for item in values]),
            }
            for name, values in comparisons.items()
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
