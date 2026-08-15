#!/usr/bin/env python3
"""Freeze the official USGS Idaho image-only lithologic-log audit set."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from geologparser.result_index import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = Path("/data/GeoLogParser/datasets/public/usgs_idaho_lithologic_v001")
ITEM_BY_STEM = {
    "usgs144_lithologic_log": ("USGS 144", "64adbf89d34e70357a2931d8"),
    "usgs145_lithologic_log": ("USGS 145", "64d15b1dd34ef477cf3c0228"),
    "usgs150_lithologic_log": ("USGS 150", "67853160d34ec3ce63796974"),
    "USGS_152_Lithologic_Log_20230227": ("USGS 152", "63ea625cd34efa0476aecdd7"),
    "USGS_152A_Lithologic_Log_20230227": ("USGS 152A", "63ea625cd34efa0476aecdd7"),
    "USGS_152B_Lithologic_Log_20230227": ("USGS 152B", "63ea625cd34efa0476aecdd7"),
    "cfpp_b01_lithologic_log": ("CFPP-B01", "671819d5d34ee1f0a8822616"),
}


def page_count(path: Path) -> int:
    text = subprocess.run(["pdfinfo", str(path)], text=True, capture_output=True, check=True).stdout
    match = re.search(r"^Pages:\s+(\d+)", text, re.M)
    if not match:
        raise ValueError(f"page count unavailable: {path}")
    return int(match.group(1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET)
    ap.add_argument("--output", type=Path, default=ROOT / "datasets/manifests/usgs_idaho_lithologic_v001.jsonl")
    args = ap.parse_args()
    rows = []
    for pdf in sorted(args.dataset_root.rglob("*.pdf")):
        if pdf.stem not in ITEM_BY_STEM:
            raise ValueError(f"unmapped PDF: {pdf}")
        borehole, item_id = ITEM_BY_STEM[pdf.stem]
        rows.append({
            "record_id": f"USGS_IDAHO_{borehole.replace('-', '_').replace(' ', '_')}",
            "borehole_id": borehole,
            "sciencebase_item_id": item_id,
            "source_url": f"https://www.sciencebase.gov/catalog/item/{item_id}",
            "pdf_path": str(pdf),
            "pdf_sha256": file_sha256(pdf),
            "page_count": page_count(pdf),
            "document_type": "image_only_pdf",
            "language": "English",
            "ground_truth_tier": "OFFICIAL_SOURCE_SCAN_COVERAGE_AUDIT",
            "human_reviewed": False,
            "interval_ground_truth_available": False,
            "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
            "retrieval_date": "2026-08-15",
        })
    if len(rows) != 7 or sum(row["page_count"] for row in rows) != 608:
        raise ValueError("unexpected document/page inventory")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps({
        "documents": len(rows),
        "pages": sum(row["page_count"] for row in rows),
        "manifest": str(args.output),
        "manifest_sha256": file_sha256(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
