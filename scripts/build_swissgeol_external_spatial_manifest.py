#!/usr/bin/env python3
"""Freeze every paired Swissgeol record outside the interval v003 split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_ROOT = Path("/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v003")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--output", type=Path,
        default=DEFAULT_ROOT / "spatial_external_manifest_v001.jsonl",
    )
    args = parser.parse_args()
    all_rows = [
        json.loads(line) for line in (args.dataset_root / "manifest.jsonl").read_text().splitlines()
        if line.strip()
    ]
    interval_ids = {
        json.loads(line)["record_id"]
        for line in (args.dataset_root / "gold_interval_manifest_v003.jsonl").read_text().splitlines()
        if line.strip()
    }
    selected = []
    for row in all_rows:
        if row["record_id"] in interval_ids:
            continue
        selected.append({
            **row,
            "spatial_evaluation_role": "external_all_records_outside_interval_v003",
            "selection_uses_document_content": False,
            "selection_uses_spatial_reference_values": False,
            "reference_scope": [
                "x_coordinate", "y_coordinate", "collar_elevation_m", "coordinate_system",
            ],
        })
    selected.sort(key=lambda row: row["record_id"])
    if not selected:
        raise ValueError("external spatial manifest would be empty")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in selected),
        encoding="utf-8",
    )
    print(f"{args.output}\nrecords={len(selected)}")


if __name__ == "__main__":
    main()
