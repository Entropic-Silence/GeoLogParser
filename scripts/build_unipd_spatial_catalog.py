#!/usr/bin/env python3
"""Build a traceable page-to-borehole spatial catalog for the Padova pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geologparser.spatial import group_page_annotations_by_source_record


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--locations", type=Path, required=True)
    parser.add_argument("--annotation-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    locations = {row["source_record_id"]: row for row in read_jsonl(arguments.locations)}
    annotations = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(arguments.annotation_root.glob("*.json"))]
    grouped = group_page_annotations_by_source_record(annotations)
    if set(locations) != set(grouped):
        raise ValueError("location and annotation source-record sets differ")
    rows = []
    for source_id in sorted(locations):
        location = locations[source_id]
        pages = grouped[source_id]
        rows.append({
            "source_record_id": source_id,
            "borehole_document_id": f"UNIPD_{source_id}",
            "annotation_ids": [page["annotation_id"] for page in pages],
            "source_pages": [page["panel"]["source_page"] for page in pages],
            "annotation_statuses": [page["annotation_status"] for page in pages],
            "human_verified_page_count": sum(page["annotation_status"] != "auto" for page in pages),
            "longitude": location["longitude"], "latitude": location["latitude"],
            "coordinate_system": location["coordinate_system"],
            "coordinate_source": location["coordinate_source"],
            "coordinate_validation_status": location["coordinate_validation_status"],
            "warning_codes": location["warning_codes"],
            "spatial_model_eligible": all(page["annotation_status"] != "auto" for page in pages),
        })
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "scope": "source-location to annotation linkage; not Ground Truth",
        "borehole_documents": len(rows),
        "page_annotations": sum(len(row["annotation_ids"]) for row in rows),
        "human_verified_pages": sum(row["human_verified_page_count"] for row in rows),
        "spatial_model_eligible_boreholes": sum(row["spatial_model_eligible"] for row in rows),
        "known_id_conflicts": sum(bool(row["warning_codes"]) for row in rows),
        "catalog_sha256": hashlib.sha256(arguments.output.read_bytes()).hexdigest(),
        "accuracy_metrics": None,
    }
    summary_path = arguments.output.with_name(arguments.output.stem + "_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
