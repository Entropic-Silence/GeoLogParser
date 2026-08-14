#!/usr/bin/env python3
"""Freeze a non-overlapping California WCR external-validation extension."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from build_california_wcr_gold import (
    DEFAULT_LITHOLOGY,
    DEFAULT_WCR,
    build_candidate_order,
    download_box_pdf,
    file_sha256,
    load_intervals,
    load_wcr_metadata,
    parse_pdf_pages,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXCLUDE = ROOT / "datasets/manifests/california_wcr_gold_v001.jsonl"
DEFAULT_DATASET_ROOT = Path("/data/GeoLogParser/datasets/public/california_wcr_gold_v002")
DEFAULT_MANIFEST = ROOT / "datasets/manifests/california_wcr_gold_v002.jsonl"
DEFAULT_SPLIT = ROOT / "datasets/splits/california_wcr_gold_split_v002.json"


def read_ids(path: Path) -> set[str]:
    return {
        json.loads(line)["record_id"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wcr", type=Path, default=DEFAULT_WCR)
    parser.add_argument("--lithology", type=Path, default=DEFAULT_LITHOLOGY)
    parser.add_argument("--exclude-manifest", type=Path, default=DEFAULT_EXCLUDE)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--split", type=Path, default=DEFAULT_SPLIT)
    parser.add_argument("--target-documents", type=int, default=100)
    args = parser.parse_args()

    excluded = read_ids(args.exclude_manifest)
    metadata = load_wcr_metadata(args.wcr)
    intervals = load_intervals(args.lithology)
    order = [record_id for record_id in build_candidate_order(metadata, intervals) if record_id not in excluded]
    rows: list[dict] = []
    failures: list[dict] = []
    pdf_root = args.dataset_root / "pdfs"
    for record_id in order:
        if len(rows) >= args.target_documents:
            break
        source = metadata[record_id]
        target = pdf_root / f"{record_id}.pdf"
        try:
            box = download_box_pdf(source["OSWCR_URL"], target) if not target.is_file() else {}
            pages = parse_pdf_pages(target)
        except Exception as exc:  # pragma: no cover - network dependent
            failures.append({
                "record_id": record_id,
                "source_url": source["OSWCR_URL"],
                "error": str(exc),
            })
            continue
        if not box:
            box = {
                "box_file_id": source["OSWCR_URL"].rstrip("/").split("/")[-1],
                "box_file_version_id": None,
                "source_filename": None,
                "source_sha1": None,
            }
        source_intervals = intervals[record_id]
        rows.append({
            "record_id": record_id,
            "borehole_id": record_id,
            "county": source["County"],
            "mtrs": source["MTRS"],
            "legacy_log_number": source["LegacyLogNo"],
            "latitude": float(source["DD_LATITUDE"]) if source["DD_LATITUDE"] else None,
            "longitude": float(source["DD_LONGITUDE"]) if source["DD_LONGITUDE"] else None,
            "coordinate_datum": source["DATUM"].strip() or None,
            "coordinate_source": source["LOCATION_FROM"].strip() or None,
            "pdf_path": str(target),
            "pdf_sha256": file_sha256(target),
            "pdf_pages": pages,
            "source_url": source["OSWCR_URL"],
            "source_filename": box["source_filename"],
            "box_file_id": box["box_file_id"],
            "box_file_version_id": box["box_file_version_id"],
            "box_source_sha1": box["source_sha1"],
            "ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION",
            "source_human_transcribed": True,
            "source_quality_controlled": True,
            "project_human_reviewed": False,
            "reference_type": "USGS_verbatim_manual_WCR_interval_transcription",
            "reference_doi": "10.5066/P9M85U0T",
            "reference_version": "3.0_July_2025",
            "license": "CC0-1.0",
            "unit": "ft_bls",
            "hole_depth_ft": source["HoleDepth"] or None,
            "completed_depth_ft": source["CompletedDepth"] or None,
            "generalized_lithology": source["GeneralizedLithology"] or None,
            "publication_groups": sorted({item["publish_date_group"] for item in source_intervals}),
            "interval_count": len(source_intervals),
            "intervals": [
                {"interval_id": f"{record_id}_I{index:03d}", **item}
                for index, item in enumerate(source_intervals, start=1)
            ],
        })
        print(
            f"selected {record_id}: county={source['County']} "
            f"intervals={len(source_intervals)} pages={pages}"
        )

    if len(rows) != args.target_documents:
        raise RuntimeError(
            f"selected {len(rows)} documents, expected {args.target_documents}; "
            f"failures={len(failures)}"
        )
    if excluded & {row["record_id"] for row in rows}:
        raise RuntimeError("v002 overlaps v001")

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    split = {
        "split_version": "california_wcr_gold_split_v002_external",
        "dataset_manifest": str(args.manifest.relative_to(ROOT)),
        "dataset_manifest_sha256": file_sha256(args.manifest),
        "development": [],
        "test": sorted(row["record_id"] for row in rows),
        "development_documents": 0,
        "test_documents": len(rows),
        "excluded_manifest": str(args.exclude_manifest.relative_to(ROOT)),
        "excluded_manifest_sha256": file_sha256(args.exclude_manifest),
        "overlap_with_v001": 0,
        "policy": "Next deterministic clean candidates after excluding every v001 record; external validation only; no method development.",
    }
    args.split.parent.mkdir(parents=True, exist_ok=True)
    args.split.write_text(json.dumps(split, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    acquisition = {
        "dataset_version": "california_wcr_gold_v002",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "selection_version": "v001_order_successor_excluding_v001",
        "source_files": {
            str(args.wcr): {"sha256": file_sha256(args.wcr), "size_bytes": args.wcr.stat().st_size},
            str(args.lithology): {
                "sha256": file_sha256(args.lithology),
                "size_bytes": args.lithology.stat().st_size,
            },
        },
        "excluded_manifest": {
            "path": str(args.exclude_manifest),
            "sha256": file_sha256(args.exclude_manifest),
            "record_count": len(excluded),
        },
        "manifest": {"path": str(args.manifest), "sha256": file_sha256(args.manifest)},
        "split": {"path": str(args.split), "sha256": file_sha256(args.split)},
        "selected_documents": len(rows),
        "selected_intervals": sum(row["interval_count"] for row in rows),
        "selected_counties": len({row["county"] for row in rows}),
        "selected_pages": sum(row["pdf_pages"] for row in rows),
        "records_with_coordinates": sum(
            row["latitude"] is not None and row["longitude"] is not None for row in rows
        ),
        "failed_downloads_before_target": failures,
        "ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION",
        "project_human_reviewed": False,
    }
    metadata_root = args.dataset_root / "metadata"
    metadata_root.mkdir(parents=True, exist_ok=True)
    (metadata_root / "acquisition.json").write_text(
        json.dumps(acquisition, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(acquisition, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
