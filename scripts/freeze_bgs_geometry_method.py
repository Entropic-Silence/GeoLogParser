#!/usr/bin/env python3
"""Freeze the all-development BGS v023 column/geometry model for one external run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.analyze_bgs_column_gate import Ranker, build_columns


def references(source: dict) -> list[float]:
    return sorted(
        {float(interval[key]) for interval in source["intervals"] for key in ("top_depth_m", "bottom_depth_m")}
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-analysis", type=Path, required=True)
    parser.add_argument("--geometry-analysis", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_analysis = json.loads(args.source_analysis.read_text())
    geometry_analysis = json.loads(args.geometry_analysis.read_text())
    sources = {row["record_id"]: row for row in map(json.loads, args.manifest.open())}
    predictions = {row["record_id"]: row for row in source_analysis["predictions"]}
    references_by_id = {record_id: references(row) for record_id, row in sources.items()}
    columns = {
        record_id: build_columns(prediction, references_by_id[record_id])
        for record_id, prediction in predictions.items()
    }
    ranker = Ranker().fit([column for rows in columns.values() for column in rows])
    selective = geometry_analysis["selective_operating_point"]
    frozen = {
        "model_id": "bgs_layout_column_geometry_v023",
        "status": "frozen_before_external_evaluation",
        "development_scope": "all BGS offshore Gold v001 source groups",
        "base_candidate_model": str(args.base_model),
        "base_candidate_model_sha256": hashlib.sha256(args.base_model.read_bytes()).hexdigest(),
        "source_analysis": str(args.source_analysis),
        "source_analysis_sha256": hashlib.sha256(args.source_analysis.read_bytes()).hexdigest(),
        "geometry_analysis": str(args.geometry_analysis),
        "geometry_analysis_sha256": hashlib.sha256(args.geometry_analysis.read_bytes()).hexdigest(),
        "development_manifest": str(args.manifest),
        "development_manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "column_gate": {
            "model": ranker.to_dict(),
            "top_k_columns_per_page": 6,
            "column_score_power": 0.0,
        },
        "sequence_decoder": {
            "full_sequence_threshold": 0.32,
            "selective_threshold": float(selective["threshold"]),
        },
        "geometry_refinement": geometry_analysis["final_model"]["parameters"],
        "development_metrics": {
            "metrics_by_tolerance_m": geometry_analysis["metrics_by_tolerance_m"],
            "selective_operating_point": selective,
            "provenance": geometry_analysis["provenance"],
        },
        "external_protocol": {
            "dataset": "bgs_offshore_gold_v002",
            "evaluation_count": 1,
            "post_evaluation_tuning_forbidden": True,
            "threshold_changes_forbidden": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
