#!/usr/bin/env python3
"""Export the Padova source-location catalog without claiming interval GT."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geologparser.export import write_geojson, write_geopackage, write_geoparquet, write_sqlite
from geologparser.spatial import attach_source_location


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation-root", type=Path, required=True)
    parser.add_argument("--locations", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.output_root.exists():
        raise FileExistsError(f"spatial export already exists: {arguments.output_root}")
    locations = {row["source_record_id"]: row for row in read_jsonl(arguments.locations)}
    # One source borehole row only: use the first page record as a header shell,
    # never duplicate a point for each page, and never merge auto intervals.
    page_annotations = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(arguments.annotation_root.glob("*.json"))]
    first_pages = {}
    for annotation in page_annotations:
        source_id = annotation["record"]["document"]["metadata"]["source_record_id"]
        page = int(annotation["panel"]["source_page"])
        if source_id not in first_pages or page < int(first_pages[source_id]["panel"]["source_page"]):
            first_pages[source_id] = annotation
    if set(first_pages) != set(locations):
        raise ValueError("annotation and location source-record sets differ")
    records = []
    for source_id in sorted(first_pages):
        source = first_pages[source_id]["record"]
        source["document"]["document_id"] = f"UNIPD_{source_id}"
        source["document"]["page_count"] = sum(
            item["record"]["document"]["metadata"]["source_record_id"] == source_id
            for item in page_annotations
        )
        source["intervals"] = []
        records.append(attach_source_location(source, locations[source_id]))
    arguments.output_root.mkdir(parents=True)
    outputs = {
        "sqlite": arguments.output_root / "unipd_source_catalog.sqlite",
        "geojson": arguments.output_root / "unipd_source_catalog.geojson",
        "geoparquet": arguments.output_root / "unipd_source_catalog.parquet",
        "geopackage": arguments.output_root / "unipd_source_catalog.gpkg",
    }
    write_sqlite(records, outputs["sqlite"])
    write_geojson(records, outputs["geojson"])
    write_geoparquet(records, outputs["geoparquet"])
    write_geopackage(records, outputs["geopackage"])
    summary = {
        "scope": "source-provided coordinate catalog; not interval GT and not a 3D model",
        "boreholes": len(records), "intervals": 0,
        "coordinate_validation_status": "source_provided_unverified",
        "source_location_manifest_sha256": sha256(arguments.locations),
        "outputs": {name: {"path": str(path), "sha256": sha256(path)} for name, path in outputs.items()},
        "paper3_real_model_metrics": None,
    }
    (arguments.output_root / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
