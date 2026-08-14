#!/usr/bin/env python3
"""Audit source-visible interval tables against Swissgeol database intervals."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from geologparser.datasets.swissgeol import explicit_interval_sections
from geologparser.result_index import file_sha256


ROOT = Path("/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v001")


def main() -> None:
    manifest = [
        json.loads(line) for line in (ROOT / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    audit_rows, gold_rows = [], []
    for row in manifest:
        reference = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))
        final_depth = float(reference["borehole"]["final_depth_m"])
        expected = sorted(
            (float(item["top_depth_m"]), float(item["bottom_depth_m"]))
            for item in reference["stratigraphy"]["intervals"]
        )
        completed = subprocess.run(
            ["pdftotext", "-layout", row["pdf_path"], "-"],
            text=True, capture_output=True, check=True,
        )
        sections = explicit_interval_sections(completed.stdout, final_depth)
        exact = [section for section in sections if sorted(section) == expected]
        status = "EXACT_FULL_INTERVAL_AGREEMENT" if exact else (
            "PARTIAL_OR_MISMATCH" if sections else "NO_EXPLICIT_INTERVAL_TABLE_PARSED"
        )
        audit = {
            "record_id": row["record_id"],
            "borehole_id": row["borehole_id"],
            "status": status,
            "database_intervals": expected,
            "source_interval_candidates": sections,
            "pdf_sha256": file_sha256(Path(row["pdf_path"])),
            "reference_sha256": file_sha256(Path(row["reference_path"])),
            "audit_method": "native_pdf_layout_explicit_table_v001",
            "human_reviewed": False,
        }
        audit_rows.append(audit)
        if exact:
            gold_rows.append({
                **row,
                "ground_truth_tier": "GOLD",
                "gold_basis": "official_database_reference_with_exact_source_table_agreement",
                "gold_scope": ["interval_top_depth_m", "interval_bottom_depth_m", "interval_thickness_m"],
                "source_interval_evidence": exact[0],
                "human_reviewed": False,
            })
    (ROOT / "pairing_audit_v001.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in audit_rows),
        encoding="utf-8",
    )
    (ROOT / "gold_interval_manifest_v001.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in gold_rows),
        encoding="utf-8",
    )
    summary = {
        "audited_documents": len(audit_rows),
        "exact_full_interval_agreement_documents": len(gold_rows),
        "exact_full_interval_agreement_intervals": sum(item["interval_count"] for item in gold_rows),
        "partial_or_mismatch_documents": sum(item["status"] == "PARTIAL_OR_MISMATCH" for item in audit_rows),
        "no_explicit_interval_table_parsed_documents": sum(item["status"] == "NO_EXPLICIT_INTERVAL_TABLE_PARSED" for item in audit_rows),
        "human_reviewed": False,
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        "gold_scope": "interval boundaries only",
    }
    (ROOT / "pairing_audit_summary_v001.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
