#!/usr/bin/env python3
"""Sensitivity of the Paper II shallow-start prior on the public candidate pool."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.evaluation import boundary_matched_interval_metrics
from geologparser.paper2_sequence import select_sequence
from recompute_paper2_candidate_pool_public import as_intervals, full_edge


ROOT = Path(__file__).resolve().parents[1]


def candidate_pool(row: dict) -> list[dict]:
    return [
        dict(
            item,
            top=item["top_ft"],
            bottom=item["bottom_ft"],
            page=item["page_order"],
            y=item["y_norm"],
            x_top=item["x_top_norm"],
            x_bottom=item["x_bottom_norm"],
            node_score=item["raw_node_score"],
        )
        for item in row["candidate_pool"]
    ]


def score(rows: list[dict], coefficient: float) -> dict:
    references = [row["reference_intervals"] for row in rows]
    predictions = [
        as_intervals(
            select_sequence(
                candidate_pool(row),
                full_edge,
                depth_penalty_per_foot=coefficient,
            )
        )
        for row in rows
    ]
    metrics = boundary_matched_interval_metrics(references, predictions, tolerance_m=0.05)
    return {
        "coefficient_per_foot": coefficient,
        "predicted_intervals": sum(len(value) for value in predictions),
        "metrics": {key: value.to_dict() for key, value in metrics.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "experiments/paper2/public/candidate_pool_v001.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments/paper2/analysis/california_depth_start_sensitivity_v001.json",
    )
    arguments = parser.parse_args()
    rows = [
        json.loads(line)
        for line in arguments.input.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    coefficients = (0.0, 0.0005, 0.001, 0.0025, 0.005)
    by_freeze = {}
    for freeze in ("v004", "v005"):
        selected = [row for row in rows if row["cohort"] == freeze]
        by_freeze[freeze] = {
            "document_count": len(selected),
            "candidate_count": sum(len(row["candidate_pool"]) for row in selected),
            "conditions": [score(selected, coefficient) for coefficient in coefficients],
        }
    payload = {
        "analysis_version": "california_depth_start_sensitivity_v001",
        "evidence_tier": "PUBLISHED_MANUAL_TRANSCRIPTION_GOLD",
        "analysis_role": "post_hoc_explanatory_sensitivity",
        "input": arguments.input.relative_to(ROOT).as_posix(),
        "candidate_pool_control": "Every coefficient uses the same public candidates, references, matcher, and tolerance.",
        "default_coefficient_per_foot": 0.0005,
        "freezes": by_freeze,
        "limitations": [
            "The coefficient was not retuned; this analysis tests local sensitivity around the archived value.",
            "The analysis is post hoc and does not alter the confirmatory policy or any external evaluation.",
        ],
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(arguments.output)


if __name__ == "__main__":
    main()
