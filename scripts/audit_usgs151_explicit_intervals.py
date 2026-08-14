#!/usr/bin/env python3
"""Audit explicit USGS-151 interval text across two independent OCR layouts.

This produces a machine-consensus source transcription candidate, not Human
Ground Truth. A row is retained only when page, lithology, top and bottom agree
between the two configured OCR outputs.
"""
from __future__ import annotations

import argparse, json, re
from pathlib import Path

from geologparser.result_index import file_sha256

LINE_RE = re.compile(
    r"LITHOLOGY:\s*(?P<lith>[A-Za-z]+)\s+"
    r"(?P<top>\d+(?:\.\d+)?)\s*(?:ft\s*)?[-–—]\s*"
    r"(?P<bottom>\d+(?:\.\d+)?)\s*(?:ft|fi|8)?\b",
    re.IGNORECASE,
)

def parse_directory(root: Path, reader: str) -> list[dict]:
    rows = []
    for path in sorted(root.glob("page-*.txt")):
        page_match = re.search(r"(\d+)$", path.stem)
        if not page_match:
            continue
        page = int(page_match.group(1))
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in LINE_RE.finditer(text):
            top, bottom = float(match.group("top")), float(match.group("bottom"))
            if not (0 <= top < bottom <= 2000):
                continue
            rows.append({
                "page": page,
                "lithology_raw": match.group("lith").title(),
                "lithology_normalized": match.group("lith").lower(),
                "top_depth_ft": top,
                "bottom_depth_ft": bottom,
                "reader": reader,
                "source_text": re.sub(r"\s+", " ", match.group(0)).strip(),
                "source_ocr_path": str(path),
                "source_ocr_sha256": file_sha256(path),
            })
    return rows

def key(row: dict) -> tuple:
    return (row["page"], row["lithology_normalized"], row["top_depth_ft"], row["bottom_depth_ft"])

def audit(a_rows: list[dict], b_rows: list[dict]) -> tuple[list[dict], dict]:
    by_a = {key(row): row for row in a_rows}
    by_b = {key(row): row for row in b_rows}
    shared = sorted(set(by_a) & set(by_b))
    consensus = []
    for index, item in enumerate(shared, 1):
        a, b = by_a[item], by_b[item]
        consensus.append({
            "interval_id": f"USGS-151_MC_{index:03d}",
            "page": item[0], "lithology_raw": a["lithology_raw"],
            "lithology_normalized": item[1], "top_depth_ft": item[2],
            "bottom_depth_ft": item[3], "agreement_status": "exact_two_reader_agreement",
            "ground_truth_tier": "SOURCE_EXPLICIT_MACHINE_CONSENSUS",
            "human_reviewed": False,
            "reader_evidence": [a, b],
        })
    summary = {
        "scope": "USGS-151 explicit lithology interval machine-consensus audit",
        "ground_truth_tier": "SOURCE_EXPLICIT_MACHINE_CONSENSUS",
        "human_reviewed": False,
        "eligible_for_human_gold_claims": False,
        "reader_a_interval_count": len(a_rows),
        "reader_b_interval_count": len(b_rows),
        "exact_consensus_interval_count": len(consensus),
        "reader_a_only_count": len(set(by_a) - set(by_b)),
        "reader_b_only_count": len(set(by_b) - set(by_a)),
        "consensus_page_count": len({row["page"] for row in consensus}),
        "selection_rule": "exact agreement on page, normalized lithology, top depth, and bottom depth",
        "publication_use": "candidate transfer/audit reference only pending independent source verification",
    }
    return consensus, summary

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader-a", type=Path, required=True)
    ap.add_argument("--reader-b", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    args = ap.parse_args()
    a_rows = parse_directory(args.reader_a, "tesseract_psm11_250dpi")
    b_rows = parse_directory(args.reader_b, "tesseract_psm6_250dpi")
    consensus, summary = audit(a_rows, b_rows)
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "consensus_intervals.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in consensus),
        encoding="utf-8",
    )
    (args.output_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))

if __name__ == "__main__":
    main()
