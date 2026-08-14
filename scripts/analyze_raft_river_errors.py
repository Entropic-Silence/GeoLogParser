#!/usr/bin/env python3
"""Summarize reproducible real error events from the Raft River formal runs."""
from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
from pathlib import Path

from geologparser.result_index import file_sha256


def feet(interval: dict, field: str) -> float:
    return round(float(interval[field]) / 0.3048, 6)


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def numeric_substitutions(document: dict) -> list[dict]:
    references = document["reference_intervals"]
    predictions = document["predicted_intervals"]
    missing = [references[index] for index in document["unmatched_reference_indices"]]
    extras = [predictions[index] for index in document["unmatched_prediction_indices"]]
    events = []
    used = set()
    for reference in missing:
        candidates = []
        for index, prediction in enumerate(extras):
            if index in used:
                continue
            same_top = feet(reference, "top_depth_m") == feet(prediction, "top_depth_m")
            same_bottom = feet(reference, "bottom_depth_m") == feet(prediction, "bottom_depth_m")
            lithology_similarity = SequenceMatcher(
                None, reference["lithology_normalized"], prediction["lithology_normalized"]
            ).ratio()
            if (same_top or same_bottom) and lithology_similarity >= 0.65:
                candidates.append((lithology_similarity, same_top + same_bottom, index, prediction))
        if not candidates:
            continue
        _similarity, _shared, index, prediction = max(candidates)
        used.add(index)
        events.append({
            "record_id": document["record_id"],
            "reference_top_ft": feet(reference, "top_depth_m"),
            "reference_bottom_ft": feet(reference, "bottom_depth_m"),
            "prediction_top_ft": feet(prediction, "top_depth_m"),
            "prediction_bottom_ft": feet(prediction, "bottom_depth_m"),
            "reference_lithology": reference["lithology_normalized"],
            "prediction_lithology": prediction["lithology_normalized"],
            "source_text": prediction.get("evidence", {}).get("source_text"),
        })
    return events


def semantic_mismatches(document: dict) -> list[dict]:
    references = document["reference_intervals"]
    predictions = document["predicted_intervals"]
    prediction_by_boundary = {
        (feet(item, "top_depth_m"), feet(item, "bottom_depth_m")): item for item in predictions
    }
    output = []
    for reference in references:
        key = (feet(reference, "top_depth_m"), feet(reference, "bottom_depth_m"))
        prediction = prediction_by_boundary.get(key)
        if prediction and prediction["lithology_normalized"] != reference["lithology_normalized"]:
            output.append({
                "record_id": document["record_id"], "top_ft": key[0], "bottom_ft": key[1],
                "reference_lithology": reference["lithology_normalized"],
                "prediction_lithology": prediction["lithology_normalized"],
                "evidence": prediction.get("evidence"),
            })
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tesseract-run", type=Path, required=True)
    parser.add_argument("--rapidocr-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tess = rows(args.tesseract_run / "predictions.jsonl")
    rapid = rows(args.rapidocr_run / "predictions.jsonl")
    substitutions = [event for document in tess for event in numeric_substitutions(document)]
    rapid_semantic = [event for document in rapid for event in semantic_mismatches(document)]
    continuation_missing = sum(
        feet(document["reference_intervals"][index], "top_depth_m") >= 645
        for document in tess for index in document["unmatched_reference_indices"]
    )
    output = {
        "analysis_scope": "post-hoc Raft River real error-event analysis",
        "prediction_reference_conditioning": "post_hoc_analysis_only",
        "tesseract_prediction_sha256": file_sha256(args.tesseract_run / "predictions.jsonl"),
        "rapidocr_prediction_sha256": file_sha256(args.rapidocr_run / "predictions.jsonl"),
        "tesseract_error_count": sum(len(document["unmatched_reference_indices"]) + len(document["unmatched_prediction_indices"]) for document in tess),
        "tesseract_numeric_substitution_count": len(substitutions),
        "tesseract_numeric_substitutions": substitutions,
        "tesseract_continuation_page_missing_interval_count": continuation_missing,
        "rapidocr_boundary_complete": all(not document["unmatched_reference_indices"] and not document["unmatched_prediction_indices"] for document in rapid),
        "rapidocr_semantic_mismatch_count": len(rapid_semantic),
        "rapidocr_semantic_mismatches": rapid_semantic,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: output[key] for key in ("tesseract_error_count", "tesseract_numeric_substitution_count", "tesseract_continuation_page_missing_interval_count", "rapidocr_semantic_mismatch_count")}, sort_keys=True))


if __name__ == "__main__":
    main()
