#!/usr/bin/env python3
"""Nested source-disjoint risk acceptance over the v028 routed BGS parser."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


FEATURE_NAMES = (
    "intercept", "route_semantic", "route_baseline", "route_abstain",
    "family_scaled", "family_graphical", "family_explicit", "page_count",
    "candidate_count_log", "candidate_count_per_page", "role_selected_count",
    "prediction_count", "starts_at_zero", "strict_monotonic", "contiguous",
    "positive_sequence", "maximum_depth_log",
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fold_id(record_id: str, folds: int) -> int:
    return int(hashlib.sha256(record_id.encode()).hexdigest()[:8], 16) % folds


def refs(row: dict) -> list[float]:
    return sorted({float(value) for interval in row["intervals"] for value in (interval["top_depth_m"], interval["bottom_depth_m"])})


def exact_sequence(prediction: list[float], reference: list[float], tolerance: float = 0.05) -> bool:
    return len(prediction) == len(reference) and all(abs(left - right) <= tolerance for left, right in zip(sorted(prediction), sorted(reference)))


def safe_sequence(prediction: list[float], reference: list[float], tolerance: float = 0.05) -> bool:
    """True when every emitted boundary is supported, even if recall is incomplete."""
    return bool(prediction) and all(any(abs(value - target) <= tolerance for target in reference) for value in prediction)


def feature_vector(row: dict) -> list[float]:
    prediction = [float(value) for value in row.get("predicted_boundaries_m", [])]
    families = set(row.get("page_families", []))
    route = row.get("route", "")
    starts = bool(prediction) and abs(prediction[0]) <= 0.05
    monotonic = all(right > left for left, right in zip(prediction, prediction[1:]))
    contiguous = all(abs(right - left) <= 0.05 for left, right in zip(prediction, prediction[1:]))
    return [
        1.0,
        float(route == "semantic_role_expert"),
        float(route == "v024_baseline_expert"),
        float(route.startswith("abstain")),
        float("scaled_composite_log" in families),
        float("graphical_contact_log" in families),
        float("explicit_depth_range_table" in families),
        float(row.get("page_count", 1)),
        math.log1p(float(row.get("candidate_count_per_page", 0.0))),
        float(row.get("candidate_count_per_page", 0.0)),
        float(row.get("role_selected_count", 0)),
        float(len(prediction)),
        float(starts),
        float(monotonic),
        float(contiguous),
        float(monotonic and all(right > left for left, right in zip(prediction, prediction[1:]))),
        math.log1p(max(prediction, default=0.0)),
    ]


def fit_logistic(x: np.ndarray, y: np.ndarray, *, steps: int = 2500, rate: float = 0.04, l2: float = 0.1) -> dict:
    if len(set(y.tolist())) < 2:
        probability = float(y.mean()) if len(y) else 0.0
        return {"constant": probability, "mean": np.zeros(x.shape[1] - 1), "scale": np.ones(x.shape[1] - 1), "weights": np.zeros(x.shape[1])}
    mean = x[:, 1:].mean(axis=0)
    scale = x[:, 1:].std(axis=0)
    scale[scale < 1e-8] = 1.0
    z = x.copy()
    z[:, 1:] = (z[:, 1:] - mean) / scale
    weights = np.zeros(z.shape[1], dtype=float)
    for _ in range(steps):
        logits = np.clip(z @ weights, -30.0, 30.0)
        p = 1.0 / (1.0 + np.exp(-logits))
        gradient = z.T @ (p - y) / len(y)
        gradient[1:] += l2 * weights[1:]
        weights -= rate * gradient
    return {"constant": None, "mean": mean, "scale": scale, "weights": weights}


def predict(model: dict, x: np.ndarray) -> np.ndarray:
    if model.get("constant") is not None:
        return np.full(len(x), float(model["constant"]))
    z = x.copy()
    z[:, 1:] = (z[:, 1:] - model["mean"]) / model["scale"]
    logits = np.clip(z @ model["weights"], -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-logits))


def threshold_from_oof(probabilities: np.ndarray, labels: np.ndarray, minimum_accuracy: float = 0.95) -> float:
    candidates = sorted({0.0, 1.0, *map(float, probabilities)})
    feasible = []
    for threshold in candidates:
        accepted = probabilities >= threshold
        if not accepted.any():
            continue
        accuracy = float(labels[accepted].mean())
        if accuracy >= minimum_accuracy:
            feasible.append((int(accepted.sum()), accuracy, threshold))
    return max(feasible, default=(0, 0.0, 1.0))[2]


def nested_gate(records: list[dict], labels: np.ndarray, folds: int) -> tuple[np.ndarray, list[dict]]:
    probabilities = np.zeros(len(records), dtype=float)
    fold_reports = []
    for target_fold in range(folds):
        train_indices = [i for i, row in enumerate(records) if fold_id(row["record_id"], folds) != target_fold]
        test_indices = [i for i, row in enumerate(records) if fold_id(row["record_id"], folds) == target_fold]
        if not test_indices:
            continue
        inner_oof = np.zeros(len(train_indices), dtype=float)
        inner_folds = sorted({fold_id(records[i]["record_id"], folds) for i in train_indices})
        for inner_fold in inner_folds:
            fit = [j for j, i in enumerate(train_indices) if fold_id(records[i]["record_id"], folds) != inner_fold]
            val = [j for j, i in enumerate(train_indices) if fold_id(records[i]["record_id"], folds) == inner_fold]
            if not val:
                continue
            model = fit_logistic(np.asarray([feature_vector(records[train_indices[j]]) for j in fit], dtype=float), labels[np.asarray([train_indices[j] for j in fit])])
            inner_oof[val] = predict(model, np.asarray([feature_vector(records[train_indices[j]]) for j in val], dtype=float))
        threshold = threshold_from_oof(inner_oof, labels[np.asarray(train_indices)], 0.95)
        model = fit_logistic(np.asarray([feature_vector(records[i]) for i in train_indices], dtype=float), labels[np.asarray(train_indices)])
        probabilities[test_indices] = predict(model, np.asarray([feature_vector(records[i]) for i in test_indices], dtype=float))
        fold_reports.append({
            "fold": target_fold,
            "train_count": len(train_indices),
            "test_count": len(test_indices),
            "threshold": threshold,
            "accepted_test_count": int((probabilities[test_indices] >= threshold).sum()),
            "test_safe_count": int(labels[np.asarray(test_indices)].sum()),
        })
    return probabilities, fold_reports


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--fold", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest = load_jsonl(args.manifest)
    fold_rows = [json.loads(path.read_text(encoding="utf-8")) for path in args.fold]
    routed_rows = [row for report in fold_rows for row in report.get("predictions", [])]
    routed = {row["record_id"]: row for row in routed_rows}
    records = [routed[row["record_id"]] for row in manifest]
    references = {row["record_id"]: refs(row) for row in manifest}
    labels = np.asarray([float(safe_sequence(records[i].get("predicted_boundaries_m", []), references[row["record_id"]])) for i, row in enumerate(manifest)])
    probabilities, fold_reports = nested_gate(records, labels, args.folds)
    threshold = threshold_from_oof(probabilities, labels, 0.95)
    accepted = probabilities >= threshold
    baseline_predictions = {row["record_id"]: [float(value) for value in records[i].get("predicted_boundaries_m", [])] for i, row in enumerate(manifest)}
    selective_predictions = {row["record_id"]: (baseline_predictions[row["record_id"]] if accepted[i] else []) for i, row in enumerate(manifest)}
    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_nested_source_disjoint_risk_acceptance",
        "method_version": "bgs_routed_moe_risk_acceptance_v029",
        "manifest": str(args.manifest),
        "fold_artifacts": [str(path) for path in args.fold],
        "fold_policy": f"sha256(record_id) modulo {args.folds}; target-fold gate fit excludes target labels",
        "feature_names": list(FEATURE_NAMES),
        "threshold": threshold,
        "document_count": len(records),
        "accepted_document_count": int(accepted.sum()),
        "coverage": float(accepted.mean()),
        "accepted_document_safety": float(labels[accepted].mean()) if accepted.any() else None,
        "accepted_document_error_rate": float(1.0 - labels[accepted].mean()) if accepted.any() else None,
        "baseline": {
            "boundary": boundary_metrics(baseline_predictions, references, 0.05),
            "interval": interval_metrics(baseline_predictions, references, 0.05),
        },
        "selective": {
            "boundary": boundary_metrics(selective_predictions, references, 0.05),
            "interval": interval_metrics(selective_predictions, references, 0.05),
        },
        "fold_reports": fold_reports,
        "probabilities": [
            {"record_id": row["record_id"], "probability": float(probabilities[i]), "safe_label": bool(labels[i]), "accepted": bool(accepted[i]), "route": records[i].get("route"), "page_families": records[i].get("page_families", [])}
            for i, row in enumerate(manifest)
        ],
        "reference_blinding": "v028 target-fold predictions were fixed before references were used; gate fitting excludes each target fold",
        "limitations": [
            "This is BGS v001 nested development evidence over reused v024/v025 artifacts, not untouched external confirmation.",
            "The gate changes acceptance only and cannot recover omitted boundaries.",
            "BGS v003 was not opened.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"threshold": threshold, "coverage": report["coverage"], "accepted_safety": report["accepted_document_safety"], "baseline_interval": report["baseline"]["interval"], "selective_interval": report["selective"]["interval"]}, indent=2))


if __name__ == "__main__":
    main()
