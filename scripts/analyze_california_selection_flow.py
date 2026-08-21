#!/usr/bin/env python3
"""Recompute the California cohort selection-flow counts from source releases."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_california_wcr_gold import DEFAULT_LITHOLOGY, DEFAULT_WCR, load_intervals, load_wcr_metadata


ROOT = Path(__file__).resolve().parents[1]


def counts(records: dict[str, list[dict]]) -> tuple[int, int]:
    return len(records), sum(len(rows) for rows in records.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wcr", type=Path, default=DEFAULT_WCR)
    parser.add_argument("--lithology", type=Path, default=DEFAULT_LITHOLOGY)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper1/analysis/california_selection_flow_v001.json")
    args = parser.parse_args()
    metadata = load_wcr_metadata(args.wcr)
    intervals = load_intervals(args.lithology)
    joined = {record_id: rows for record_id, rows in intervals.items() if record_id in metadata}
    interval_count = {record_id: rows for record_id, rows in joined.items() if 5 <= len(rows) <= 60}
    empty_comments = {record_id: rows for record_id, rows in interval_count.items() if not any(item["comments"] for item in rows)}
    continuous = {}
    for record_id, rows in empty_comments.items():
        adjacent = list(zip(rows, rows[1:]))
        rate = sum(abs(left["bottom_depth_ft"] - right["top_depth_ft"]) <= 0.01 for left, right in adjacent) / len(adjacent) if adjacent else 1.0
        if rate >= 0.99:
            continuous[record_id] = rows
    manifests = [
        ROOT / "datasets/manifests/california_wcr_gold_v001.jsonl",
        ROOT / "datasets/manifests/california_wcr_gold_v002.jsonl",
        ROOT / "datasets/manifests/california_wcr_gold_v003.jsonl",
        ROOT / "datasets/manifests/california_wcr_gold_v004.jsonl",
        ROOT / "datasets/manifests/california_wcr_gold_v005.jsonl",
    ]
    acquired = [json.loads(line) for path in manifests for line in path.read_text(encoding="utf-8").splitlines() if line]
    split = json.loads((ROOT / "datasets/splits/california_wcr_gold_split_v001.json").read_text(encoding="utf-8"))
    development_ids = set(split["development"])
    formal = [row for row in acquired if row["record_id"] not in development_ids]
    stages = []
    for stage_id, label, records in (
        ("joined", "Public-link records joined to manual transcriptions", joined),
        ("interval_count", "Five to sixty valid deduplicated intervals", interval_count),
        ("empty_comments", "Empty source comments", empty_comments),
        ("continuity", "Adjacent continuity at least 0.99", continuous),
    ):
        document_count, interval_total = counts(records)
        stages.append({"stage_id": stage_id, "label": label, "document_count": document_count, "interval_count": interval_total})
    stages.extend([
        {"stage_id": "acquired", "label": "Deterministically acquired across v001–v005", "document_count": len(acquired), "interval_count": sum(len(row["intervals"]) for row in acquired)},
        {"stage_id": "formal", "label": "Formal evaluated cohorts; ten v001 development records excluded", "document_count": len(formal), "interval_count": sum(len(row["intervals"]) for row in formal)},
    ])
    for previous, current in zip(stages, stages[1:]):
        current["documents_removed_from_previous"] = previous["document_count"] - current["document_count"]
        current["intervals_removed_from_previous"] = previous["interval_count"] - current["interval_count"]
    payload = {
        "analysis_version": "california_selection_flow_v001",
        "evidence_tier": "PUBLISHED_MANUAL_TRANSCRIPTION_GOLD",
        "selection_unit": "document",
        "stages": stages,
        "sampling_note": "The eligible pool after continuity filtering exceeded fixed cohort budgets; deterministic county-first/seeded acquisition selected 460 records, of which 450 were formal evaluation records.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
