"""Conservative, auditable fusion of two schema-compliant extraction records."""

from __future__ import annotations

import copy
from typing import Any, Mapping

from geologparser.schema import validate_record


def _present(envelope: Mapping[str, Any]) -> bool:
    return envelope.get("value") is not None


def _fuse_envelope(
    grounded: Mapping[str, Any], visual: Mapping[str, Any], field_path: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Prefer grounded evidence while surfacing every disagreement for review."""
    left = copy.deepcopy(dict(grounded))
    right = copy.deepcopy(dict(visual))
    left_present, right_present = _present(left), _present(right)
    if not left_present and not right_present:
        return left, {"field_path": field_path, "decision": "both_abstained"}
    if left_present and not right_present:
        left["extraction_method"] = "fusion"
        return left, {"field_path": field_path, "decision": "grounded_only", "value": left["value"]}
    if right_present and not left_present:
        right["extraction_method"] = "fusion"
        right["warning_codes"] = sorted(set(right.get("warning_codes", [])) | {"FUSION_SINGLE_VISUAL_SOURCE"})
        right["validation_status"] = "needs_review"
        return right, {"field_path": field_path, "decision": "visual_only_needs_review", "value": right["value"]}
    if str(left["value"]).strip() == str(right["value"]).strip():
        left["extraction_method"] = "fusion"
        confidences = [value for value in (left.get("confidence"), right.get("confidence")) if value is not None]
        left["confidence"] = sum(confidences) / len(confidences) if confidences else None
        return left, {
            "field_path": field_path, "decision": "agreement_keep_grounded_provenance",
            "value": left["value"],
        }
    left["extraction_method"] = "fusion"
    left["warning_codes"] = sorted(set(left.get("warning_codes", [])) | {"FUSION_DISAGREEMENT"})
    left["validation_status"] = "needs_review"
    return left, {
        "field_path": field_path, "decision": "disagreement_keep_grounded_needs_review",
        "grounded_value": left["value"], "visual_value": right["value"],
    }


def fuse_records(
    grounded_record: Mapping[str, Any], visual_record: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fuse direct/OCR evidence with VLM evidence without silent correction.

    Interval alignment is deliberately positional only when counts agree. If
    counts differ, grounded intervals are retained and visual-only intervals
    are appended as review items; the decision log exposes the mismatch.
    """
    validate_record(grounded_record)
    validate_record(visual_record)
    fused = copy.deepcopy(dict(grounded_record))
    decisions: list[dict[str, Any]] = []
    for name in fused["borehole"]:
        fused["borehole"][name], decision = _fuse_envelope(
            grounded_record["borehole"][name], visual_record["borehole"][name], f"borehole.{name}",
        )
        decisions.append(decision)

    grounded_intervals = grounded_record["intervals"]
    visual_intervals = visual_record["intervals"]
    if len(grounded_intervals) == len(visual_intervals):
        fused["intervals"] = copy.deepcopy(grounded_intervals)
        for index, (grounded, visual) in enumerate(zip(grounded_intervals, visual_intervals)):
            for name in grounded:
                if name == "interval_id":
                    continue
                fused["intervals"][index][name], decision = _fuse_envelope(
                    grounded[name], visual[name], f"intervals.{index}.{name}",
                )
                decisions.append(decision)
    elif not grounded_intervals:
        fused["intervals"] = copy.deepcopy(visual_intervals)
        for index, interval in enumerate(fused["intervals"]):
            for name, envelope in interval.items():
                if name == "interval_id":
                    continue
                if _present(envelope):
                    envelope["extraction_method"] = "fusion"
                    envelope["validation_status"] = "needs_review"
                    envelope["warning_codes"] = sorted(
                        set(envelope.get("warning_codes", [])) | {"FUSION_UNALIGNED_VISUAL_INTERVAL"}
                    )
        decisions.append({
            "field_path": "intervals", "decision": "visual_intervals_unaligned_needs_review",
            "grounded_count": 0, "visual_count": len(visual_intervals),
        })
    else:
        decisions.append({
            "field_path": "intervals", "decision": "count_mismatch_keep_grounded_needs_review",
            "grounded_count": len(grounded_intervals), "visual_count": len(visual_intervals),
        })
        for interval in fused["intervals"]:
            for name, envelope in interval.items():
                if name != "interval_id" and _present(envelope):
                    envelope["validation_status"] = "needs_review"
                    envelope["warning_codes"] = sorted(
                        set(envelope.get("warning_codes", [])) | {"FUSION_INTERVAL_COUNT_MISMATCH"}
                    )
    fused["document"]["metadata"]["fusion_version"] = "conservative_field_fusion_v001"
    validate_record(fused)
    return fused, decisions
