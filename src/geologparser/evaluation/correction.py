"""Safety metrics for constraint-guided correction and human review."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .types import MetricResult, validate_pairs


def _decision_value(decision: Mapping[str, Any], name: str) -> Any:
    return decision.get(name)


def correction_safety_metrics(
    references: Sequence[Any],
    originals: Sequence[Any],
    decisions: Sequence[Mapping[str, Any]],
) -> dict[str, MetricResult]:
    """Evaluate proposals without treating abstention as correction.

    False correction means the original was correct and the automatically
    proposed accepted value is wrong. Incorrect correction includes every
    accepted proposal whose proposed value differs from GT. Both denominators
    are explicit; no automatic corrections yields undefined rates.
    """
    validate_pairs(references, originals)
    if len(decisions) != len(references):
        raise ValueError("decisions must have the same length as references")
    automatic = [
        (reference, original, decision)
        for reference, original, decision in zip(references, originals, decisions)
        if _decision_value(decision, "status") == "ACCEPT_PROPOSAL"
    ]
    incorrect = sum(_decision_value(decision, "accepted_value") != reference for reference, _, decision in automatic)
    false_corrections = sum(
        original == reference and _decision_value(decision, "accepted_value") != reference
        for reference, original, decision in automatic
    )
    improvements = sum(
        original != reference and _decision_value(decision, "accepted_value") == reference
        for reference, original, decision in automatic
    )
    return {
        "false_correction_rate": MetricResult(
            "false_correction_rate",
            false_corrections / len(automatic) if automatic else None,
            false_corrections, len(automatic), "ratio",
        ),
        "incorrect_correction_rate": MetricResult(
            "incorrect_correction_rate",
            incorrect / len(automatic) if automatic else None,
            incorrect, len(automatic), "ratio",
        ),
        "correction_success_rate": MetricResult(
            "correction_success_rate",
            improvements / len(automatic) if automatic else None,
            improvements, len(automatic), "ratio",
        ),
        "automatic_correction_rate": MetricResult(
            "automatic_correction_rate",
            len(automatic) / len(references) if references else None,
            len(automatic), len(references), "ratio",
        ),
    }


def review_detection_metrics(
    needs_review_labels: Sequence[bool], decisions: Sequence[Mapping[str, Any]],
) -> dict[str, MetricResult]:
    """Precision/recall for the explicit NEEDS_REVIEW decision."""
    if len(needs_review_labels) != len(decisions):
        raise ValueError("labels and decisions must have equal length")
    predicted = [_decision_value(decision, "status") == "NEEDS_REVIEW" for decision in decisions]
    true_positive = sum(label and prediction for label, prediction in zip(needs_review_labels, predicted))
    false_positive = sum(not label and prediction for label, prediction in zip(needs_review_labels, predicted))
    false_negative = sum(label and not prediction for label, prediction in zip(needs_review_labels, predicted))
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    return {
        "manual_review_precision": MetricResult(
            "manual_review_precision", true_positive / precision_denominator if precision_denominator else None,
            true_positive, precision_denominator, "ratio",
        ),
        "manual_review_recall": MetricResult(
            "manual_review_recall", true_positive / recall_denominator if recall_denominator else None,
            true_positive, recall_denominator, "ratio",
        ),
        "review_rate": MetricResult(
            "review_rate", sum(predicted) / len(predicted) if predicted else None,
            sum(predicted), len(predicted), "ratio",
        ),
    }
