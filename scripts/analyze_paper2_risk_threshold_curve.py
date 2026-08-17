#!/usr/bin/env python3
"""Development-only threshold/coverage/risk curve for the frozen addition policy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.evaluation import match_intervals_by_boundaries


ROOT = Path(__file__).resolve().parents[1]
RUNS = {
    "v001_development": ROOT / "results/2026-08-14/P2_CALIFORNIA_WCR_CONSTRAINT_TEST_FORMAL_001/predictions.jsonl",
    "v002_development": ROOT / "results/2026-08-14/P2_CALIFORNIA_WCR_V002_CONSTRAINT_EXTERNAL_FORMAL_002/predictions.jsonl",
}


def key(row: dict) -> tuple[float, float]:
    return round(float(row["top_depth_m"]), 5), round(float(row["bottom_depth_m"]), 5)


def overlaps(left: dict, right: dict) -> bool:
    return max(float(left["top_depth_m"]), float(right["top_depth_m"])) < min(float(left["bottom_depth_m"]), float(right["bottom_depth_m"])) - 1e-9


def document_f1(matches: int, predictions: int, references: int) -> float:
    denominator = predictions + references
    return 2 * matches / denominator if denominator else 0.0


def evaluate(rows: list[dict], threshold: float) -> dict:
    accepted_actions = correct_actions = accepted_documents = changed_documents = worsened_documents = 0
    matched = predicted = reference_count = 0
    for row in rows:
        reference = row["reference_intervals"]
        raw = list(row["raw_predictions"])
        raw_keys = {key(item) for item in raw}
        changed_documents += {key(item) for item in row["constrained_predictions"]} != raw_keys
        proposed = [item for item in row["constrained_predictions"] if key(item) not in raw_keys and float(item.get("evidence", {}).get("node_score", float("-inf"))) >= threshold]
        proposed.sort(key=lambda item: float(item["evidence"]["node_score"]), reverse=True)
        selected = list(raw)
        accepted = []
        raw_monotonic = all(float(right["top_depth_m"]) >= float(left["top_depth_m"]) for left, right in zip(raw, raw[1:]))
        if raw_monotonic:
            for item in proposed:
                if any(overlaps(item, current) for current in selected):
                    continue
                selected.append(item)
                accepted.append(item)
            selected.sort(key=lambda item: (float(item["top_depth_m"]), float(item["bottom_depth_m"])))
        accepted_documents += bool(accepted)
        accepted_actions += len(accepted)
        for item in accepted:
            correct_actions += any(abs(float(item["top_depth_m"]) - float(target["top_depth_m"])) <= 0.05 and abs(float(item["bottom_depth_m"]) - float(target["bottom_depth_m"])) <= 0.05 for target in reference)
        raw_matches = len(match_intervals_by_boundaries(reference, raw, tolerance_m=0.05)[0])
        selected_matches = len(match_intervals_by_boundaries(reference, selected, tolerance_m=0.05)[0])
        worsened_documents += document_f1(selected_matches, len(selected), len(reference)) < document_f1(raw_matches, len(raw), len(reference)) - 1e-12
        matched += selected_matches
        predicted += len(selected)
        reference_count += len(reference)
    precision = matched / predicted if predicted else 0.0
    recall = matched / reference_count if reference_count else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    incorrect = accepted_actions - correct_actions
    return {
        "threshold": threshold,
        "accepted_documents": accepted_documents,
        "accepted_actions": accepted_actions,
        "correct_actions": correct_actions,
        "incorrect_actions": incorrect,
        "action_fcr": incorrect / accepted_actions if accepted_actions else None,
        "worsened_documents": worsened_documents,
        "coverage_all_documents": accepted_documents / len(rows),
        "coverage_changed_documents": accepted_documents / changed_documents if changed_documents else None,
        "interval_precision": precision,
        "interval_recall": recall,
        "interval_f1": f1,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper2/analysis/california_risk_threshold_curve_v001.json")
    args = parser.parse_args()
    rows = []
    scores = {2.999}
    for cohort, path in RUNS.items():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            row = json.loads(line)
            row["development_cohort"] = cohort
            rows.append(row)
            scores.update(float(item.get("evidence", {}).get("node_score", -1)) for item in row["constrained_predictions"])
    grid = sorted({round(score, 6) for score in scores if 1.0 <= score <= 3.0} | {1.0, 2.0, 2.5, 2.9, 2.95, 2.975, 2.99, 2.995, 2.999, 3.0})
    curve = [evaluate(rows, threshold) for threshold in grid]
    chosen = next(row for row in curve if abs(row["threshold"] - 2.999) < 1e-12)
    payload = {
        "analysis_version": "california_risk_threshold_curve_v001",
        "evidence_tier": "PUBLISHED_MANUAL_TRANSCRIPTION_GOLD_DEVELOPMENT_ONLY",
        "source_runs": {key: str(path.relative_to(ROOT)) for key, path in RUNS.items()},
        "document_count": len(rows),
        "threshold_selection_scope": "v001/v002 development outcomes only; v003/v004/v005 excluded",
        "chosen_threshold": 2.999,
        "chosen_operating_point": chosen,
        "curve": curve,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
