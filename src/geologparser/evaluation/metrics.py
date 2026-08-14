"""Initial exact, numeric, interval-boundary, and calibration metrics."""

from __future__ import annotations

from decimal import Decimal
from math import floor
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .types import MetricResult, validate_pairs


def _levenshtein(reference: Sequence[Any], prediction: Sequence[Any]) -> int:
    """Memory-bounded Levenshtein distance for character/token metrics."""
    previous = list(range(len(prediction) + 1))
    for reference_index, reference_item in enumerate(reference, 1):
        current = [reference_index]
        for prediction_index, prediction_item in enumerate(prediction, 1):
            current.append(min(
                current[-1] + 1,
                previous[prediction_index] + 1,
                previous[prediction_index - 1] + (reference_item != prediction_item),
            ))
        previous = current
    return previous[-1]


def sequence_error_rate(
    references: Sequence[str],
    predictions: Sequence[str],
    *,
    unit: str = "character",
    name: str | None = None,
) -> MetricResult:
    """Micro CER/WER with explicit empty-reference handling.

    For WER the contract is whitespace tokenization. Chinese word segmentation
    must be supplied as already space-delimited strings and recorded by the
    caller; the metric never silently selects a language model/tokenizer.
    """
    validate_pairs(references, predictions)
    if unit not in {"character", "word"}:
        raise ValueError("unit must be character or word")
    transform = (lambda value: list(value)) if unit == "character" else (lambda value: value.split())
    edits = 0
    denominator = 0
    empty_reference_insertions = 0
    for reference, prediction in zip(references, predictions):
        if not isinstance(reference, str) or not isinstance(prediction, str):
            raise TypeError("sequence error rate inputs must be strings")
        reference_units = transform(reference)
        prediction_units = transform(prediction)
        distance = _levenshtein(reference_units, prediction_units)
        if reference_units:
            edits += distance
            denominator += len(reference_units)
        else:
            # Insertions against an empty reference are traced but cannot be
            # divided by zero. Dataset protocols should report them separately.
            empty_reference_insertions += distance
    default_name = "cer" if unit == "character" else "wer"
    return MetricResult(
        name or default_name,
        edits / denominator if denominator else None,
        edits,
        denominator,
        "error_rate",
        {"unit": unit, "empty_reference_insertions": empty_reference_insertions},
    )


def character_error_rate(references: Sequence[str], predictions: Sequence[str]) -> MetricResult:
    return sequence_error_rate(references, predictions, unit="character", name="cer")


def word_error_rate(references: Sequence[str], predictions: Sequence[str]) -> MetricResult:
    return sequence_error_rate(references, predictions, unit="word", name="wer")


def numeric_character_error_rate(
    references: Sequence[str], predictions: Sequence[str], *, include_signs: bool = True,
) -> MetricResult:
    """CER over digits, decimal points, and optionally signs only."""
    pattern = r"[^0-9.\-+]" if include_signs else r"[^0-9.]"
    import re

    numeric_references = [re.sub(pattern, "", value) for value in references]
    numeric_predictions = [re.sub(pattern, "", value) for value in predictions]
    result = sequence_error_rate(
        numeric_references, numeric_predictions, unit="character", name="numeric_cer",
    )
    return MetricResult(
        result.name, result.value, result.numerator, result.denominator, result.unit,
        result.details | {"include_signs": include_signs, "filtered_alphabet": "0-9.-+" if include_signs else "0-9."},
    )


def normalized_edit_similarity(
    references: Sequence[str], predictions: Sequence[str], *, unit: str = "character",
    name: str = "normalized_edit_similarity",
) -> MetricResult:
    """Macro normalized Levenshtein similarity with explicit empty semantics."""
    validate_pairs(references, predictions)
    if unit not in {"character", "word"}:
        raise ValueError("unit must be character or word")
    transform = (lambda value: list(value)) if unit == "character" else (lambda value: value.split())
    similarities = []
    for reference, prediction in zip(references, predictions):
        if not isinstance(reference, str) or not isinstance(prediction, str):
            raise TypeError("normalized edit similarity inputs must be strings")
        reference_units, prediction_units = transform(reference), transform(prediction)
        denominator = max(len(reference_units), len(prediction_units))
        similarities.append(
            1.0 if denominator == 0 else 1 - _levenshtein(reference_units, prediction_units) / denominator
        )
    return MetricResult(
        name, sum(similarities) / len(similarities) if similarities else None,
        sum(similarities), len(similarities), "similarity",
        {"aggregation": "macro", "unit": unit, "normalizer": "max_reference_prediction_length"},
    )


def critical_numerical_error_rate(
    references: Sequence[float | None], predictions: Sequence[float | None], *,
    threshold: float, name: str = "critical_numerical_error_rate",
) -> MetricResult:
    """Rate of missing or over-threshold predictions on present numeric GT."""
    validate_pairs(references, predictions)
    if threshold < 0:
        raise ValueError("critical numerical threshold must be non-negative")
    decimal_threshold = Decimal(str(threshold))
    eligible = [(reference, prediction) for reference, prediction in zip(references, predictions) if reference is not None]
    missing_predictions = sum(prediction is None for _, prediction in eligible)
    over_threshold = sum(
        abs(Decimal(str(reference)) - Decimal(str(prediction))) > decimal_threshold
        for reference, prediction in eligible if prediction is not None
    )
    critical = missing_predictions + over_threshold
    return MetricResult(
        name, critical / len(eligible) if eligible else None, critical, len(eligible), "ratio",
        {
            "threshold": threshold, "comparison": "absolute_error > threshold",
            "missing_prediction_is_critical": True,
            "missing_prediction_count": missing_predictions,
            "over_threshold_count": over_threshold,
            "missing_reference_count": len(references) - len(eligible),
        },
    )


def hierarchical_classification_metrics(
    reference_paths: Sequence[Sequence[str] | None],
    prediction_paths: Sequence[Sequence[str] | None],
) -> dict[str, MetricResult]:
    """Micro ancestor-set P/R/F1 plus path exact match from supplied paths."""
    validate_pairs(reference_paths, prediction_paths)
    reference_sets: list[set[str]] = []
    prediction_sets: list[set[str]] = []
    exact = 0
    for reference, prediction in zip(reference_paths, prediction_paths):
        reference_tuple = tuple(reference or ())
        prediction_tuple = tuple(prediction or ())
        if len(set(reference_tuple)) != len(reference_tuple) or len(set(prediction_tuple)) != len(prediction_tuple):
            raise ValueError("ontology paths must not repeat a node")
        if not reference_tuple:
            continue
        reference_sets.append(set(reference_tuple))
        prediction_sets.append(set(prediction_tuple))
        exact += reference_tuple == prediction_tuple
    true_positive = sum(len(reference & prediction) for reference, prediction in zip(reference_sets, prediction_sets))
    predicted = sum(len(path) for path in prediction_sets)
    reference = sum(len(path) for path in reference_sets)
    precision = true_positive / predicted if predicted else None
    recall = true_positive / reference if reference else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall else None
    )
    details = {
        "aggregation": "micro_ancestor_set", "auxiliary_metric": True,
        "does_not_replace_exact_match": True,
    }
    return {
        "hierarchical_precision": MetricResult(
            "hierarchical_precision", precision, true_positive, predicted, "ratio", details,
        ),
        "hierarchical_recall": MetricResult(
            "hierarchical_recall", recall, true_positive, reference, "ratio", details,
        ),
        "hierarchical_f1": MetricResult(
            "hierarchical_f1", f1, 0.0 if f1 is None else f1,
            1.0 if f1 is not None else 0.0, "ratio", details,
        ),
        "hierarchical_path_exact_match": MetricResult(
            "hierarchical_path_exact_match", exact / len(reference_sets) if reference_sets else None,
            exact, len(reference_sets), "ratio", details | {
                "missing_reference_path_count": len(reference_paths) - len(reference_sets),
            },
        ),
        "hierarchical_prediction_coverage": MetricResult(
            "hierarchical_prediction_coverage",
            sum(bool(path) for path in prediction_sets) / len(prediction_sets) if prediction_sets else None,
            sum(bool(path) for path in prediction_sets), len(prediction_sets), "ratio",
            details | {"denominator": "non-missing reference ontology paths"},
        ),
    }


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
    if precision_denominator == 0 and recall_denominator == 0:
        f1 = None
    elif true_positive == 0:
        f1 = 0.0
    else:
        assert precision is not None and recall is not None
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "interval_precision": MetricResult("interval_precision", precision, true_positive, precision_denominator, "ratio"),
        "interval_recall": MetricResult("interval_recall", recall, true_positive, recall_denominator, "ratio"),
        "interval_f1": MetricResult("interval_f1", f1, 0.0 if f1 is None else f1, 1.0 if f1 is not None else 0.0, "ratio"),
    }


@dataclass(frozen=True)
class IntervalMatch:
    reference_index: int
    prediction_index: int
    top_error_m: float
    bottom_error_m: float


def _boundary_pair(interval: Mapping[str, Any]) -> tuple[Decimal, Decimal] | None:
    def value(name: str) -> Any:
        candidate = interval.get(name)
        return candidate.get("value") if isinstance(candidate, Mapping) else candidate

    top = value("top_depth_m")
    bottom = value("bottom_depth_m")
    if top is None or bottom is None:
        return None
    try:
        return Decimal(str(top)), Decimal(str(bottom))
    except Exception:
        return None


def match_intervals_by_boundaries(
    references: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
    tolerance_m: float = 0.05,
) -> tuple[list[IntervalMatch], list[int], list[int]]:
    """Order-preserving maximum-cardinality boundary matching.

    A pair is eligible only when both top and bottom errors are within the
    inclusive tolerance. Dynamic programming first maximizes match count, then
    minimizes summed top+bottom error. Order preservation prevents crossed
    matches between successive strata. Missing boundaries cannot match.
    """
    if tolerance_m < 0:
        raise ValueError("tolerance must be non-negative")
    tolerance = Decimal(str(tolerance_m))
    ref_pairs = [_boundary_pair(interval) for interval in references]
    pred_pairs = [_boundary_pair(interval) for interval in predictions]
    # Each cell stores (match_count, negative_total_error, match_path).
    table: list[list[tuple[int, Decimal, tuple[tuple[int, int, Decimal, Decimal], ...]]]] = [
        [(0, Decimal("0"), ()) for _ in range(len(predictions) + 1)]
        for _ in range(len(references) + 1)
    ]
    for ref_index in range(1, len(references) + 1):
        for pred_index in range(1, len(predictions) + 1):
            candidates = [table[ref_index - 1][pred_index], table[ref_index][pred_index - 1]]
            ref_pair = ref_pairs[ref_index - 1]
            pred_pair = pred_pairs[pred_index - 1]
            if ref_pair is not None and pred_pair is not None:
                top_error = abs(ref_pair[0] - pred_pair[0])
                bottom_error = abs(ref_pair[1] - pred_pair[1])
                if top_error <= tolerance and bottom_error <= tolerance:
                    previous = table[ref_index - 1][pred_index - 1]
                    candidates.append((
                        previous[0] + 1,
                        previous[1] - top_error - bottom_error,
                        previous[2] + ((ref_index - 1, pred_index - 1, top_error, bottom_error),),
                    ))
            table[ref_index][pred_index] = max(candidates, key=lambda item: (item[0], item[1]))
    path = table[-1][-1][2]
    matches = [IntervalMatch(i, j, float(top_error), float(bottom_error)) for i, j, top_error, bottom_error in path]
    matched_references = {match.reference_index for match in matches}
    matched_predictions = {match.prediction_index for match in matches}
    return (
        matches,
        [index for index in range(len(references)) if index not in matched_references],
        [index for index in range(len(predictions)) if index not in matched_predictions],
    )


def boundary_matched_interval_metrics(
    reference_documents: Sequence[Sequence[Mapping[str, Any]]],
    prediction_documents: Sequence[Sequence[Mapping[str, Any]]],
    tolerance_m: float = 0.05,
) -> dict[str, MetricResult]:
    """Micro interval P/R/F1 and boundary error for the v001 matcher."""
    validate_pairs(reference_documents, prediction_documents)
    matches: list[IntervalMatch] = []
    reference_count = sum(len(intervals) for intervals in reference_documents)
    prediction_count = sum(len(intervals) for intervals in prediction_documents)
    unmatched_reference_count = 0
    unmatched_prediction_count = 0
    for references, predictions in zip(reference_documents, prediction_documents):
        document_matches, unmatched_references, unmatched_predictions = match_intervals_by_boundaries(
            references, predictions, tolerance_m,
        )
        matches.extend(document_matches)
        unmatched_reference_count += len(unmatched_references)
        unmatched_prediction_count += len(unmatched_predictions)
    true_positive = len(matches)
    precision = true_positive / prediction_count if prediction_count else None
    recall = true_positive / reference_count if reference_count else None
    if reference_count == 0 and prediction_count == 0:
        f1 = None
    elif true_positive == 0:
        f1 = 0.0
    else:
        assert precision is not None and recall is not None
        f1 = 2 * precision * recall / (precision + recall)
    top_error_sum = sum(match.top_error_m for match in matches)
    bottom_error_sum = sum(match.bottom_error_m for match in matches)
    details = {
        "matching": "order_preserving_max_cardinality_then_min_error_v001",
        "tolerance_m": tolerance_m,
        "reference_count": reference_count,
        "prediction_count": prediction_count,
        "matched_count": true_positive,
        "unmatched_reference_count": unmatched_reference_count,
        "unmatched_prediction_count": unmatched_prediction_count,
    }
    return {
        "interval_precision": MetricResult("interval_precision", precision, true_positive, prediction_count, "ratio", details),
        "interval_recall": MetricResult("interval_recall", recall, true_positive, reference_count, "ratio", details),
        "interval_f1": MetricResult("interval_f1", f1, 0.0 if f1 is None else f1, 1.0 if f1 is not None else 0.0, "ratio", details),
        "matched_top_boundary_mae_m": MetricResult(
            "matched_top_boundary_mae_m", top_error_sum / true_positive if true_positive else None,
            top_error_sum, true_positive, "m", details,
        ),
        "matched_bottom_boundary_mae_m": MetricResult(
            "matched_bottom_boundary_mae_m", bottom_error_sum / true_positive if true_positive else None,
            bottom_error_sum, true_positive, "m", details,
        ),
    }


def constraint_consistency_summary(
    result_documents: Sequence[Sequence[Any]],
) -> dict[str, MetricResult]:
    """Summarize evaluated checks and violations without rewarding missing data.

    Items may be ConstraintResult objects or their serialized mappings. Overall
    consistency is null when no checks were evaluated. Per-constraint details
    retain coverage so an extractor cannot score well merely by abstaining.
    """
    totals: dict[str, dict[str, int]] = {}
    for document in result_documents:
        for result in document:
            if isinstance(result, Mapping):
                name = str(result["name"])
                evaluated = int(result.get("evaluated_count", 0))
                violations = len(result.get("violations", ()))
            else:
                name = str(result.name)
                evaluated = int(result.evaluated_count)
                violations = len(result.violations)
            counts = totals.setdefault(name, {"evaluated": 0, "violations": 0, "documents_present": 0})
            counts["evaluated"] += evaluated
            counts["violations"] += violations
            counts["documents_present"] += 1
    total_evaluated = sum(counts["evaluated"] for counts in totals.values())
    total_violations = sum(counts["violations"] for counts in totals.values())
    documents = len(result_documents)
    details = {
        "definition": "1 - violation_count / evaluated_check_count",
        "evaluated_check_count": total_evaluated,
        "violation_count": total_violations,
        "document_count": documents,
        "per_constraint": {
            name: {
                **counts,
                "consistency_rate": (
                    1 - counts["violations"] / counts["evaluated"] if counts["evaluated"] else None
                ),
            }
            for name, counts in sorted(totals.items())
        },
    }
    consistency = 1 - total_violations / total_evaluated if total_evaluated else None
    documents_with_any_evaluation = sum(
        any(
            (int(result.get("evaluated_count", 0)) if isinstance(result, Mapping) else int(result.evaluated_count)) > 0
            for result in document
        )
        for document in result_documents
    )
    return {
        "constraint_consistency_rate": MetricResult(
            "constraint_consistency_rate", consistency,
            total_evaluated - total_violations, total_evaluated, "ratio", details,
        ),
        "constraint_document_coverage": MetricResult(
            "constraint_document_coverage",
            documents_with_any_evaluation / documents if documents else None,
            documents_with_any_evaluation, documents, "ratio", details,
        ),
    }
