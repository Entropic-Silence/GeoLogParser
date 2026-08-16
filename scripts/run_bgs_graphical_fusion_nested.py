#!/usr/bin/env python3
"""Nested source-disjoint fusion of raster contact evidence and v025 candidates."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from geologparser.layout import DepthBoundaryCandidate, LogisticCandidateRanker
from geologparser.result_index import file_sha256
from scripts.run_bgs_layout_method_development import (
    boundary_metrics, candidate_label, interval_metrics, monotonic_sequence,
    tune_sequence_threshold,
)


ROOT = Path(__file__).resolve().parents[1]
FEATURES = (
    "base_logit", "contact_line_support", "contact_transition_support",
    "contact_confidence", "contact_y_proximity", "contact_depth_agreement",
    "contact_axis_inliers", "contact_axis_rmse_quality", "source_printed",
    "source_graphic", "source_metadata", "printed_line_support",
    "graphic_line_support", "view_agreement", "ocr_confidence",
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def references(row: dict) -> list[float]:
    return sorted({float(interval[key]) for interval in row["intervals"] for key in ("top_depth_m", "bottom_depth_m")})


def attach_contact_features(candidate_row: dict, pages: dict[int, dict]) -> DepthBoundaryCandidate:
    center_y = (float(candidate_row["bbox"][1]) + float(candidate_row["bbox"][3])) / 2.0
    page = pages.get(int(candidate_row["page"]), {})
    events = page.get("events", [])
    nearest = min(events, key=lambda event: abs(float(event["y_px"]) - center_y), default=None)
    features = dict(candidate_row.get("features", {}))
    probability = min(1 - 1e-6, max(1e-6, float(candidate_row["probability"])))
    features["base_logit"] = math.log(probability / (1.0 - probability))
    if nearest is None:
        features.update({
            "contact_line_support": 0.0, "contact_transition_support": 0.0,
            "contact_confidence": 0.0, "contact_y_proximity": 0.0,
            "contact_depth_agreement": 0.0, "contact_axis_inliers": 0.0,
            "contact_axis_rmse_quality": 0.0,
        })
    else:
        y_distance = abs(float(nearest["y_px"]) - center_y)
        depth_distance = abs(float(nearest["depth_m"]) - float(candidate_row["value_m"]))
        axis = page.get("axis") or {}
        features.update({
            "contact_line_support": float(nearest["line_support"]),
            "contact_transition_support": float(nearest["transition_support"]),
            "contact_confidence": float(nearest["confidence"]),
            "contact_y_proximity": math.exp(-y_distance / 12.0),
            "contact_depth_agreement": math.exp(-depth_distance / 0.12),
            "contact_axis_inliers": min(1.0, float(axis.get("inlier_count", 0)) / 8.0),
            "contact_axis_rmse_quality": max(0.0, 1.0 - min(1.0, float(axis.get("rmse_m", 1.0)) / 0.40)),
        })
    return DepthBoundaryCandidate(
        value_m=float(candidate_row["value_m"]), page=int(candidate_row["page"]),
        bbox=tuple(float(value) for value in candidate_row["bbox"]),
        candidate_source=str(candidate_row["candidate_source"]),
        features=features, provenance=tuple(candidate_row.get("provenance", [])),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "datasets/manifests/bgs_offshore_gold_v001.jsonl")
    parser.add_argument("--base-report", type=Path, default=ROOT / "experiments/paper2/analysis/bgs_layout_method_development_v025_role_multi.json")
    parser.add_argument("--grounding-report", type=Path, default=ROOT / "experiments/paper2/analysis/bgs_graphical_grounding_development_v001.json")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper2/analysis/bgs_graphical_fusion_nested_v001.json")
    args = parser.parse_args()
    source_rows = load_jsonl(args.manifest)
    reference_by_id = {row["record_id"]: references(row) for row in source_rows}
    base = json.loads(args.base_report.read_text(encoding="utf-8"))
    grounding = json.loads(args.grounding_report.read_text(encoding="utf-8"))
    grounding_by_id = {
        row["record_id"]: {int(page["page"]): page for page in row["pages"]}
        for row in grounding["predictions"]
    }
    base_by_id = {row["record_id"]: row for row in base["predictions"]}
    candidates_by_id = {
        record_id: [attach_contact_features(row, grounding_by_id.get(record_id, {})) for row in base_row["ranked_candidates"]]
        for record_id, base_row in base_by_id.items()
    }
    fold_by_id = {record_id: int(row["fold"]) for record_id, row in base_by_id.items()}
    predictions: dict[str, list[float]] = {}
    fold_reports = []
    for fold in sorted(set(fold_by_id.values())):
        train_ids = [record_id for record_id in candidates_by_id if fold_by_id[record_id] != fold]
        test_ids = [record_id for record_id in candidates_by_id if fold_by_id[record_id] == fold]
        train_candidates = [candidate for record_id in train_ids for candidate in candidates_by_id[record_id]]
        train_labels = [
            candidate_label(candidate, reference_by_id[record_id], 0.05)
            for record_id in train_ids for candidate in candidates_by_id[record_id]
        ]
        ranker = LogisticCandidateRanker(FEATURES).fit(train_candidates, train_labels)
        train_probabilities = {record_id: ranker.predict_proba(candidates_by_id[record_id]).tolist() for record_id in train_ids}
        threshold = tune_sequence_threshold(
            {record_id: candidates_by_id[record_id] for record_id in train_ids},
            train_probabilities, {record_id: reference_by_id[record_id] for record_id in train_ids},
        )
        for record_id in test_ids:
            probabilities = ranker.predict_proba(candidates_by_id[record_id]).tolist()
            sequence = monotonic_sequence(candidates_by_id[record_id], probabilities, threshold)
            predictions[record_id] = [candidate.value_m for candidate, _ in sequence]
        fold_metrics = {
            "boundary_at_0_05m": boundary_metrics(
                {record_id: predictions[record_id] for record_id in test_ids},
                {record_id: reference_by_id[record_id] for record_id in test_ids}, 0.05,
            ),
            "interval_at_0_05m": interval_metrics(
                {record_id: predictions[record_id] for record_id in test_ids},
                {record_id: reference_by_id[record_id] for record_id in test_ids}, 0.05,
            ),
        }
        fold_reports.append({
            "fold": fold, "train_document_count": len(train_ids),
            "test_document_count": len(test_ids), "threshold": threshold,
            "metrics": fold_metrics, "ranker": ranker.to_dict(),
        })
    overall = {
        "boundary_at_0_05m": boundary_metrics(predictions, reference_by_id, 0.05),
        "interval_at_0_05m": interval_metrics(predictions, reference_by_id, 0.05),
        "prediction_count": sum(map(len, predictions.values())),
    }
    report = {
        "experiment_id": "P2_BGS_GRAPHICAL_FUSION_NESTED_V001",
        "evaluation_role": "nested_source_disjoint_development",
        "manifest": str(args.manifest), "manifest_sha256": file_sha256(args.manifest),
        "base_report": str(args.base_report), "base_report_sha256": file_sha256(args.base_report),
        "grounding_report": str(args.grounding_report), "grounding_report_sha256": file_sha256(args.grounding_report),
        "feature_names": list(FEATURES), "overall": overall,
        "folds": fold_reports,
        "predictions": [{"record_id": record_id, "fold": fold_by_id[record_id], "predicted_boundaries_m": predictions[record_id]} for record_id in sorted(predictions)],
        "reference_blinding": "raster contact features are reference-blind; official boundaries enter only outer-fold training labels, threshold selection on training folds, and post-prediction scoring",
        "external_policy": "BGS v003 remains unopened; no external run is authorized from this development result",
    }
    if args.output.exists():
        raise FileExistsError(f"immutable output exists: {args.output}")
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(overall, indent=2))


if __name__ == "__main__":
    main()
