"""Source-location linkage without promoting external metadata to Ground Truth."""

from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any, Iterable, Mapping

from geologparser.schema import validate_record


SOURCE_COORDINATE_STATUS = "source_provided_unverified"


def _source_field(value: Any, source_text: str, warning_codes: list[str] | None = None) -> dict[str, Any]:
    return {
        "value": value,
        "source_page": None,
        "source_bbox": None,
        "display_bbox": None,
        "source_text": source_text,
        "extraction_method": "unknown",
        "confidence": None,
        "validation_status": "needs_review",
        "warning_codes": sorted(set((warning_codes or []) + ["SOURCE_COORDINATE_UNVERIFIED"])),
    }


def attach_source_location(
    record: Mapping[str, Any], location: Mapping[str, Any],
) -> dict[str, Any]:
    """Copy a record and attach source coordinates with explicit uncertainty.

    The location is contextual source metadata, not page evidence and not GT.
    Existing extracted coordinates are never overwritten silently.
    """
    result = copy.deepcopy(record)
    borehole = result["borehole"]
    warning_codes = list(location.get("warning_codes", []))
    for name, value in (
        ("x_coordinate", location["longitude"]),
        ("y_coordinate", location["latitude"]),
        ("coordinate_system", location["coordinate_system"]),
    ):
        current = borehole[name].get("value")
        if current is not None and current != value:
            raise ValueError(f"record already has conflicting {name}: {current!r} != {value!r}")
        borehole[name] = _source_field(value, str(location["coordinate_source"]), warning_codes)
    metadata = result["document"].setdefault("metadata", {})
    metadata.update({
        "source_location_link_key": location["link_key"],
        "source_location_validation_status": location["coordinate_validation_status"],
        "source_location_warning_codes": warning_codes,
    })
    validate_record(result)
    return result


def group_page_annotations_by_source_record(
    annotations: Iterable[Mapping[str, Any]],
) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for annotation in annotations:
        metadata = annotation["record"]["document"].get("metadata", {})
        source_record_id = metadata.get("source_record_id")
        if not source_record_id:
            raise ValueError(f"annotation {annotation.get('annotation_id')} lacks source_record_id")
        grouped[str(source_record_id)].append(annotation)
    for values in grouped.values():
        values.sort(key=lambda item: int(item["panel"]["source_page"]))
    return dict(grouped)


def merge_verified_page_annotations(
    annotations: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Merge human-verified page records into one borehole document record."""
    pages = list(annotations)
    if not pages:
        raise ValueError("at least one page annotation is required")
    allowed = {"single_verified", "double_verified", "expert_verified"}
    if any(page["annotation_status"] not in allowed for page in pages):
        raise ValueError("all page annotations must be human-verified before merging")
    pages.sort(key=lambda item: int(item["panel"]["source_page"]))
    source_ids = {
        str(page["record"]["document"].get("metadata", {}).get("source_record_id"))
        for page in pages
    }
    if len(source_ids) != 1 or None in source_ids:
        raise ValueError("page annotations must belong to one source record")
    source_id = next(iter(source_ids))
    record = copy.deepcopy(pages[0]["record"])
    record["document"]["document_id"] = f"UNIPD_{source_id}"
    record["document"]["page_count"] = len(pages)
    record["document"]["metadata"].update({
        "merged_from_annotation_ids": [page["annotation_id"] for page in pages],
        "merged_annotation_statuses": [page["annotation_status"] for page in pages],
    })
    # Header values may repeat on every page. Keep the first observed human
    # value and reject disagreement so page order cannot silently decide truth.
    for name in record["borehole"]:
        values = [page["record"]["borehole"][name] for page in pages]
        non_null = [value for value in values if value.get("value") is not None]
        if non_null:
            distinct = {repr(value["value"]) for value in non_null}
            if len(distinct) > 1:
                raise ValueError(f"conflicting human page values for borehole.{name}")
            record["borehole"][name] = copy.deepcopy(non_null[0])
    intervals = []
    for page in pages:
        for interval in page["record"].get("intervals", []):
            merged = copy.deepcopy(interval)
            merged["interval_id"] = f"I{len(intervals) + 1:03d}"
            intervals.append(merged)
    record["intervals"] = intervals
    validate_record(record)
    return record
