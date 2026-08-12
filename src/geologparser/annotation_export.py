"""Human-verification gates and agreement summaries for annotation exports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from geologparser.annotation import validate_annotation
from geologparser.evaluation import exact_match, numeric_with_missing_mae


HUMAN_STATUSES = {"single_verified", "double_verified", "expert_verified"}


def export_verified_annotations(annotation_root: Path, destination: Path) -> dict[str, Any]:
    """Write JSONL only when every source annotation is human-verified."""
    paths = sorted(annotation_root.glob("*.json"))
    if not paths:
        raise ValueError("annotation root contains no annotations")
    annotations = []
    for path in paths:
        annotation = json.loads(path.read_text(encoding="utf-8"))
        validate_annotation(annotation)
        if annotation["annotation_status"] not in HUMAN_STATUSES:
            raise ValueError(f"annotation {annotation['annotation_id']} is not human-verified")
        annotations.append(annotation)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(annotation, ensure_ascii=False, sort_keys=True) + "\n" for annotation in annotations),
        encoding="utf-8",
    )
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {
        "annotation_count": len(annotations),
        "status_counts": {
            status: sum(annotation["annotation_status"] == status for annotation in annotations)
            for status in sorted(HUMAN_STATUSES)
        },
        "annotator_ids": sorted({str(annotation["annotator_id"]) for annotation in annotations}),
        "output_path": str(destination), "sha256": digest,
    }


def annotation_agreement(
    first: Sequence[Mapping[str, Any]], second: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare two independently supplied annotation collections by ID.

    Reports exact header agreement and boundary numeric agreement. It does not
    infer that matching annotator IDs constitute independent annotation.
    """
    left = {str(item["annotation_id"]): item for item in first}
    right = {str(item["annotation_id"]): item for item in second}
    if set(left) != set(right):
        raise ValueError("annotation ID sets differ")
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
        "boundary": {name: metric.to_dict() for name, metric in numeric.items()},
        "documents_excluded_for_interval_count_mismatch": unmatched_interval_documents,
    }
