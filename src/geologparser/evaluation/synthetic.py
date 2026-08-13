"""Controlled evaluation for programmatically generated known labels."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .metrics import exact_match, numeric_with_missing_mae, boundary_matched_interval_metrics


def _value(record: Mapping[str, Any], name: str) -> Any:
    return record["borehole"][name]["value"]


def evaluate_synthetic_controlled(
    references: Sequence[Mapping[str, Any]], predictions: Sequence[Mapping[str, Any]],
    *, interval_tolerance_m: float = 0.05,
) -> dict[str, Any]:
    """Evaluate known synthetic labels without invoking the human-GT gate."""
    if len(references) != len(predictions):
        raise ValueError("synthetic reference/prediction lengths differ")
    reference_ids = [record["document"]["document_id"] for record in references]
    prediction_ids = [record["document"]["document_id"] for record in predictions]
    if reference_ids != prediction_ids:
        raise ValueError("synthetic reference/prediction ID order differs")
    ids = [_value(record, "borehole_id") for record in references]
    predicted_ids = [_value(record, "borehole_id") for record in predictions]
    final_depth = numeric_with_missing_mae(
        [_value(record, "final_depth_m") for record in references],
        [_value(record, "final_depth_m") for record in predictions],
        "final_depth_m_mae",
    )
    interval_metrics = boundary_matched_interval_metrics(
        [record["intervals"] for record in references],
        [record["intervals"] for record in predictions], interval_tolerance_m,
    )
    return {
        "scope": "synthetic controlled evaluation; not real or human-GT benchmark evidence",
        "ground_truth_tier": "SYNTHETIC",
        "document_count": len(references),
        "borehole_id_exact_match": exact_match(ids, predicted_ids, "borehole_id_exact_match").to_dict(),
        "final_depth": {name: value.to_dict() for name, value in final_depth.items()},
        "intervals": {name: value.to_dict() for name, value in interval_metrics.items()},
        "formal_benchmark_eligible": False,
    }
