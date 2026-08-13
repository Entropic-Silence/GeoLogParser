"""Audited field-level ROI re-reading for the local annotation application."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4

from geologparser.datasets.manifest import sha256_file
from geologparser.ocr import OCRAdapter
from geologparser.rereading import (
    AuditedROIReader, decide_reread, decision_to_dict, get_field,
    reread_numeric_roi_audited,
)


NUMERIC_FIELDS = {
    "x_coordinate", "y_coordinate", "collar_elevation_m", "final_depth_m",
    "groundwater_depth_m", "groundwater_elevation_m", "top_depth_m",
    "bottom_depth_m", "thickness_m",
}


def _numeric_field_name(field_path: str) -> str:
    envelope = field_path.rsplit(".", 1)
    if len(envelope) != 2 or envelope[1] not in NUMERIC_FIELDS:
        raise ValueError("field-level OCR re-reading supports numeric MVP fields only")
    return envelope[1]


def resolve_reread_bbox(
    record: Mapping[str, Any], field_path: str, supplied_bbox: Sequence[float] | None,
) -> tuple[float, float, float, float]:
    """Resolve a rendered-pixel bbox without silently mixing coordinate spaces."""
    _numeric_field_name(field_path)
    envelope = get_field(record, field_path)
    if supplied_bbox is not None:
        bbox = supplied_bbox
    elif envelope.get("display_bbox") is not None:
        bbox = envelope["display_bbox"]
    elif record.get("document", {}).get("bbox_coordinate_space") == "pixels":
        bbox = envelope.get("source_bbox")
    else:
        raise ValueError("field lacks a rendered-pixel bbox; supply bbox_pixels explicitly")
    if bbox is None or len(bbox) != 4:
        raise ValueError("bbox_pixels must contain four coordinates")
    try:
        values = tuple(float(value) for value in bbox)
    except (TypeError, ValueError) as exc:
        raise ValueError("bbox_pixels must be numeric") from exc
    if not (values[0] < values[2] and values[1] < values[3]):
        raise ValueError("bbox_pixels must satisfy x1 < x2 and y1 < y2")
    return values


def run_annotation_reread(
    annotation: Mapping[str, Any], field_path: str,
    adapters: Sequence[OCRAdapter | AuditedROIReader],
    run_root: Path, *, bbox_pixels: Sequence[float] | None = None,
    padding_pixels: int = 12, scale: float = 3.0,
) -> dict[str, Any]:
    """Run OCR on one ROI, rank candidates, and persist a non-mutating audit."""
    if not adapters:
        raise ValueError("at least one OCR adapter is required")
    if not 0 <= padding_pixels <= 128:
        raise ValueError("padding_pixels must be within [0, 128]")
    if not 1 <= scale <= 4:
        raise ValueError("scale must be within [1, 4]")
    record = annotation["record"]
    bbox = resolve_reread_bbox(record, field_path, bbox_pixels)
    source_path = Path(annotation["panel"]["rendered_path"]).resolve()
    if not source_path.is_file():
        raise FileNotFoundError("rendered panel image does not exist")
    expected_hash = annotation["panel"].get("rendered_sha256")
    actual_hash = sha256_file(source_path)
    if expected_hash is not None and expected_hash != actual_hash:
        raise ValueError("rendered panel image hash mismatch")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:12]
    run_directory = Path(run_root).resolve() / str(annotation["annotation_id"]) / run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    crop_path = run_directory / "roi.png"
    try:
        crop, candidates, outputs, reader_audits = reread_numeric_roi_audited(
            source_path, bbox, crop_path, adapters,
            padding_pixels=padding_pixels, scale=scale,
        )
        decision = decide_reread(record, field_path, candidates)
        result = {
            "reread_schema_version": "annotation_field_reread_v001",
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "annotation_id": annotation["annotation_id"],
            "annotation_revision": annotation["revision"],
            "field_path": field_path,
            "source_panel_sha256": actual_hash,
            "crop": asdict(crop),
            "crop_sha256": sha256_file(crop_path),
            "parameters": {"padding_pixels": padding_pixels, "scale": scale},
            "adapters": [adapter.name for adapter in adapters],
            "ocr_outputs": {
                name: [asdict(region) for region in regions] for name, regions in outputs.items()
            },
            "reader_audits": reader_audits,
            "decision": decision_to_dict(decision),
            "interpretation": (
                "non-mutating candidate proposal; a human must inspect evidence and explicitly confirm"
            ),
        }
        result_path = run_directory / "result.json"
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result["result_sha256"] = sha256_file(result_path)
        return result
    except Exception:
        # Preserve any crop/evidence already produced, but never leave a
        # partially written result that could be indexed as a completed run.
        raise
