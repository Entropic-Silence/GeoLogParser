"""Initial exact, numeric, interval-boundary, and calibration metrics."""

from __future__ import annotations

from decimal import Decimal
from math import floor
from typing import Any, Sequence

from .types import MetricResult, validate_pairs


def exact_match(references: Sequence[Any], predictions: Sequence[Any], name: str = "exact_match") -> MetricResult:
    validate_pairs(references, predictions)
    correct = sum(reference == prediction for reference, prediction in zip(references, predictions))
    total = len(references)
    return MetricResult(name, correct / total if total else None, correct, total, "ratio")


def mean_absolute_error(references: Sequence[float | None], predictions: Sequence[float | None], name: str = "mae") -> MetricResult:
    validate_pairs(references, predictions)
    errors = [abs(float(r) - float(p)) for r, p in zip(references, predictions) if r is not None and p is not None]
    return MetricResult(name, sum(errors) / len(errors) if errors else None, sum(errors), len(errors), "same_as_input")


def extraction_coverage(predictions: Sequence[Any], name: str = "extraction_coverage") -> MetricResult:
    present = sum(value is not None and value != "" for value in predictions)
    total = len(predictions)
    return MetricResult(name, present / total if total else None, present, total, "ratio")


def numeric_with_missing_mae(
    references: Sequence[float | None],
    predictions: Sequence[float | None],
    name: str = "numeric_mae",
) -> dict[str, MetricResult]:
    """Return paired-value MAE together with prediction coverage.

    MAE never silently treats a missing prediction as zero. Consumers must
    report the companion coverage metric to expose abstention/extraction loss.
    """
    validate_pairs(references, predictions)
    eligible_predictions = [prediction for reference, prediction in zip(references, predictions) if reference is not None]
    eligible_references = [reference for reference in references if reference is not None]
    paired_references = [reference for reference, prediction in zip(references, predictions) if reference is not None and prediction is not None]
    paired_predictions = [prediction for reference, prediction in zip(references, predictions) if reference is not None and prediction is not None]
    return {
        name: mean_absolute_error(paired_references, paired_predictions, name),
        f"{name}_coverage": extraction_coverage(eligible_predictions, f"{name}_coverage"),
        f"{name}_reference_count": MetricResult(
            f"{name}_reference_count", float(len(eligible_references)), len(eligible_references), 1.0, "count"
        ),
    }


def boundary_accuracy(
    references: Sequence[float | None],
    predictions: Sequence[float | None],
    tolerance: float,
    name: str | None = None,
) -> MetricResult:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    validate_pairs(references, predictions)
    decimal_tolerance = Decimal(str(tolerance))
    evaluated = [
        (Decimal(str(r)), Decimal(str(p)))
        for r, p in zip(references, predictions)
        if r is not None and p is not None
    ]
    correct = sum(abs(r - p) <= decimal_tolerance for r, p in evaluated)
    return MetricResult(
        name or f"boundary_accuracy_at_{tolerance:g}",
        correct / len(evaluated) if evaluated else None,
        correct,
        len(evaluated),
        "ratio",
        {"tolerance": tolerance},
    )


def brier_score(labels: Sequence[int], probabilities: Sequence[float]) -> MetricResult:
    validate_pairs(labels, probabilities)
    if any(label not in (0, 1) for label in labels):
        raise ValueError("Brier labels must be binary")
    if any(probability < 0 or probability > 1 for probability in probabilities):
        raise ValueError("probabilities must be within [0, 1]")
    squared = [(probability - label) ** 2 for label, probability in zip(labels, probabilities)]
    return MetricResult("brier_score", sum(squared) / len(squared) if squared else None, sum(squared), len(squared), "score")


def expected_calibration_error(labels: Sequence[int], probabilities: Sequence[float], bins: int = 10) -> MetricResult:
    validate_pairs(labels, probabilities)
    if bins <= 0:
        raise ValueError("bins must be positive")
    if any(label not in (0, 1) for label in labels):
        raise ValueError("ECE labels must be binary")
    if any(probability < 0 or probability > 1 for probability in probabilities):
        raise ValueError("probabilities must be within [0, 1]")
    if not labels:
        return MetricResult("expected_calibration_error", None, 0.0, 0, "score", {"bins": bins, "bin_stats": []})

    grouped: list[list[tuple[int, float]]] = [[] for _ in range(bins)]
    for label, probability in zip(labels, probabilities):
        index = min(floor(probability * bins), bins - 1)
        grouped[index].append((label, probability))
    contribution = 0.0
    stats = []
    for index, values in enumerate(grouped):
        if not values:
            continue
        accuracy = sum(label for label, _ in values) / len(values)
        confidence = sum(probability for _, probability in values) / len(values)
        contribution += len(values) / len(labels) * abs(accuracy - confidence)
        stats.append({"bin": index, "count": len(values), "accuracy": accuracy, "confidence": confidence})
    return MetricResult("expected_calibration_error", contribution, contribution, 1.0, "score", {"bins": bins, "bin_stats": stats})


def interval_prf1(reference_ids: Sequence[set[str]], prediction_ids: Sequence[set[str]]) -> dict[str, MetricResult]:
    """Exact-ID placeholder matching; boundary-aware matching is a future strategy adapter."""
    validate_pairs(reference_ids, prediction_ids)
    true_positive = sum(len(reference & prediction) for reference, prediction in zip(reference_ids, prediction_ids))
    false_positive = sum(len(prediction - reference) for reference, prediction in zip(reference_ids, prediction_ids))
    false_negative = sum(len(reference - prediction) for reference, prediction in zip(reference_ids, prediction_ids))
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else None
    recall = true_positive / recall_denominator if recall_denominator else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    return {
        "interval_precision": MetricResult("interval_precision", precision, true_positive, precision_denominator, "ratio"),
        "interval_recall": MetricResult("interval_recall", recall, true_positive, recall_denominator, "ratio"),
        "interval_f1": MetricResult("interval_f1", f1, 0.0 if f1 is None else f1, 1.0 if f1 is not None else 0.0, "ratio"),
    }
