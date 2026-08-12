"""Conservative conversion of VLM JSON into GeoLogParser schema v001."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from geologparser.io.records import empty_borehole_record, empty_interval, field


BOREHOLE_FIELDS = {
    "borehole_id": "string",
    "project_name": "string",
    "page_id": "string",
    "x_coordinate": "number",
    "y_coordinate": "number",
    "coordinate_system": "string",
    "collar_elevation_m": "number",
    "final_depth_m": "number",
    "groundwater_depth_m": "number",
    "groundwater_elevation_m": "number",
    "drilling_date": "string",
}
INTERVAL_FIELDS = {
    "top_depth_m": "number",
    "bottom_depth_m": "number",
    "thickness_m": "number",
    "stratum_code_raw": "string",
    "lithology_raw": "string",
    "description_raw": "string",
}


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a single object, accepting a fenced response but no Python literals."""
    candidate = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        candidate = fence.group(1).strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        start = candidate.find("{")
        if start < 0:
            raise ValueError("VLM response contains no JSON object") from None
        try:
            value, end = decoder.raw_decode(candidate[start:])
        except json.JSONDecodeError as exc:
            raise ValueError(f"VLM response is not valid JSON: {exc.msg}") from exc
        if candidate[start + end :].strip() and not candidate[start + end :].strip().startswith("```"):
            raise ValueError("VLM response contains non-JSON trailing content")
    if not isinstance(value, dict):
        raise ValueError("VLM response root must be a JSON object")
    return value


def _coerce(value: Any, expected_type: str) -> Any:
    if value is None:
        return None
    if expected_type == "string":
        return value.strip() if isinstance(value, str) and value.strip() else None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", value.strip()):
        return float(value.strip())
    return None


def _source_text(value: Any) -> str | None:
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


def compact_payload_to_record(
    payload: Mapping[str, Any],
    *,
    document_id: str,
    source_file: Path,
    source_sha256: str | None = None,
) -> dict[str, Any]:
    """Normalize only declared fields; absent/invalid values remain unknown.

    The VLM is not asked to invent provenance boxes. Whole-image VLM evidence
    therefore has a null bbox and stays ``needs_review`` until grounded or
    human verified.
    """
    record = empty_borehole_record(document_id, str(source_file), "image")
    record["document"]["source_sha256"] = source_sha256
    borehole = payload.get("borehole", {})
    if not isinstance(borehole, Mapping):
        borehole = {}
    for name, expected_type in BOREHOLE_FIELDS.items():
        raw = borehole.get(name)
        value = _coerce(raw, expected_type)
        record["borehole"][name] = field(
            value,
            source_page=1,
            source_text=_source_text(raw),
            extraction_method="vlm",
            confidence=None,
            validation_status="needs_review" if value is not None else "not_validated",
            warning_codes=["VLM_UNGROUNDED"] if value is not None else [],
            raw_unit="m" if name.endswith("_m") and value is not None else None,
        )
    intervals = payload.get("intervals", [])
    if not isinstance(intervals, list):
        intervals = []
    for index, candidate in enumerate(intervals, 1):
        if not isinstance(candidate, Mapping):
            continue
        interval = empty_interval(str(candidate.get("interval_id") or f"I{index:03d}"))
        has_value = False
        for name, expected_type in INTERVAL_FIELDS.items():
            raw = candidate.get(name)
            value = _coerce(raw, expected_type)
            has_value = has_value or value is not None
            interval[name] = field(
                value,
                source_page=1,
                source_text=_source_text(raw),
                extraction_method="vlm",
                confidence=None,
                validation_status="needs_review" if value is not None else "not_validated",
                warning_codes=["VLM_UNGROUNDED"] if value is not None else [],
                raw_unit="m" if name.endswith("_m") and value is not None else None,
            )
        if has_value:
            record["intervals"].append(interval)
    return record

