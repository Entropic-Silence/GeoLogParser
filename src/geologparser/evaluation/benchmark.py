"""Dataset-level evaluation over frozen, human-gated annotations."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from geologparser.annotation_export import ground_truth_gate
from geologparser.schema import validate_record

from .errors import classify_field_error, error_distribution
from .metrics import (
    boundary_accuracy, boundary_matched_interval_metrics, character_error_rate,
    critical_numerical_error_rate, exact_match, match_intervals_by_boundaries,
    normalized_edit_similarity, numeric_character_error_rate, numeric_with_missing_mae,
)


CATEGORICAL_BOREHOLE_FIELDS = ("borehole_id", "project_name", "coordinate_system")
NUMERIC_BOREHOLE_FIELDS = (
    "x_coordinate", "y_coordinate", "collar_elevation_m", "final_depth_m",
    "groundwater_depth_m", "groundwater_elevation_m",
)
BOUNDARY_FIELDS = ("top_depth_m", "bottom_depth_m", "thickness_m")


def _value(envelope: Any) -> Any:
    return envelope.get("value") if isinstance(envelope, Mapping) else envelope


def _prediction_record(row: Mapping[str, Any]) -> Mapping[str, Any]:
    if "record" in row:
        return row["record"]
    return row


def evaluate_benchmark(
    references: Sequence[Mapping[str, Any]],
    prediction_rows: Sequence[Mapping[str, Any]],
    *,
    interval_match_tolerance_m: float = 0.05,
    boundary_tolerances_m: Sequence[float] = (0.01, 0.05, 0.10),
    critical_error_thresholds: Mapping[str, float] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return metrics and traceable errors; reject non-GT references."""
    if interval_match_tolerance_m < 0 or any(value < 0 for value in boundary_tolerances_m):
        raise ValueError("tolerances must be non-negative")
    reference_by_id: dict[str, Mapping[str, Any]] = {}
    for annotation in references:
        failures = ground_truth_gate(annotation)
        if failures:
            raise ValueError(
                f"reference {annotation.get('annotation_id')} failed Ground Truth gate: "
                + ", ".join(failures)
            )
        annotation_id = str(annotation["annotation_id"])
        if annotation_id in reference_by_id:
            raise ValueError(f"duplicate reference ID: {annotation_id}")
        validate_record(annotation["record"])
        reference_by_id[annotation_id] = annotation
    prediction_by_id: dict[str, Mapping[str, Any]] = {}
    for row in prediction_rows:
        item_id = str(row.get("item_id") or row.get("annotation_id") or "")
        if not item_id:
            record = _prediction_record(row)
            item_id = str(record.get("document", {}).get("document_id") or "")
        if not item_id:
            raise ValueError("prediction row lacks item/document ID")
        if item_id in prediction_by_id:
            raise ValueError(f"duplicate prediction ID: {item_id}")
        record = _prediction_record(row)
        validate_record(record)
        prediction_by_id[item_id] = record
    if set(reference_by_id) != set(prediction_by_id):
        missing = sorted(set(reference_by_id) - set(prediction_by_id))
        extra = sorted(set(prediction_by_id) - set(reference_by_id))
        raise ValueError(f"reference/prediction ID sets differ; missing={missing}, extra={extra}")

    ids = sorted(reference_by_id)
    reference_records = [reference_by_id[item]["record"] for item in ids]
    prediction_records = [prediction_by_id[item] for item in ids]
    metrics: dict[str, Any] = {
        "scope": "human-GT benchmark evaluation",
        "document_count": len(ids),
        "interval_matching": {
            "strategy": "order_preserving_max_cardinality_then_min_error_v001",
            "tolerance_m": interval_match_tolerance_m,
        },
        "borehole_fields": {}, "intervals": {}, "text": {},
    }
    errors: list[dict[str, Any]] = []
    for name in CATEGORICAL_BOREHOLE_FIELDS:
        refs = [_value(record["borehole"][name]) for record in reference_records]
        preds = [_value(record["borehole"][name]) for record in prediction_records]
        metrics["borehole_fields"][name] = exact_match(refs, preds, f"{name}_exact_match").to_dict()
        for item_id, reference, prediction in zip(ids, refs, preds):
            error_type = classify_field_error(name, reference, prediction)
            if error_type:
                errors.append({
                    "item_id": item_id, "field_path": f"borehole.{name}",
                    "reference": reference, "prediction": prediction, "error_type": error_type,
                })
    for name in NUMERIC_BOREHOLE_FIELDS:
        refs = [_value(record["borehole"][name]) for record in reference_records]
        preds = [_value(record["borehole"][name]) for record in prediction_records]
        field_metrics = numeric_with_missing_mae(refs, preds, f"{name}_mae")
        metrics["borehole_fields"][name] = {
            metric_name: metric.to_dict() for metric_name, metric in field_metrics.items()
        }
        if critical_error_thresholds and name in critical_error_thresholds:
            metrics["borehole_fields"][name]["critical_numerical_error_rate"] = (
                critical_numerical_error_rate(
                    refs, preds, threshold=critical_error_thresholds[name],
                    name=f"{name}_critical_numerical_error_rate",
                ).to_dict()
            )
        for item_id, reference, prediction in zip(ids, refs, preds):
            error_type = classify_field_error(name, reference, prediction)
            if error_type:
                errors.append({
                    "item_id": item_id, "field_path": f"borehole.{name}",
                    "reference": reference, "prediction": prediction, "error_type": error_type,
                })

    reference_intervals = [record["intervals"] for record in reference_records]
    prediction_intervals = [record["intervals"] for record in prediction_records]
    metrics["intervals"].update({
        name: value.to_dict() for name, value in boundary_matched_interval_metrics(
            reference_intervals, prediction_intervals, interval_match_tolerance_m,
        ).items()
    })
    matched_values = {name: ([], []) for name in BOUNDARY_FIELDS}
    lithology_references: list[Any] = []
    lithology_predictions: list[Any] = []
    description_references: list[str] = []
    description_predictions: list[str] = []
    for item_id, refs, preds in zip(ids, reference_intervals, prediction_intervals):
        matches, unmatched_refs, unmatched_preds = match_intervals_by_boundaries(
            refs, preds, interval_match_tolerance_m,
        )
        for index in unmatched_refs:
            errors.append({
                "item_id": item_id, "field_path": f"intervals[{index}]",
                "reference": refs[index]["interval_id"], "prediction": None,
                "error_type": "missing_interval",
            })
        for index in unmatched_preds:
            errors.append({
                "item_id": item_id, "field_path": f"prediction_intervals[{index}]",
                "reference": None, "prediction": preds[index]["interval_id"],
                "error_type": "hallucination",
            })
        for match in matches:
            reference = refs[match.reference_index]
            prediction = preds[match.prediction_index]
            for name in BOUNDARY_FIELDS:
                ref_value, pred_value = _value(reference[name]), _value(prediction[name])
                matched_values[name][0].append(ref_value)
                matched_values[name][1].append(pred_value)
                error_type = classify_field_error(name, ref_value, pred_value)
                if error_type:
                    errors.append({
                        "item_id": item_id,
                        "field_path": f"intervals[{match.reference_index}].{name}",
                        "prediction_field_path": f"intervals[{match.prediction_index}].{name}",
                        "reference": ref_value, "prediction": pred_value, "error_type": error_type,
                    })
            ref_lithology = _value(reference["lithology_raw"])
            pred_lithology = _value(prediction["lithology_raw"])
            lithology_references.append(ref_lithology)
            lithology_predictions.append(pred_lithology)
            error_type = classify_field_error("lithology_raw", ref_lithology, pred_lithology)
            if error_type:
                errors.append({
                    "item_id": item_id,
                    "field_path": f"intervals[{match.reference_index}].lithology_raw",
                    "prediction_field_path": f"intervals[{match.prediction_index}].lithology_raw",
                    "reference": ref_lithology, "prediction": pred_lithology,
                    "error_type": error_type,
                })
            reference_description = _value(reference["description_raw"])
            if reference_description is not None:
                description_references.append(str(reference_description))
                description_predictions.append(str(_value(prediction["description_raw"]) or ""))
    for name, (refs, preds) in matched_values.items():
        values = numeric_with_missing_mae(refs, preds, f"matched_{name}_mae")
        metrics["intervals"][name] = {key: value.to_dict() for key, value in values.items()}
        metrics["intervals"][name]["boundary_accuracy"] = {
            f"at_{tolerance:g}m": boundary_accuracy(refs, preds, tolerance).to_dict()
            for tolerance in boundary_tolerances_m
        }
    metrics["intervals"]["lithology_raw_exact_match"] = exact_match(
        lithology_references, lithology_predictions, "lithology_raw_exact_match",
    ).to_dict()
    metrics["text"]["description_cer"] = character_error_rate(
        description_references, description_predictions,
    ).to_dict()
    metrics["text"]["description_numeric_cer"] = numeric_character_error_rate(
        description_references, description_predictions,
    ).to_dict()
    metrics["text"]["description_normalized_edit_similarity"] = normalized_edit_similarity(
        description_references, description_predictions,
        name="description_normalized_edit_similarity",
    ).to_dict()
    metrics["error_distribution"] = error_distribution(errors)
    return metrics, errors
