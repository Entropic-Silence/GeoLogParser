#!/usr/bin/env python3
"""Summarize real cross-engine detection disagreements in the USGS Idaho audit."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from geologparser.result_index import file_sha256

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, default=ROOT / "results/2026-08-15/P1_USGS_IDAHO_LITHOLOGIC_V001_CROSS_ENGINE_COVERAGE_001")
    ap.add_argument("--output", type=Path, default=ROOT / "experiments/paper1/analysis/usgs_idaho_cross_engine_errors_v001.json")
    args = ap.parse_args()
    rows = [json.loads(line) for line in (args.result / "page_audit.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rapid_only = [row for row in rows if row["rapidocr"]["lithology_label"] and not row["tesseract"]["lithology_label"]]
    tesseract_only = [row for row in rows if row["tesseract"]["lithology_label"] and not row["rapidocr"]["lithology_label"]]
    blank_rapid = [row for row in rows if not row["rapidocr"]["has_text"]]
    blank_tesseract = [row for row in rows if not row["tesseract"]["has_text"]]
    by_document = {}
    for document_id in sorted({row["document_id"] for row in rows}):
        items = [row for row in rows if row["document_id"] == document_id]
        by_document[document_id] = {
            "page_count": len(items),
            "rapidocr_only_lithology_pages": sum(row in rapid_only for row in items),
            "tesseract_only_lithology_pages": sum(row in tesseract_only for row in items),
            "both_lithology_pages": sum(row["rapidocr"]["lithology_label"] and row["tesseract"]["lithology_label"] for row in items),
            "rapidocr_depth_ranges": sum(row["rapidocr"]["depth_range_count"] for row in items),
            "tesseract_depth_ranges": sum(row["tesseract"]["depth_range_count"] for row in items),
        }
    output = {
        "scope": "USGS Idaho official-source scan cross-engine error-event analysis",
        "human_reviewed": False,
        "accuracy_claim_allowed": False,
        "page_count": len(rows),
        "document_count": len(by_document),
        "lithology_detection": {
            "rapidocr_only_pages": len(rapid_only),
            "tesseract_only_pages": len(tesseract_only),
            "both_pages": sum(row["rapidocr"]["lithology_label"] and row["tesseract"]["lithology_label"] for row in rows),
            "neither_pages": sum(not row["rapidocr"]["lithology_label"] and not row["tesseract"]["lithology_label"] for row in rows),
            "disagreement_document_counts": dict(sorted(Counter(row["document_id"] for row in rapid_only + tesseract_only).items())),
        },
        "full_text_detection": {
            "rapidocr_blank_pages": len(blank_rapid),
            "tesseract_blank_pages": len(blank_tesseract),
        },
        "depth_range_detection": {
            "rapidocr_total": sum(row["rapidocr"]["depth_range_count"] for row in rows),
            "tesseract_total": sum(row["tesseract"]["depth_range_count"] for row in rows),
            "rapidocr_minus_tesseract": sum(row["rapidocr"]["depth_range_count"] - row["tesseract"]["depth_range_count"] for row in rows),
        },
        "by_document": by_document,
        "source_page_audit_sha256": file_sha256(args.result / "page_audit.jsonl"),
        "interpretation_boundary": "Engine disagreement is a real detection event, not proof that either engine is correct; no interval precision/recall/F1 is computed.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
