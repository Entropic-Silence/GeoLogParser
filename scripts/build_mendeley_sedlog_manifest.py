#!/usr/bin/env python3
"""Build a traceable manifest for the acquired Mendeley SedLog PDF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

from geologparser.datasets.manifest import sha256_file


DATASET_ID = "mendeley_sedlog_drilling_cores_v001"
DOI = "10.17632/v6k9s36pbm.1"
EXPECTED_SHA256 = "007d26b081677478bd0534b26309c696871c6735237eac7669c53ac7e8e6dd02"
EXPECTED_SIZE = 10_549_922
EXPECTED_PAGE_IDS = [
    "CC23-S-01", "CC23-S-03", "CC23-S-04", "CC23-S-06", "CC23-S-09", "CC23-S-10",
    "CC23-S-11", "SC-23", "SP-11", "CC23-S-02", "CC23-S-05", "CC23-S-07",
    "CC23-S-08", "SC-04", "SC-18", "SC-22", "SC-24", "SC-26",
]


def build_manifest(dataset_root: Path) -> dict:
    source = dataset_root / "raw/SedLog_drilling_cores.pdf"
    if source.stat().st_size != EXPECTED_SIZE:
        raise ValueError("SedLog PDF size does not match public repository inventory")
    source_sha256 = sha256_file(source)
    if source_sha256 != EXPECTED_SHA256:
        raise ValueError("SedLog PDF SHA256 does not match public repository inventory")
    document = pymupdf.open(source)
    if len(document) != len(EXPECTED_PAGE_IDS):
        raise ValueError("unexpected SedLog PDF page count")
    rows = []
    for index, (page, expected_id) in enumerate(zip(document, EXPECTED_PAGE_IDS, strict=True), start=1):
        words = page.get_text("words")
        extracted_words = {str(word[4]) for word in words}
        if expected_id not in extracted_words:
            raise ValueError(f"page {index} does not expose expected source identifier {expected_id}")
        rows.append({
            "source_record_id": f"MENDELEY_SEDLOG_{index:03d}",
            "source_page_id": expected_id,
            "source_page": index,
            "source_dataset_doi": DOI,
            "source_pdf_sha256": source_sha256,
            "source_pdf_path": str(source),
            "page_width_pt": page.rect.width,
            "page_height_pt": page.rect.height,
            "document_type": "native_pdf",
            "native_text_chars": len(page.get_text("text")),
            "language": "English",
            "license": "CC-BY-4.0",
            "redistribution": "allowed_with_attribution_and_change_notice",
            "content_class": "digitised_sedlog_lithology_column",
            "paper_fit": ["paper1_international_transfer", "paper1_layout_stress_test"],
            "annotation_status": "unannotated",
            "benchmark_eligible": False,
            "eligibility_blockers": [
                "NO_HUMAN_GROUND_TRUTH",
                "NOT_CHINESE_CORE_BENCHMARK",
                "MVP_HEADER_AND_DESCRIPTION_FIELDS_ABSENT",
            ],
        })
    metadata_root = dataset_root / "metadata"
    metadata_root.mkdir(parents=True, exist_ok=True)
    manifest_path = metadata_root / "manifest.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    acquisition = {
        "dataset_id": DATASET_ID,
        "doi": DOI,
        "repository_url": "https://data.mendeley.com/datasets/v6k9s36pbm/1",
        "file_inventory_url": "https://data.mendeley.com/public-api/datasets/v6k9s36pbm/files?folder_id=root&version=1",
        "file_id": "fe3c0b6b-13ca-4ea5-8562-b9b160424c81",
        "access_date": "2026-08-13",
        "license": "CC-BY-4.0",
        "source_pdf_size_bytes": source.stat().st_size,
        "source_pdf_sha256": source_sha256,
        "documents": 1,
        "pages": len(rows),
        "native_pdf_pages": sum(row["document_type"] == "native_pdf" for row in rows),
        "human_ground_truth_pages": 0,
        "benchmark_eligible_pages": 0,
        "content_review": {
            "status": "single_visual_and_programmatic_review",
            "finding": "18 long-form SedLog lithology columns with English legend, depths, lithology patterns, and structure/fossil symbols; most GeoLogParser MVP header and text-description fields are absent.",
            "scope": "international transfer/layout stress testing only",
        },
    }
    acquisition_path = metadata_root / "acquisition.json"
    acquisition_path.write_text(json.dumps(acquisition, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = {
        **acquisition,
        "manifest_sha256": sha256_file(manifest_path),
        "acquisition_sha256": sha256_file(acquisition_path),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("/data/GeoLogParser/datasets/public/mendeley_sedlog_drilling_cores_v001"),
    )
    arguments = parser.parse_args()
    build_manifest(arguments.dataset_root)


if __name__ == "__main__":
    main()
