#!/usr/bin/env python3
"""Summarize real error events from the frozen BGS offshore benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, dict]:
    return {
        row["record_id"]: row
        for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    }


def summarize(rows: dict[str, dict]) -> dict:
    output_docs = [row for row in rows.values() if row.get("predicted_intervals")]
    missing = sum(len(row.get("unmatched_reference_indices", [])) for row in rows.values())
    spurious = sum(len(row.get("unmatched_prediction_indices", [])) for row in rows.values())
    lithology_errors = sum(
        row.get("matched_interval_count", 0) - row.get("matched_lithology_exact_count", 0)
        for row in rows.values()
    )
    per_doc = []
    for row in rows.values():
        per_doc.append({
            "record_id": row["record_id"],
            "predicted_interval_count": len(row.get("predicted_intervals", [])),
            "matched_interval_count": row.get("matched_interval_count", 0),
            "missing_interval_count": len(row.get("unmatched_reference_indices", [])),
            "spurious_interval_count": len(row.get("unmatched_prediction_indices", [])),
            "lithology_error_count": row.get("matched_interval_count", 0) - row.get("matched_lithology_exact_count", 0),
            "error_events": sorted(set(
                (["zero_output_document"] if not row.get("predicted_intervals") else [])
                + (["boundary_omission"] if row.get("unmatched_reference_indices") else [])
                + (["spurious_interval"] if row.get("unmatched_prediction_indices") else [])
                + (["lithology_semantic_error"] if row.get("matched_interval_count", 0) > row.get("matched_lithology_exact_count", 0) else [])
            )),
        })
    return {
        "document_count": len(rows),
        "documents_with_output": len(output_docs),
        "zero_output_documents": len(rows) - len(output_docs),
        "predicted_interval_count": sum(len(row.get("predicted_intervals", [])) for row in rows.values()),
        "matched_interval_count": sum(row.get("matched_interval_count", 0) for row in rows.values()),
        "missing_interval_count": missing,
        "spurious_interval_count": spurious,
        "matched_lithology_error_count": lithology_errors,
        "documents_with_any_boundary_omission": sum(bool(row.get("unmatched_reference_indices")) for row in rows.values()),
        "documents_with_any_spurious_interval": sum(bool(row.get("unmatched_prediction_indices")) for row in rows.values()),
        "documents_with_lithology_error": sum(
            row.get("matched_interval_count", 0) > row.get("matched_lithology_exact_count", 0)
            for row in rows.values()
        ),
        "per_document": sorted(per_doc, key=lambda row: (row["matched_interval_count"], row["record_id"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "datasets/manifests/bgs_offshore_gold_v001.jsonl")
    parser.add_argument("--rapidocr", type=Path, default=ROOT / "results/2026-08-15/P1_BGS_OFFSHORE_V001_RAPIDOCR_CROSS_SOURCE_FORMAL_001/predictions.jsonl")
    parser.add_argument("--tesseract", type=Path, default=ROOT / "results/2026-08-15/P1_BGS_OFFSHORE_V001_TESSERACT_CROSS_SOURCE_FORMAL_001/predictions.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper1/analysis/bgs_offshore_errors_v001.json")
    args = parser.parse_args()
    manifest = load(args.manifest)
    rapidocr = load(args.rapidocr)
    tesseract = load(args.tesseract)
    if set(manifest) != set(rapidocr) or set(manifest) != set(tesseract):
        raise ValueError("manifest and predictions must contain identical records")
    rapid_docs = {key for key, row in rapidocr.items() if row.get("predicted_intervals")}
    tess_docs = {key for key, row in tesseract.items() if row.get("predicted_intervals")}
    output = {
        "analysis_scope": "post-hoc real error-event analysis on frozen BGS offshore authoritative interval benchmark",
        "manifest_sha256": __import__("hashlib").sha256(args.manifest.read_bytes()).hexdigest(),
        "rapidocr": summarize(rapidocr),
        "tesseract": summarize(tesseract),
        "engine_overlap": {
            "rapidocr_only_output_documents": len(rapid_docs - tess_docs),
            "tesseract_only_output_documents": len(tess_docs - rapid_docs),
            "both_output_documents": len(rapid_docs & tess_docs),
            "neither_output_documents": len(set(manifest) - rapid_docs - tess_docs),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("rapidocr", "tesseract", "engine_overlap")}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
