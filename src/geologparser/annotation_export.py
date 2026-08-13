"""Human-verification gates and agreement summaries for annotation exports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from geologparser.annotation import matching_attestations, validate_annotation


HUMAN_STATUSES = {"single_verified", "double_verified", "expert_verified"}
MVP_BOREHOLE_FIELDS = (
    "borehole_id", "collar_elevation_m", "final_depth_m", "groundwater_depth_m",
)
MVP_INTERVAL_FIELDS = (
    "top_depth_m", "bottom_depth_m", "thickness_m", "lithology_raw", "description_raw",
)


def ground_truth_gate(
    annotation: Mapping[str, Any], *, require_intervals: bool = True,
) -> list[str]:
    """Return explicit reasons a human-status annotation is not exportable GT."""
    failures = []
    if annotation.get("annotation_status") not in HUMAN_STATUSES:
        failures.append("ANNOTATION_NOT_HUMAN_VERIFIED")
    else:
        attestations = matching_attestations(annotation)
        annotator_ids = {item["annotator_id"] for item in attestations}
        if not attestations:
            failures.append("MISSING_VALID_VERIFICATION_ATTESTATION")
        if annotation.get("annotation_status") == "double_verified" and len(annotator_ids) < 2:
            failures.append("INSUFFICIENT_INDEPENDENT_ATTESTATIONS")
        if annotation.get("annotation_status") == "expert_verified" and not any(
            item.get("role") == "expert" for item in attestations
        ):
            failures.append("MISSING_EXPERT_ATTESTATION")
    record = annotation.get("record", {})
    intervals = record.get("intervals", [])
    if require_intervals and not intervals:
        failures.append("NO_INTERVALS")
    # A missing document-level value is legitimate only after a reviewer has
    # explicitly confirmed absence.  Otherwise an unreviewed model abstention
    # would silently become a Ground Truth null.
    for name in MVP_BOREHOLE_FIELDS:
        envelope = record.get("borehole", {}).get(name, {})
        if envelope.get("validation_status") != "human_verified":
            failures.append(f"FIELD_NOT_HUMAN_VERIFIED:borehole.{name}")
        if envelope.get("extraction_method") != "human":
            failures.append(f"FIELD_NOT_HUMAN_AUTHORED:borehole.{name}")
        if envelope.get("source_page") is None:
            failures.append(f"MISSING_SOURCE_PAGE:borehole.{name}")
    for index, interval in enumerate(intervals):
        for name in MVP_INTERVAL_FIELDS:
            envelope = interval.get(name, {})
            # Null is a valid GT value when the source does not report a field;
            # the human-authored/verified flags distinguish confirmed absence
            # from an unreviewed model abstention.
            if envelope.get("validation_status") != "human_verified":
                failures.append(f"FIELD_NOT_HUMAN_VERIFIED:intervals[{index}].{name}")
            if envelope.get("extraction_method") != "human":
                failures.append(f"FIELD_NOT_HUMAN_AUTHORED:intervals[{index}].{name}")
            if envelope.get("source_page") is None:
                failures.append(f"MISSING_SOURCE_PAGE:intervals[{index}].{name}")
    return failures


def export_verified_annotations(
    annotation_root: Path, destination: Path, *, require_intervals: bool = True,
) -> dict[str, Any]:
    """Write JSONL only when every source annotation is human-verified."""
    paths = sorted(annotation_root.glob("*.json"))
    if not paths:
        raise ValueError("annotation root contains no annotations")
    annotations = []
    for path in paths:
        annotation = json.loads(path.read_text(encoding="utf-8"))
        validate_annotation(annotation)
        failures = ground_truth_gate(annotation, require_intervals=require_intervals)
        if failures:
            raise ValueError(
                f"annotation {annotation['annotation_id']} failed Ground Truth gate: "
                + ", ".join(failures)
            )
        annotations.append(annotation)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(annotation, ensure_ascii=False, sort_keys=True) + "\n" for annotation in annotations),
        encoding="utf-8",
    )
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    current_attestations = [
        attestation
        for annotation in annotations
        for attestation in matching_attestations(annotation)
    ]
    return {
        "annotation_count": len(annotations),
        "status_counts": {
            status: sum(annotation["annotation_status"] == status for annotation in annotations)
            for status in sorted(HUMAN_STATUSES)
        },
        "annotator_ids": sorted({
            str(attestation["annotator_id"]) for attestation in current_attestations
        }),
        "valid_attestation_count": len(current_attestations),
        "expert_attestation_count": sum(
            attestation["role"] == "expert" for attestation in current_attestations
        ),
        "output_path": str(destination), "sha256": digest,
    }


def annotation_agreement(
    first: Sequence[Mapping[str, Any]], second: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare two independently supplied annotation collections by ID.

    Reports exact header agreement and boundary numeric agreement. It does not
    infer that matching annotator IDs constitute independent annotation.
    """
    # Local import prevents the GT gate from depending on the evaluation
    # package initializer, which itself exposes the benchmark evaluator.
    from geologparser.evaluation.metrics import exact_match, numeric_with_missing_mae

    left = {str(item["annotation_id"]): item for item in first}
    right = {str(item["annotation_id"]): item for item in second}
    if len(left) != len(first) or len(right) != len(second):
        raise ValueError("annotation collections contain duplicate annotation IDs")
    if set(left) != set(right):
        raise ValueError("annotation ID sets differ")
    left_annotators = {str(item["annotator_id"]) for item in first}
    right_annotators = {str(item["annotator_id"]) for item in second}
    overlap = left_annotators & right_annotators
    if overlap:
        raise ValueError(
            "agreement collections must use disjoint annotator IDs; overlap: "
            + ", ".join(sorted(overlap))
        )
    ids = sorted(left)
    borehole_fields = ("borehole_id", "project_name", "coordinate_system")
    categorical: dict[str, Any] = {}
    for name in borehole_fields:
        references = [left[item]["record"]["borehole"][name]["value"] for item in ids]
        predictions = [right[item]["record"]["borehole"][name]["value"] for item in ids]
        categorical[name] = exact_match(references, predictions, f"{name}_agreement").to_dict()
    boundary_left, boundary_right = [], []
    unmatched_interval_documents = 0
    for item in ids:
        left_intervals = left[item]["record"]["intervals"]
        right_intervals = right[item]["record"]["intervals"]
        if len(left_intervals) != len(right_intervals):
            unmatched_interval_documents += 1
            continue
        for first_interval, second_interval in zip(left_intervals, right_intervals):
            for name in ("top_depth_m", "bottom_depth_m", "thickness_m"):
                boundary_left.append(first_interval[name]["value"])
                boundary_right.append(second_interval[name]["value"])
    numeric = numeric_with_missing_mae(boundary_left, boundary_right, "boundary_agreement_mae_m")
    return {
        "document_count": len(ids), "categorical": categorical,
        "independent_annotator_ids": {
            "first": sorted(left_annotators), "second": sorted(right_annotators),
            "disjoint": True,
        },
        "boundary": {name: metric.to_dict() for name, metric in numeric.items()},
        "documents_excluded_for_interval_count_mismatch": unmatched_interval_documents,
    }
