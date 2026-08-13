"""Factories for schema-compliant, explicitly unknown fields."""

from __future__ import annotations

from typing import Any


def field(
    value: Any = None,
    *,
    source_page: int | None = None,
    source_bbox: list[float] | None = None,
    display_bbox: list[float] | None = None,
    display_bbox_source: str | None = None,
    display_bbox_annotator_id: str | None = None,
    source_text: str | None = None,
    extraction_method: str = "unknown",
    confidence: float | None = None,
    validation_status: str = "not_validated",
    warning_codes: list[str] | None = None,
    raw_unit: str | None = None,
) -> dict[str, Any]:
    result = {
        "value": value,
        "source_page": source_page,
        "source_bbox": source_bbox,
        "display_bbox": display_bbox,
        "display_bbox_source": display_bbox_source,
        "display_bbox_annotator_id": display_bbox_annotator_id,
        "source_text": source_text,
        "extraction_method": extraction_method,
        "confidence": confidence,
        "validation_status": validation_status,
        "warning_codes": warning_codes or [],
    }
    if raw_unit is not None:
        result["raw_unit"] = raw_unit
    return result


BOREHOLE_STRING_FIELDS = ("borehole_id", "project_name", "page_id", "coordinate_system")
BOREHOLE_NUMBER_FIELDS = (
    "x_coordinate", "y_coordinate", "collar_elevation_m", "final_depth_m",
    "groundwater_depth_m", "groundwater_elevation_m",
)
INTERVAL_STRING_FIELDS = (
    "stratum_code_raw", "stratum_code_normalized", "lithology_raw",
    "lithology_normalized", "description_raw", "description_normalized",
    "weathering", "color", "consistency_or_density", "moisture", "structure",
    "inclusions",
)


def empty_borehole_record(document_id: str, source_file: str, document_type: str = "unknown") -> dict[str, Any]:
    borehole = {name: field() for name in BOREHOLE_STRING_FIELDS + BOREHOLE_NUMBER_FIELDS}
    borehole["drilling_date"] = field()
    return {
        "schema_version": "v001",
        "document": {
            "document_id": document_id,
            "source_file": source_file,
            "document_type": document_type,
            "page_count": 1,
            "bbox_coordinate_space": "unknown",
            "source_sha256": None,
            "metadata": {
                "template_id": None, "project_id": None, "source_id": None,
                "quality": "unknown", "contains_stamp": None,
                "contains_handwriting": None, "dpi": None,
            },
        },
        "borehole": borehole,
        "intervals": [],
    }


def empty_interval(interval_id: str) -> dict[str, Any]:
    result = {"interval_id": interval_id}
    for name in ("top_depth_m", "bottom_depth_m", "thickness_m") + INTERVAL_STRING_FIELDS:
        result[name] = field()
    return result
