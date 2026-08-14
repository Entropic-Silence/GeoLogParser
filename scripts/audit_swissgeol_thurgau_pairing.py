#!/usr/bin/env python3
"""Audit source-visible interval tables against Swissgeol database intervals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from geologparser.datasets.swissgeol import explicit_interval_sections
from geologparser.result_index import file_sha256


DEFAULT_ROOT = Path("/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v001")


def optional_final_depth(reference: dict) -> float | None:
    """Return a numeric final depth when present; preserve missing as null."""
    value = (reference.get("borehole") or {}).get("final_depth_m")
    return float(value) if value is not None else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--audit-version", default="v001")
    parser.add_argument("--exclude-gold-manifest", type=Path)
    arguments = parser.parse_args()
    root = arguments.dataset_root
    version = arguments.audit_version
    if not version.startswith("v") or not version[1:].isdigit():
        raise ValueError("audit version must look like v001")
    destinations = [
        root / f"pairing_audit_{version}.jsonl",
        root / f"gold_interval_manifest_{version}.jsonl",
        root / f"pairing_audit_summary_{version}.json",
    ]
    if arguments.exclude_gold_manifest:
        destinations.append(root / f"gold_interval_manifest_incremental_{version}.jsonl")
    existing = [path for path in destinations if path.exists()]
    if existing:
        raise FileExistsError(
            "immutable audit output already exists: " + ", ".join(map(str, existing))
        )
    manifest = [
        json.loads(line) for line in (root / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    audit_rows, gold_rows = [], []
    for row in manifest:
        reference = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))
        final_depth = optional_final_depth(reference)
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
            "audit_method": "native_pdf_layout_explicit_table_v002_reference_independent",
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
    (root / f"pairing_audit_{version}.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in audit_rows),
        encoding="utf-8",
    )
    (root / f"gold_interval_manifest_{version}.jsonl").write_text(
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
        "audit_method": "native_pdf_layout_explicit_table_v002_reference_independent",
        "audit_version": version,
    }
    if arguments.exclude_gold_manifest:
        excluded_rows = [
            json.loads(line)
            for line in arguments.exclude_gold_manifest.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        excluded_ids = {row["record_id"] for row in excluded_rows}
        incremental = [row for row in gold_rows if row["record_id"] not in excluded_ids]
        incremental_path = root / f"gold_interval_manifest_incremental_{version}.jsonl"
        incremental_path.write_text(
            "".join(
                json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
                for item in incremental
            ),
            encoding="utf-8",
        )
        summary.update({
            "excluded_gold_manifest": str(arguments.exclude_gold_manifest),
            "excluded_gold_manifest_sha256": file_sha256(arguments.exclude_gold_manifest),
            "incremental_gold_documents": len(incremental),
            "incremental_gold_intervals": sum(item["interval_count"] for item in incremental),
            "incremental_gold_manifest": str(incremental_path),
            "incremental_gold_manifest_sha256": file_sha256(incremental_path),
        })
    (root / f"pairing_audit_summary_{version}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
