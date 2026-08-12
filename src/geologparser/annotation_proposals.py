"""Build immutable review proposals from already frozen experiment outputs."""

from __future__ import annotations

import copy
from typing import Any, Mapping

from geologparser.annotation import create_annotation, pdf_bbox_to_rendered_pixels
from geologparser.schema import validate_record


def proposal_from_prediction(
    prediction: Mapping[str, Any],
    panel: Mapping[str, Any],
    experiment_id: str,
) -> dict[str, Any]:
    if prediction["item_id"] != panel["panel_id"]:
        raise ValueError("prediction item_id and panel_id differ")
    record = copy.deepcopy(prediction["record"])
    if record["document"]["document_id"] != panel["panel_id"]:
        raise ValueError("prediction document_id and panel_id differ")
    for envelope in list(record["borehole"].values()) + [
        value for interval in record.get("intervals", []) for name, value in interval.items()
        if name != "interval_id"
    ]:
        if envelope.get("source_bbox") is not None and envelope.get("display_bbox") is None:
            envelope["display_bbox"] = pdf_bbox_to_rendered_pixels(envelope["source_bbox"], panel)
    record["document"]["metadata"].update({
        "annotation_proposal_experiment_id": experiment_id,
        "annotation_proposal_status": "auto_needs_human_verification",
    })
    validate_record(record)
    return create_annotation(
        annotation_id=panel["panel_id"], panel=panel, record=record,
        annotator_id=f"AUTO_EXPERIMENT:{experiment_id}", status="auto",
    )
