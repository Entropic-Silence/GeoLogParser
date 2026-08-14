#!/usr/bin/env python3
"""Generate traceable California WCR cross-engine and correction error analysis."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from geologparser.evaluation import match_intervals_by_boundaries


ROOT = Path(__file__).resolve().parents[1]
FT_TO_M = 0.3048


def load_jsonl(path: Path) -> dict[str, dict]:
    return {
        row["record_id"]: row
        for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    }


def feet(value_m: float) -> float:
    return round(value_m / FT_TO_M, 3)


def analyze_engine(rows: dict[str, dict]) -> dict:
    counts = Counter()
    nearest_events = []
    lithology_events = []
    per_document = []
    for record_id, row in sorted(rows.items()):
        references = row["reference_intervals"]
        predictions = row["predicted_intervals"]
        matches, missing, extra = match_intervals_by_boundaries(references, predictions, tolerance_m=0.05)
        counts["documents"] += 1
        counts["reference_intervals"] += len(references)
        counts["predicted_intervals"] += len(predictions)
        counts["matches"] += len(matches)
        counts["missing"] += len(missing)
        counts["spurious"] += len(extra)
        if not predictions:
            counts["documents_without_predictions"] += 1
        lith_errors = 0
        for match in matches:
            reference = references[match.reference_index]
            prediction = predictions[match.prediction_index]
            if reference["lithology_normalized"] != prediction["lithology_normalized"]:
                lith_errors += 1
                if len(lithology_events) < 40:
                    lithology_events.append({
                        "record_id": record_id,
                        "top_ft": feet(reference["top_depth_m"]),
                        "bottom_ft": feet(reference["bottom_depth_m"]),
                        "reference": reference["lithology_raw"],
                        "prediction": prediction["lithology_raw"],
                    })
        counts["matched_lithology_errors"] += lith_errors
        if missing and extra:
            available = set(extra)
            for reference_index in missing:
                reference = references[reference_index]
                if not available:
                    break
                nearest = min(
                    available,
                    key=lambda index: abs(predictions[index]["top_depth_m"] - reference["top_depth_m"])
                    + abs(predictions[index]["bottom_depth_m"] - reference["bottom_depth_m"]),
                )
                prediction = predictions[nearest]
                distance_ft = (
                    abs(prediction["top_depth_m"] - reference["top_depth_m"])
                    + abs(prediction["bottom_depth_m"] - reference["bottom_depth_m"])
                ) / FT_TO_M
                if distance_ft <= 150 and len(nearest_events) < 80:
                    nearest_events.append({
                        "record_id": record_id,
                        "reference": [feet(reference["top_depth_m"]), feet(reference["bottom_depth_m"])],
                        "prediction": [feet(prediction["top_depth_m"]), feet(prediction["bottom_depth_m"])],
                        "absolute_pair_error_ft": round(distance_ft, 3),
                        "reference_lithology": reference["lithology_raw"],
                        "prediction_lithology": prediction["lithology_raw"],
                    })
                    available.remove(nearest)
        per_document.append({
            "record_id": record_id,
            "county": row.get("county"),
            "reference_count": len(references),
            "prediction_count": len(predictions),
            "match_count": len(matches),
            "missing_count": len(missing),
            "spurious_count": len(extra),
            "matched_lithology_error_count": lith_errors,
        })
    return {
        "counts": dict(counts),
        "per_document": per_document,
        "nearest_boundary_error_examples": nearest_events,
        "lithology_error_examples": lithology_events,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapid-run", type=Path, default=ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_RAPIDOCR_TEST_FORMAL_001")
    parser.add_argument("--tesseract-run", type=Path, default=ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_TESSERACT_TEST_FORMAL_001")
    parser.add_argument("--constraint-run", type=Path, default=ROOT / "results/2026-08-14/P2_CALIFORNIA_WCR_CONSTRAINT_TEST_FORMAL_001")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper1/analysis/california_wcr_errors_v001.json")
    args = parser.parse_args()

    rapid = load_jsonl(args.rapid_run / "predictions.jsonl")
    tesseract = load_jsonl(args.tesseract_run / "predictions.jsonl")
    constrained = load_jsonl(args.constraint_run / "predictions.jsonl")
    ids = set(rapid)
    if set(tesseract) != ids or set(constrained) != ids:
        raise ValueError("California result documents do not align")

    rapid_analysis = analyze_engine(rapid)
    tesseract_analysis = analyze_engine(tesseract)
    engine_comparison = Counter()
    method_comparison = Counter()
    harmful_documents = []
    beneficial_documents = []
    for record_id in sorted(ids):
        rapid_matches = rapid[record_id]["matched_interval_count"]
        tess_matches = tesseract[record_id]["matched_interval_count"]
        if rapid_matches > tess_matches:
            engine_comparison["rapidocr_more_matches"] += 1
        elif tess_matches > rapid_matches:
            engine_comparison["tesseract_more_matches"] += 1
        else:
            engine_comparison["equal_matches"] += 1
        method = constrained[record_id]
        delta = method["constrained_match_count"] - method["raw_match_count"]
        if delta > 0:
            method_comparison["documents_improved"] += 1
            beneficial_documents.append({
                "record_id": record_id,
                "county": method["county"],
                "raw_match_count": method["raw_match_count"],
                "constrained_match_count": method["constrained_match_count"],
                "delta": delta,
                "correction_taxonomy": method["correction_taxonomy"],
            })
        elif delta < 0:
            method_comparison["documents_worsened"] += 1
            harmful_documents.append({
                "record_id": record_id,
                "county": method["county"],
                "raw_match_count": method["raw_match_count"],
                "constrained_match_count": method["constrained_match_count"],
                "delta": delta,
                "correction_taxonomy": method["correction_taxonomy"],
            })
        else:
            method_comparison["documents_unchanged"] += 1
    beneficial_documents.sort(key=lambda row: row["delta"], reverse=True)
    harmful_documents.sort(key=lambda row: row["delta"])

    payload = {
        "analysis_version": "california_wcr_errors_v001",
        "dataset_manifest": "datasets/manifests/california_wcr_gold_v001.jsonl",
        "split": "datasets/splits/california_wcr_gold_split_v001.json",
        "rapid_run": args.rapid_run.name,
        "tesseract_run": args.tesseract_run.name,
        "constraint_run": args.constraint_run.name,
        "rapidocr": rapid_analysis,
        "tesseract": tesseract_analysis,
        "engine_document_comparison": dict(engine_comparison),
        "constraint_document_comparison": dict(method_comparison),
        "largest_constraint_benefits": beneficial_documents[:15],
        "constraint_harm_cases": harmful_documents,
        "constraint_metrics": json.loads((args.constraint_run / "metrics.json").read_text(encoding="utf-8")),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
