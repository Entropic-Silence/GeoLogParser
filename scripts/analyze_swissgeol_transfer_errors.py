#!/usr/bin/env python3
"""Post-hoc numeric-evidence analysis for a Swissgeol transfer run."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_variants(value: float) -> set[str]:
    variants = {f"{value:g}", f"{value:.1f}", f"{value:.2f}"}
    return variants | {item.replace(".", ",") for item in variants}


def contains_numeric_token(text: str, value: float) -> bool:
    for variant in numeric_variants(value):
        if re.search(rf"(?<!\d){re.escape(variant)}(?!\d)", text):
            return True
    return False


def boundary_coverage(text: str, intervals: list[dict]) -> tuple[int, int, float | None]:
    values = sorted({float(item["bottom_depth_m"]) for item in intervals if item["bottom_depth_m"]})
    present = sum(contains_numeric_token(text, value) for value in values)
    return present, len(values), present / len(values) if values else None


def native_pdf_text(path: Path) -> str:
    completed = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else ""


def diagnostic_category(predicted_count: int, native_coverage: float, ocr_coverage: float) -> str:
    if predicted_count:
        return "candidate_section_detected"
    if native_coverage >= 0.5 and ocr_coverage >= 0.5:
        return "parser_section_failure_with_numeric_evidence"
    if native_coverage >= 0.5 and ocr_coverage < 0.5:
        return "ocr_numeric_evidence_loss"
    if native_coverage < 0.5 and ocr_coverage >= 0.5:
        return "parser_failure_on_ocr_recovered_evidence"
    if native_coverage > 0 or ocr_coverage > 0:
        return "limited_reference_numeric_evidence"
    return "no_reference_numeric_evidence_in_extracted_text"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()

    manifest_rows = {
        row["record_id"]: row
        for row in (
            json.loads(line) for line in arguments.manifest.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    predictions = [
        json.loads(line)
        for line in (arguments.run / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    native_cache: dict[str, str] = {}
    rows = []
    for prediction in predictions:
        record_id = prediction["record_id"]
        manifest = manifest_rows[record_id]
        content_group = prediction["content_group_id"]
        if content_group not in native_cache:
            native_cache[content_group] = native_pdf_text(Path(manifest["pdf_path"]))
        native_text = native_cache[content_group]
        ocr_text = (arguments.run / prediction["ocr_text_path"]).read_text(encoding="utf-8")
        native_present, total, native_coverage = boundary_coverage(
            native_text, prediction["reference_intervals"],
        )
        ocr_present, _, ocr_coverage = boundary_coverage(
            ocr_text, prediction["reference_intervals"],
        )
        native_value = native_coverage or 0.0
        ocr_value = ocr_coverage or 0.0
        rows.append({
            "record_id": record_id,
            "source_family": prediction["source_family"],
            "content_group_id": content_group,
            "reference_boundary_token_count": total,
            "native_boundary_tokens_present": native_present,
            "native_boundary_token_coverage": native_coverage,
            "ocr_boundary_tokens_present": ocr_present,
            "ocr_boundary_token_coverage": ocr_coverage,
            "predicted_interval_count": len(prediction["predicted_intervals"]),
            "matched_interval_count": prediction["matched_interval_count"],
            "diagnostic_category": diagnostic_category(
                len(prediction["predicted_intervals"]), native_value, ocr_value,
            ),
        })

    by_source = defaultdict(Counter)
    for row in rows:
        by_source[row["source_family"]][row["diagnostic_category"]] += 1
    summary = {
        "scope": "post-hoc reference-token visibility diagnostic; not a prediction metric",
        "experiment_id": json.loads((arguments.run / "run.json").read_text())["experiment_id"],
        "run_metrics_sha256": file_sha256(arguments.run / "metrics.json"),
        "dataset_manifest_sha256": file_sha256(arguments.manifest),
        "document_count": len(rows),
        "content_group_count": len({row["content_group_id"] for row in rows}),
        "category_counts": dict(Counter(row["diagnostic_category"] for row in rows)),
        "source_category_counts": {
            source: dict(counts) for source, counts in sorted(by_source.items())
        },
        "interpretation_limitations": [
            "Reference values are used only after prediction to diagnose failures.",
            "A matching number can occur outside the interval table and is not proof of correct localization.",
            "Low token coverage can reflect OCR loss, raster-only content, formatting differences, or page/database mismatch.",
        ],
        "rows": rows,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(arguments.output)
    print(json.dumps(summary["category_counts"], sort_keys=True))


if __name__ == "__main__":
    main()
