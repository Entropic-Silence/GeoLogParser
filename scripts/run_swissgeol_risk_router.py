#!/usr/bin/env python3
"""Fit a reference-blind document risk gate on Swissgeol development pages.

The extraction expert is unchanged.  The learned component estimates whether
the complete baseline interval sequence is safe to auto-accept from page/OCR
and sequence features.  Training labels are document exactness on the declared
development manifest; held-out references are loaded only after decisions are
fixed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geologparser.layout import classify_borehole_page
from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


FEATURE_NAMES = (
    "intercept",
    "page_family_supported",
    "page_family_confidence",
    "page_count",
    "region_count_log",
    "mean_ocr_confidence",
    "numeric_region_fraction",
    "predicted_interval_count",
    "predicted_boundary_count",
    "starts_at_zero",
    "strict_monotonic",
    "contiguous_sequence",
    "all_positive_thickness",
    "maximum_depth_log",
    "maximum_depth_ocr_supported",
    "all_boundaries_ocr_supported",
    "has_tiefe",
    "has_bis",
    "has_beschreibung",
    "has_schichtenverzeichnis",
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fold_id(record_id: str, folds: int) -> int:
    return int(hashlib.sha256(record_id.encode()).hexdigest()[:8], 16) % folds


def numeric_value(text: str) -> float | None:
    cleaned = text.strip().replace(",", ".").replace("O", "0").replace("o", "0")
    match = re.fullmatch(r"[^0-9]*([0-9]{1,4}(?:\.[0-9]{1,3})?)[^0-9]*", cleaned)
    return float(match.group(1)) if match else None


def baseline_boundaries(row: dict) -> list[float]:
    return sorted({
        float(value)
        for interval in row.get("predicted_intervals", [])
        for value in (interval["top_depth_m"], interval["bottom_depth_m"])
    })


def gold_boundaries(row: dict) -> list[float]:
    return sorted({
        float(value)
        for interval in row["intervals"]
        for value in (interval["top_depth_m"], interval["bottom_depth_m"])
    })


def features(manifest_row: dict, prediction_row: dict, source_run: Path) -> tuple[list[float], dict]:
    record_id = manifest_row["record_id"]
    all_regions = []
    assessments = []
    for page in manifest_row["evaluation_pages"]:
        regions = load_jsonl(source_run / f"{record_id}_page-{page}_regions.jsonl")
        image = cv2.imread(str(source_run / f"{record_id}_page-{page}.png"), cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue
        assessments.append(classify_borehole_page(regions, width=image.shape[1], height=image.shape[0]))
        all_regions.extend(regions)
    texts = [str(row.get("text") or "") for row in all_regions]
    joined = " ".join(texts).lower()
    numeric = [value for text in texts if (value := numeric_value(text)) is not None]
    intervals = prediction_row.get("predicted_intervals", [])
    boundaries = baseline_boundaries(prediction_row)
    starts_at_zero = bool(boundaries) and abs(boundaries[0]) <= 0.05
    strict_monotonic = all(
        float(interval["bottom_depth_m"]) > float(interval["top_depth_m"])
        for interval in intervals
    ) and all(
        float(left["top_depth_m"]) <= float(left["bottom_depth_m"]) <= float(right["bottom_depth_m"])
        for left, right in zip(intervals, intervals[1:])
    )
    contiguous = all(
        abs(float(left["bottom_depth_m"]) - float(right["top_depth_m"])) <= 0.05
        for left, right in zip(intervals, intervals[1:])
    )
    positive = all(float(interval["bottom_depth_m"]) - float(interval["top_depth_m"]) > 0 for interval in intervals)
    maximum = max(boundaries, default=0.0)
    support = lambda value: any(abs(value - candidate) <= 0.01 for candidate in numeric)
    supported = [assessment for assessment in assessments if assessment.family != "unsupported"]
    family_confidence = max((assessment.confidence for assessment in supported), default=0.0)
    vector = [
        1.0,
        float(bool(supported)),
        family_confidence,
        float(len(manifest_row["evaluation_pages"])),
        math.log1p(len(all_regions)),
        float(np.mean([float(row.get("confidence") or 0.0) for row in all_regions])) if all_regions else 0.0,
        len(numeric) / max(1, len(all_regions)),
        float(len(intervals)),
        float(len(boundaries)),
        float(starts_at_zero),
        float(strict_monotonic),
        float(contiguous),
        float(positive),
        math.log1p(maximum),
        float(bool(boundaries) and support(maximum)),
        sum(support(value) for value in boundaries) / max(1, len(boundaries)),
        float("tiefe" in joined),
        float(re.search(r"\bbis\b", joined) is not None),
        float("beschreibung" in joined),
        float("schichtenverzeichnis" in joined),
    ]
    return vector, {
        "page_families": [assessment.family for assessment in assessments],
        "baseline_boundary_count": len(boundaries),
        "baseline_interval_count": len(intervals),
    }


def fit_logistic(x: np.ndarray, y: np.ndarray, *, steps: int = 2500, rate: float = 0.05, l2: float = 0.08) -> dict:
    mean = x[:, 1:].mean(axis=0)
    scale = x[:, 1:].std(axis=0)
    scale[scale < 1e-8] = 1.0
    standardized = x.copy()
    standardized[:, 1:] = (standardized[:, 1:] - mean) / scale
    weights = np.zeros(standardized.shape[1], dtype=float)
    for _ in range(steps):
        logits = np.clip(standardized @ weights, -30.0, 30.0)
        probability = 1.0 / (1.0 + np.exp(-logits))
        gradient = standardized.T @ (probability - y) / len(y)
        gradient[1:] += l2 * weights[1:]
        weights -= rate * gradient
    return {"mean": mean, "scale": scale, "weights": weights}


def predict(model: dict, x: np.ndarray) -> np.ndarray:
    standardized = x.copy()
    standardized[:, 1:] = (standardized[:, 1:] - model["mean"]) / model["scale"]
    logits = np.clip(standardized @ model["weights"], -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-logits))


def select_threshold(probabilities: np.ndarray, labels: np.ndarray, minimum_accuracy: float) -> dict:
    candidates = sorted({0.0, 1.0, *map(float, probabilities)})
    rows = []
    for threshold in candidates:
        accepted = probabilities >= threshold
        count = int(accepted.sum())
        accuracy = float(labels[accepted].mean()) if count else None
        rows.append({"threshold": threshold, "accepted": count, "accuracy": accuracy})
    feasible = [row for row in rows if row["accepted"] > 0 and row["accuracy"] is not None and row["accuracy"] >= minimum_accuracy]
    selected = max(feasible, key=lambda row: (row["accepted"], row["accuracy"], row["threshold"])) if feasible else {"threshold": 1.0, "accepted": 0, "accuracy": None}
    return {"selected": selected, "curve": rows}


def calibration_metrics(probabilities: np.ndarray, labels: np.ndarray, bins: int = 5) -> dict:
    clipped = np.clip(probabilities, 1e-8, 1.0 - 1e-8)
    brier = float(np.mean((clipped - labels) ** 2))
    log_loss = float(-np.mean(labels * np.log(clipped) + (1.0 - labels) * np.log(1.0 - clipped)))
    ece = 0.0
    rows = []
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        mask = (clipped >= lower) & (clipped < upper if index < bins - 1 else clipped <= upper)
        count = int(mask.sum())
        if not count:
            rows.append({"lower": lower, "upper": upper, "count": 0, "confidence": None, "accuracy": None})
            continue
        confidence = float(clipped[mask].mean())
        accuracy = float(labels[mask].mean())
        ece += count / len(labels) * abs(confidence - accuracy)
        rows.append({"lower": lower, "upper": upper, "count": count, "confidence": confidence, "accuracy": accuracy})
    return {"brier_score": brier, "negative_log_likelihood": log_loss, "expected_calibration_error": ece, "bins": rows}


def coverage_accuracy_curve(probabilities: np.ndarray, labels: np.ndarray) -> list[dict]:
    output = []
    for threshold in (0.0, 0.25, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.98):
        accepted = probabilities >= threshold
        count = int(accepted.sum())
        output.append({
            "threshold": threshold,
            "accepted_document_count": count,
            "coverage": count / len(labels),
            "accepted_document_accuracy": float(labels[accepted].mean()) if count else None,
            "accepted_document_error_rate": float(1.0 - labels[accepted].mean()) if count else None,
        })
    return output


def evaluate(
    manifest: list[dict], predictions: dict[str, dict], source_run: Path,
    model: dict, threshold: float,
) -> dict:
    x_rows = []
    diagnostics = []
    gold = {row["record_id"]: gold_boundaries(row) for row in manifest}
    baseline = {row["record_id"]: baseline_boundaries(predictions[row["record_id"]]) for row in manifest}
    for row in manifest:
        vector, detail = features(row, predictions[row["record_id"]], source_run)
        x_rows.append(vector)
        diagnostics.append({"record_id": row["record_id"], **detail})
    probabilities = predict(model, np.asarray(x_rows, dtype=float))
    routed = {}
    exact = []
    for row, probability, detail in zip(manifest, probabilities, diagnostics):
        record_id = row["record_id"]
        accepted = bool(probability >= threshold)
        routed[record_id] = baseline[record_id] if accepted else []
        label = bool(predictions[record_id].get("document_full_exact"))
        exact.append(label)
        detail.update({"acceptance_probability": float(probability), "accepted": accepted, "document_exact": label})
    accepted_labels = [label for label, detail in zip(exact, diagnostics) if detail["accepted"]]
    return {
        "document_count": len(manifest),
        "accepted_document_count": len(accepted_labels),
        "coverage": len(accepted_labels) / max(1, len(manifest)),
        "accepted_document_accuracy": sum(accepted_labels) / len(accepted_labels) if accepted_labels else None,
        "accepted_document_error_rate": 1.0 - sum(accepted_labels) / len(accepted_labels) if accepted_labels else None,
        "calibration": calibration_metrics(probabilities, np.asarray(exact, dtype=float)),
        "coverage_accuracy_curve": coverage_accuracy_curve(probabilities, np.asarray(exact, dtype=float)),
        "baseline": {"boundary": boundary_metrics(baseline, gold, 0.05), "interval": interval_metrics(baseline, gold, 0.05)},
        "routed": {"boundary": boundary_metrics(routed, gold, 0.05), "interval": interval_metrics(routed, gold, 0.05)},
        "diagnostics": diagnostics,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development-manifest", type=Path, required=True)
    parser.add_argument("--development-source-run", type=Path, required=True)
    parser.add_argument("--development-predictions", type=Path, required=True)
    parser.add_argument("--heldout-manifest", type=Path, required=True)
    parser.add_argument("--heldout-source-run", type=Path, required=True)
    parser.add_argument("--heldout-predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--minimum-oof-accuracy", type=float, default=0.95)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    development = load_jsonl(args.development_manifest)
    development_predictions = {row["record_id"]: row for row in load_jsonl(args.development_predictions)}
    x_rows, labels = [], []
    for row in development:
        vector, _ = features(row, development_predictions[row["record_id"]], args.development_source_run)
        x_rows.append(vector)
        labels.append(float(development_predictions[row["record_id"]].get("document_full_exact")))
    x = np.asarray(x_rows, dtype=float)
    y = np.asarray(labels, dtype=float)
    oof = np.zeros(len(development), dtype=float)
    fold_models = []
    for fold in range(args.folds):
        train = np.asarray([fold_id(row["record_id"], args.folds) != fold for row in development])
        test = ~train
        model = fit_logistic(x[train], y[train])
        oof[test] = predict(model, x[test])
        fold_models.append({"fold": fold, "train_count": int(train.sum()), "test_count": int(test.sum())})
    threshold_report = select_threshold(oof, y, args.minimum_oof_accuracy)
    threshold = float(threshold_report["selected"]["threshold"])
    final_model = fit_logistic(x, y)
    development_result = evaluate(development, development_predictions, args.development_source_run, final_model, threshold)
    # Held-out predictions are fixed before their exactness/reference labels are
    # read by evaluate; the threshold and full-development model are immutable.
    heldout = load_jsonl(args.heldout_manifest)
    heldout_predictions = {row["record_id"]: row for row in load_jsonl(args.heldout_predictions)}
    heldout_result = evaluate(heldout, heldout_predictions, args.heldout_source_run, final_model, threshold)
    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_development_fitted_heldout_validation",
        "method_version": "swissgeol_page_family_risk_router_v001",
        "feature_names": list(FEATURE_NAMES),
        "fold_policy": f"sha256(record_id) modulo {args.folds}",
        "minimum_oof_accuracy": args.minimum_oof_accuracy,
        "oof_threshold_selection": threshold_report,
        "oof_probabilities": [
            {"record_id": row["record_id"], "probability": float(probability), "label": bool(label), "fold": fold_id(row["record_id"], args.folds)}
            for row, probability, label in zip(development, oof, y)
        ],
        "fold_models": fold_models,
        "final_model": {
            "weights": final_model["weights"].tolist(),
            "mean": final_model["mean"].tolist(),
            "scale": final_model["scale"].tolist(),
        },
        "development": development_result,
        "heldout": heldout_result,
        "reference_blinding": "threshold and model fitted only on development document-exact labels; held-out decisions fixed before held-out labels were scored",
        "limitations": [
            "The held-out Swissgeol split was previously consumed by the multilingual alias coverage audit and is validation rather than untouched external confirmation.",
            "The router changes acceptance only; it does not improve the extraction expert or recover missing intervals.",
            "Small development and accepted-action counts require uncertainty-aware interpretation.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"threshold": threshold, "development": {k: development_result[k] for k in ("coverage", "accepted_document_accuracy")}, "heldout": {k: heldout_result[k] for k in ("coverage", "accepted_document_accuracy")}, "heldout_routed_interval": heldout_result["routed"]["interval"]}, indent=2))


if __name__ == "__main__":
    main()
