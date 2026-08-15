#!/usr/bin/env python3
"""Source-disjoint development of the field-aware BGS depth parser.

Candidate generation is reference-blind.  Official intervals are loaded only
after candidates and features exist, to train/evaluate the probabilistic
ranker under deterministic source-disjoint folds.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import time

import cv2
from PIL import Image

from geologparser.layout import (
    DepthBoundaryCandidate, LogisticCandidateRanker, aggregate_numeric_evidence,
    fit_depth_scale, graphic_boundary_candidates, infer_log_panel_layout,
    metadata_final_depth_candidates, printed_boundary_candidates,
)
from geologparser.ocr import TextRegion
from geologparser.result_index import file_sha256


ROOT = Path(__file__).resolve().parents[1]
FEATURES = (
    "source_printed", "source_graphic", "source_metadata", "ocr_confidence",
    "view_support", "view_agreement", "full_page_support", "line_left_run",
    "line_right_run", "line_left_dark", "line_right_dark", "texture_change",
    "scale_inliers", "scale_rmse", "normalized_y", "description_x_distance",
    "depth_x_distance", "near_same_y_pair", "metadata_label_score",
    "snap_step", "snap_delta", "snap_integer", "snap_half", "snap_tenth",
    "printed_line_support", "printed_pair_support", "graphic_line_support",
    "graphic_change_support", "metadata_cross_field",
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def reference_boundaries(source: dict) -> list[float]:
    return sorted(
        {float(row["top_depth_m"]) for row in source["intervals"]}
        | {float(row["bottom_depth_m"]) for row in source["intervals"]}
    )


def fold_id(record_id: str, folds: int) -> int:
    return int(hashlib.sha256(record_id.encode()).hexdigest()[:8], 16) % folds


def candidate_label(candidate: DepthBoundaryCandidate, references: list[float], tolerance: float) -> int:
    return int(any(abs(candidate.value_m - value) <= tolerance for value in references))


def deduplicate(candidates: list[DepthBoundaryCandidate], probabilities: list[float]) -> list[tuple[DepthBoundaryCandidate, float]]:
    selected: dict[tuple[int, int], tuple[DepthBoundaryCandidate, float]] = {}
    for candidate, probability in zip(candidates, probabilities):
        key = (candidate.page, round(candidate.value_m * 20))
        if key not in selected or probability > selected[key][1]:
            selected[key] = (candidate, probability)
    return list(selected.values())


def monotonic_sequence(
    candidates: list[DepthBoundaryCandidate], probabilities: list[float], threshold: float,
) -> list[tuple[DepthBoundaryCandidate, float]]:
    """Maximum-evidence monotone depth sequence with traceable abstention."""
    terminal_cap = infer_terminal_cap(candidates)
    rows = [
        row for row in deduplicate(candidates, probabilities)
        if row[1] >= threshold and (terminal_cap is None or row[0].value_m <= terminal_cap + 0.05)
    ]
    if not rows:
        return []
    # Geological order is increasing depth. Metadata terminal-depth evidence is
    # permitted only as the last node even though it occurs in the page header.
    rows.sort(key=lambda row: (row[0].value_m, row[0].page, row[0].bbox[1]))
    scores = []
    previous = []
    for index, (candidate, probability) in enumerate(rows):
        node = math.log(max(1e-6, probability) / max(1e-6, 1 - probability))
        scores.append(node)
        previous.append(-1)
        for left in range(index):
            prior, _ = rows[left]
            if candidate.value_m <= prior.value_m + 0.025:
                continue
            gap = candidate.value_m - prior.value_m
            edge = 0.12 - 0.015 * max(0.0, gap - 50.0)
            proposed = scores[left] + node + edge
            if proposed > scores[index]:
                scores[index] = proposed
                previous[index] = left
    end = max(range(len(rows)), key=lambda index: scores[index])
    sequence = []
    while end >= 0:
        sequence.append(rows[end])
        end = previous[end]
    sequence.reverse()
    return sequence


def raw_selection(candidates: list[DepthBoundaryCandidate], scores: list[float], threshold: float) -> list[tuple[DepthBoundaryCandidate, float]]:
    terminal_cap = infer_terminal_cap(candidates)
    return sorted(
        [
            row for row in deduplicate(candidates, scores)
            if row[1] >= threshold and (terminal_cap is None or row[0].value_m <= terminal_cap + 0.05)
        ],
        key=lambda row: row[0].value_m,
    )


def add_cross_field_support(candidates: list[DepthBoundaryCandidate]) -> None:
    body_values = [
        candidate.value_m for candidate in candidates
        if candidate.candidate_source != "metadata_final_depth"
    ]
    for candidate in candidates:
        if candidate.candidate_source == "metadata_final_depth":
            candidate.features["metadata_cross_field"] = float(
                any(abs(candidate.value_m - value) <= 0.05 for value in body_values)
            )


def infer_terminal_cap(candidates: list[DepthBoundaryCandidate]) -> float | None:
    supported = [
        candidate for candidate in candidates
        if candidate.candidate_source == "metadata_final_depth"
        and candidate.features.get("metadata_label_score", 0.0) >= 0.30
        and candidate.features.get("metadata_cross_field", 0.0) >= 1.0
    ]
    if not supported:
        return None
    return max(
        supported,
        key=lambda candidate: (
            candidate.features.get("metadata_label_score", 0.0),
            candidate.features.get("view_agreement", 0.0),
            -candidate.value_m,
        ),
    ).value_m


def boundary_metrics(predictions: dict[str, list[float]], references: dict[str, list[float]], tolerance: float) -> dict:
    true_positive = false_positive = false_negative = 0
    errors = []
    for record_id, expected in references.items():
        remaining = set(range(len(expected)))
        for prediction in predictions.get(record_id, []):
            possible = sorted(
                ((abs(prediction - expected[index]), index) for index in remaining),
                key=lambda row: row[0],
            )
            if possible and possible[0][0] <= tolerance:
                true_positive += 1
                remaining.remove(possible[0][1])
                errors.append(possible[0][0])
            else:
                false_positive += 1
        false_negative += len(remaining)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": precision, "recall": recall, "f1": f1,
        "true_positive": true_positive, "false_positive": false_positive,
        "false_negative": false_negative,
        "critical_numerical_error_rate": false_positive / (true_positive + false_positive) if true_positive + false_positive else None,
        "matched_boundary_mae_m": sum(errors) / len(errors) if errors else None,
    }


def interval_metrics(predictions: dict[str, list[float]], references: dict[str, list[float]], tolerance: float) -> dict:
    predicted_intervals = {
        key: list(zip(sorted(values), sorted(values)[1:])) for key, values in predictions.items()
    }
    reference_intervals = {
        key: list(zip(values, values[1:])) for key, values in references.items()
    }
    tp = fp = fn = 0
    for record_id, expected in reference_intervals.items():
        remaining = set(range(len(expected)))
        for top, bottom in predicted_intervals.get(record_id, []):
            possible = [
                index for index in remaining
                if abs(top - expected[index][0]) <= tolerance and abs(bottom - expected[index][1]) <= tolerance
            ]
            if possible:
                tp += 1
                remaining.remove(possible[0])
            else:
                fp += 1
        fn += len(remaining)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "true_positive": tp, "false_positive": fp, "false_negative": fn}


def heuristic_probability(candidate: DepthBoundaryCandidate) -> float:
    feature = candidate.features
    if feature.get("source_metadata"):
        score = 0.42 + 0.28 * feature.get("metadata_label_score", 0) + 0.20 * feature.get("ocr_confidence", 0)
    elif feature.get("source_graphic"):
        score = (
            0.18 + 0.34 * feature.get("line_right_run", 0)
            + 1.8 * feature.get("texture_change", 0)
            + 0.12 * feature.get("scale_inliers", 0)
            - 0.12 * feature.get("scale_rmse", 1)
        )
    else:
        score = (
            0.18 * feature.get("ocr_confidence", 0)
            + 0.18 * feature.get("view_support", 0)
            + 0.18 * feature.get("view_agreement", 0)
            + 0.18 * max(feature.get("line_left_run", 0), feature.get("line_right_run", 0))
            + 0.08 * feature.get("full_page_support", 0)
            + 0.10 * feature.get("near_same_y_pair", 0)
            + 0.10 * (1 - min(feature.get("description_x_distance", 1), feature.get("depth_x_distance", 1)))
        )
    return min(0.999, max(0.001, score))


def risk_policy_probability(candidate: DepthBoundaryCandidate) -> float:
    """Conservative, reference-blind acceptance score for production review."""
    feature = candidate.features
    if candidate.candidate_source == "metadata_final_depth":
        return min(0.999, 0.50 + 0.45 * feature.get("metadata_label_score", 0.0)) if feature.get("metadata_cross_field", 0.0) else 0.001
    if candidate.candidate_source == "printed_depth":
        line = feature.get("printed_line_support", 0.0)
        repeated = feature.get("view_agreement", 0.0) >= 0.75 and feature.get("view_support", 0.0) >= 0.6
        if line >= 0.22 and repeated:
            return min(0.995, 0.82 + 0.12 * line + 0.05 * feature.get("view_agreement", 0.0))
        if feature.get("printed_pair_support", 0.0) and repeated:
            return 0.90
        return 0.001
    line = feature.get("graphic_line_support", 0.0)
    scale_ok = feature.get("scale_rmse", 1.0) <= 0.16 and feature.get("scale_inliers", 0.0) >= 0.5
    if scale_ok and line >= 0.80 and (feature.get("graphic_change_support", 0.0) >= 0.02 or abs(candidate.value_m) <= 0.05):
        return min(0.995, 0.80 + 0.15 * line + 0.05 * (1 - feature.get("scale_rmse", 1.0)))
    return 0.001


def tune_threshold(
    probabilities: list[float], labels: list[int], *, minimum_precision: float | None = None,
) -> float:
    best = None
    for threshold in [index / 100 for index in range(20, 96, 2)]:
        selected = [index for index, value in enumerate(probabilities) if value >= threshold]
        if not selected:
            continue
        tp = sum(labels[index] for index in selected)
        fp = len(selected) - tp
        fn = sum(labels) - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        if minimum_precision is not None and precision < minimum_precision:
            continue
        key = (f1 if minimum_precision is None else recall, precision, -threshold)
        if best is None or key > best[0]:
            best = (key, threshold)
    return best[1] if best else 0.99


def tune_sequence_threshold(
    candidates_by_document: dict[str, list[DepthBoundaryCandidate]],
    probabilities_by_document: dict[str, list[float]], references: dict[str, list[float]],
) -> float:
    best = None
    for threshold in [index / 100 for index in range(30, 96, 2)]:
        predictions = {
            record_id: [row[0].value_m for row in monotonic_sequence(
                candidates_by_document[record_id], probabilities_by_document[record_id], threshold,
            )]
            for record_id in candidates_by_document
        }
        interval = interval_metrics(predictions, references, 0.05)
        boundary = boundary_metrics(predictions, references, 0.05)
        key = (interval["f1"], boundary["f1"], boundary["precision"], -threshold)
        if best is None or key > best[0]:
            best = (key, threshold)
    return best[1] if best else 0.99


def generate_document_candidates(source: dict, multiscale: dict, source_run: Path, field_roi: dict | None = None) -> dict:
    page_outputs = []
    for page_row in multiscale["page_layout"]:
        page = int(page_row["page"])
        image_path = source_run / f"{source['record_id']}_page-{page}.png"
        region_path = source_run / f"{source['record_id']}_page-{page}_regions.jsonl"
        text_rows = load_jsonl(region_path)
        with Image.open(image_path) as opened:
            width, height = opened.size
        gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        regions = [
            TextRegion(page, tuple(row["bbox"]), row["text"], float(row.get("confidence") or 0), "frozen_full_page")
            for row in text_rows
        ]
        layout = infer_log_panel_layout(regions, width, height)
        if layout is None:
            page_outputs.append({"page": page, "layout_detected": False, "baseline": [], "multiscale": [], "all": [], "scale": None})
            continue
        roi_page = None
        if field_roi is not None:
            roi_doc = next((row for row in field_roi.get("documents", []) if row["record_id"] == source["record_id"]), None)
            if roi_doc is not None:
                roi_page = next((row for row in roi_doc["pages"] if int(row["page"]) == page), None)
        roi_rows = list(roi_page.get("rows", [])) if roi_page else []
        boundary_hint = next((float(row["center_x_normalized"]) for row in (roi_page or {}).get("targets", []) if row["field_role"] == "boundary_depth"), None)
        scale_hint = next((float(row["center_x_normalized"]) for row in (roi_page or {}).get("targets", []) if row["field_role"] == "scale_depth"), None)
        base_rows = list(page_row["baseline"])
        combined_rows = list(page_row["baseline"]) + list(page_row["reread"])
        boundary_rows = [row for row in roi_rows if row.get("field_role") == "boundary_depth"]
        scale_rows = [row for row in roi_rows if row.get("field_role") == "scale_depth"]
        baseline_evidence = aggregate_numeric_evidence(base_rows, page=page)
        combined_evidence = aggregate_numeric_evidence(combined_rows + boundary_rows, page=page)
        scale_evidence = aggregate_numeric_evidence(combined_rows + scale_rows, page=page)
        baseline_printed = list(printed_boundary_candidates(baseline_evidence, gray, layout=layout, boundary_x_hint=boundary_hint))
        multiscale_printed = list(printed_boundary_candidates(combined_evidence, gray, layout=layout, boundary_x_hint=boundary_hint))
        baseline_meta = metadata_final_depth_candidates(
            baseline_evidence, text_rows, layout=layout, width=width, height=height,
        )
        multiscale_meta = metadata_final_depth_candidates(
            combined_evidence, text_rows, layout=layout, width=width, height=height,
        )
        calibration = fit_depth_scale(scale_evidence, layout, width=width, height=height, x_center_hint=scale_hint)
        graphic = graphic_boundary_candidates(
            gray, page=page, layout=layout, calibration=calibration, depth_x_hint=scale_hint,
        ) if calibration else []
        page_outputs.append({
            "page": page,
            "layout_detected": True,
            "baseline": baseline_printed + baseline_meta,
            "multiscale": multiscale_printed + multiscale_meta,
            "all": multiscale_printed + multiscale_meta + graphic,
            "scale": {
                "depth_per_pixel": calibration.depth_per_pixel,
                "intercept_m": calibration.intercept_m,
                "inlier_count": calibration.inlier_count,
                "rmse_m": calibration.rmse_m,
            } if calibration else None,
        })
    output = {
        "record_id": source["record_id"],
        "pages": page_outputs,
        "baseline": [item for page in page_outputs for item in page["baseline"]],
        "multiscale": [item for page in page_outputs for item in page["multiscale"]],
        "all": [item for page in page_outputs for item in page["all"]],
    }
    add_cross_field_support(output["baseline"])
    add_cross_field_support(output["multiscale"])
    add_cross_field_support(output["all"])
    output["terminal_cap_m"] = infer_terminal_cap(output["all"])
    return output


def serialize_candidate(candidate: DepthBoundaryCandidate, probability: float | None = None) -> dict:
    return {
        "value_m": candidate.value_m, "page": candidate.page,
        "bbox": list(candidate.bbox), "candidate_source": candidate.candidate_source,
        "features": dict(candidate.features), "provenance": list(candidate.provenance),
        "probability": probability,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--multiscale-analysis", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--field-roi-analysis", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-output", type=Path, required=True)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--label-tolerance-m", type=float, default=0.10)
    args = parser.parse_args()
    started = time.perf_counter()
    sources = load_jsonl(args.manifest)
    multiscale_rows = {
        row["record_id"]: row
        for row in json.loads(args.multiscale_analysis.read_text(encoding="utf-8"))["documents"]
    }
    field_roi = json.loads(args.field_roi_analysis.read_text(encoding="utf-8")) if args.field_roi_analysis else None
    references = {row["record_id"]: reference_boundaries(row) for row in sources}
    generated = {
        row["record_id"]: generate_document_candidates(row, multiscale_rows[row["record_id"]], args.source_run, field_roi=field_roi)
        for row in sources
    }

    # Incremental reference-blind generation ablations use one frozen heuristic.
    ablations = {}
    for name, candidate_key in (("semantic_full_page", "baseline"), ("multiscale_tiling", "multiscale"), ("field_aware_generation", "all")):
        predictions = {}
        for record_id, document in generated.items():
            candidates = document[candidate_key]
            scores = [heuristic_probability(candidate) for candidate in candidates]
            predictions[record_id] = [row[0].value_m for row in monotonic_sequence(candidates, scores, 0.48)]
        ablations[name] = {
            "boundary_at_0_05m": boundary_metrics(predictions, references, 0.05),
            "boundary_at_0_10m": boundary_metrics(predictions, references, 0.10),
            "interval_at_0_05m": interval_metrics(predictions, references, 0.05),
            "prediction_count": sum(map(len, predictions.values())),
        }

    # Deterministic source-disjoint out-of-fold probabilistic ranking.
    oof_probabilities: dict[str, list[float]] = {}
    oof_thresholds: dict[str, float] = {}
    oof_risk_thresholds: dict[str, float] = {}
    fold_models = []
    for fold in range(args.folds):
        train_ids = [record_id for record_id in generated if fold_id(record_id, args.folds) != fold]
        test_ids = [record_id for record_id in generated if fold_id(record_id, args.folds) == fold]
        train_candidates = [candidate for record_id in train_ids for candidate in generated[record_id]["all"]]
        train_labels = [
            candidate_label(candidate, references[record_id], args.label_tolerance_m)
            for record_id in train_ids for candidate in generated[record_id]["all"]
        ]
        ranker = LogisticCandidateRanker(FEATURES).fit(train_candidates, train_labels)
        train_probabilities = ranker.predict_proba(train_candidates).tolist()
        grouped_train_candidates = {record_id: generated[record_id]["all"] for record_id in train_ids}
        grouped_train_probabilities = {
            record_id: ranker.predict_proba(generated[record_id]["all"]).tolist()
            for record_id in train_ids
        }
        threshold = tune_sequence_threshold(
            grouped_train_candidates, grouped_train_probabilities,
            {record_id: references[record_id] for record_id in train_ids},
        )
        risk_threshold = tune_threshold(train_probabilities, train_labels, minimum_precision=0.95)
        for record_id in test_ids:
            oof_probabilities[record_id] = ranker.predict_proba(generated[record_id]["all"]).tolist()
            oof_thresholds[record_id] = threshold
            oof_risk_thresholds[record_id] = risk_threshold
        fold_models.append({
            "fold": fold, "train_document_count": len(train_ids), "test_document_count": len(test_ids),
            "threshold": threshold, "risk_threshold": risk_threshold, "model": ranker.to_dict(),
        })

    raw_predictions = {}
    sequence_predictions = {}
    risk_predictions = {}
    conservative_predictions = {}
    prediction_rows = []
    for record_id, document in generated.items():
        probabilities = oof_probabilities[record_id]
        raw = raw_selection(document["all"], probabilities, oof_thresholds[record_id])
        sequence = monotonic_sequence(document["all"], probabilities, oof_thresholds[record_id])
        risk = monotonic_sequence(document["all"], probabilities, oof_risk_thresholds[record_id])
        conservative_scores = [risk_policy_probability(candidate) for candidate in document["all"]]
        conservative = monotonic_sequence(document["all"], conservative_scores, 0.80)
        raw_predictions[record_id] = [row[0].value_m for row in raw]
        sequence_predictions[record_id] = [row[0].value_m for row in sequence]
        risk_predictions[record_id] = [row[0].value_m for row in risk]
        conservative_predictions[record_id] = [row[0].value_m for row in conservative]
        prediction_rows.append({
            "record_id": record_id,
            "fold": fold_id(record_id, args.folds),
            "reference_boundary_count": len(references[record_id]),
            "candidate_count": len(document["all"]),
            "threshold": oof_thresholds[record_id],
            "risk_threshold": oof_risk_thresholds[record_id],
            "ranked_candidates": [
                serialize_candidate(candidate, probability)
                for candidate, probability in zip(document["all"], probabilities)
            ],
            "raw_selected": [serialize_candidate(*row) for row in raw],
            "sequence_selected": [serialize_candidate(*row) for row in sequence],
            "risk_selected": [serialize_candidate(*row) for row in risk],
            "conservative_selected": [serialize_candidate(*row) for row in conservative],
            "scale_calibrations": [page["scale"] for page in document["pages"] if page["scale"]],
            "terminal_cap_m": document["terminal_cap_m"],
        })

    ablations["learned_candidate_ranking"] = {
        "boundary_at_0_05m": boundary_metrics(raw_predictions, references, 0.05),
        "boundary_at_0_10m": boundary_metrics(raw_predictions, references, 0.10),
        "interval_at_0_05m": interval_metrics(raw_predictions, references, 0.05),
        "prediction_count": sum(map(len, raw_predictions.values())),
    }
    ablations["geological_monotonic_sequence"] = {
        "boundary_at_0_05m": boundary_metrics(sequence_predictions, references, 0.05),
        "boundary_at_0_10m": boundary_metrics(sequence_predictions, references, 0.10),
        "interval_at_0_05m": interval_metrics(sequence_predictions, references, 0.05),
        "prediction_count": sum(map(len, sequence_predictions.values())),
    }
    ablations["risk_aware_selective_prediction"] = {
        "boundary_at_0_05m": boundary_metrics(risk_predictions, references, 0.05),
        "boundary_at_0_10m": boundary_metrics(risk_predictions, references, 0.10),
        "interval_at_0_05m": interval_metrics(risk_predictions, references, 0.05),
        "accepted_boundary_count": sum(map(len, risk_predictions.values())),
        "boundary_coverage_against_reference": sum(map(len, risk_predictions.values())) / sum(map(len, references.values())),
        "abstention_rate_against_reference": 1 - min(1.0, sum(map(len, risk_predictions.values())) / sum(map(len, references.values()))),
    }
    ablations["conservative_risk_gate"] = {
        "boundary_at_0_05m": boundary_metrics(conservative_predictions, references, 0.05),
        "boundary_at_0_10m": boundary_metrics(conservative_predictions, references, 0.10),
        "interval_at_0_05m": interval_metrics(conservative_predictions, references, 0.05),
        "accepted_boundary_count": sum(map(len, conservative_predictions.values())),
        "coverage_against_reference": sum(map(len, conservative_predictions.values())) / sum(map(len, references.values())),
        "abstention_rate_against_reference": 1 - min(1.0, sum(map(len, conservative_predictions.values())) / sum(map(len, references.values()))),
    }

    # Freeze a final model on every v001 development source for one-time v002 use.
    all_candidates = [candidate for document in generated.values() for candidate in document["all"]]
    all_labels = [
        candidate_label(candidate, references[record_id], args.label_tolerance_m)
        for record_id, document in generated.items() for candidate in document["all"]
    ]
    final_ranker = LogisticCandidateRanker(FEATURES).fit(all_candidates, all_labels)
    final_probabilities = final_ranker.predict_proba(all_candidates).tolist()
    final_grouped_probabilities = {
        record_id: final_ranker.predict_proba(document["all"]).tolist()
        for record_id, document in generated.items()
    }
    final_threshold = tune_sequence_threshold(
        {record_id: document["all"] for record_id, document in generated.items()},
        final_grouped_probabilities, references,
    )
    final_risk_threshold = tune_threshold(final_probabilities, all_labels, minimum_precision=0.95)
    model = {
        "method_version": "bgs_layout_field_aware_v006",
        "training_manifest_sha256": file_sha256(args.manifest),
        "training_role": "development_only",
        "feature_names": list(FEATURES),
        "ranker": final_ranker.to_dict(),
        "decision_threshold": final_threshold,
        "risk_threshold": final_risk_threshold,
        "label_tolerance_m": args.label_tolerance_m,
        "candidate_generation": {
            "semantic_layout": "long_page_layout_v001",
            "multiscale": "2x gray+Otsu, PSM 6+11",
            "graphic_boundary": "depth-scale calibration plus image transition",
            "sequence": "strict increasing depth maximum log-odds path",
        },
    }
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.model_output.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = {
        "analysis_scope": "BGS v001 development-only source-disjoint layout/field-aware method ablation",
        "manifest_path": str(args.manifest), "manifest_sha256": file_sha256(args.manifest),
        "multiscale_analysis_sha256": file_sha256(args.multiscale_analysis),
        "field_roi_analysis_sha256": file_sha256(args.field_roi_analysis) if args.field_roi_analysis else None,
        "source_run": str(args.source_run), "source_run_predictions_sha256": file_sha256(args.source_run / "predictions.jsonl"),
        "reference_blinding": "candidate generation and visual/layout features are reference-blind; official intervals enter only ranker labels and post-hoc scoring",
        "document_count": len(sources), "page_count": sum(len(row["evaluation_pages"]) for row in sources),
        "reference_boundary_count": sum(map(len, references.values())),
        "candidate_count": sum(len(document["all"]) for document in generated.values()),
        "scale_calibrated_pages": sum(bool(page["scale"]) for document in generated.values() for page in document["pages"]),
        "fold_policy": f"sha256(record_id) modulo {args.folds}; source-group disjoint",
        "ablations": ablations,
        "fold_models": fold_models,
        "frozen_external_model_path": str(args.model_output),
        "frozen_external_model_sha256": file_sha256(args.model_output),
        "wall_time_seconds": time.perf_counter() - started,
        "predictions": prediction_rows,
        "limitations": [
            "BGS v001 has been inspected and is development evidence, not an external confirmation.",
            "Official interval endpoints label candidate correctness; lithology and description recovery are not evaluated in this experiment.",
            "The v002 external freeze must be run once with the serialized model and thresholds unchanged.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    for name, values in ablations.items():
        print(name, values.get("interval_at_0_05m"), values.get("boundary_at_0_05m"))


if __name__ == "__main__":
    main()
