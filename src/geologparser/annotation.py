"""Panel rendering and revisioned annotation records."""

from __future__ import annotations

import copy
import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from geologparser.datasets.manifest import sha256_file
from geologparser.io.records import empty_interval
from geologparser.schema import validate_record
from geologparser.rereading import get_field


ANNOTATION_STATUSES = {"auto", "single_verified", "double_verified", "expert_verified"}


def validate_annotator_id(annotator_id: Any) -> str:
    """Return a stripped, non-empty human or system actor identifier."""
    if not isinstance(annotator_id, str) or not annotator_id.strip():
        raise ValueError("annotator_id must be a non-empty string")
    return annotator_id.strip()


def validate_display_bbox(
    bbox: Any, panel: Mapping[str, Any], *, require_dimensions: bool = True,
) -> list[float]:
    """Validate a rendered-image pixel bbox without clamping or guessing."""
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError("display bbox must contain four coordinates")
    try:
        values = [float(value) for value in bbox]
    except (TypeError, ValueError) as exc:
        raise ValueError("display bbox must be numeric") from exc
    if not all(math.isfinite(value) for value in values):
        raise ValueError("display bbox must contain finite coordinates")
    x1, y1, x2, y2 = values
    if not (0 <= x1 < x2 and 0 <= y1 < y2):
        raise ValueError("display bbox must satisfy 0 <= x1 < x2 and 0 <= y1 < y2")
    width, height = panel.get("rendered_width_px"), panel.get("rendered_height_px")
    if width is None or height is None:
        rendered_path = panel.get("rendered_path")
        if rendered_path:
            try:
                from PIL import Image
                with Image.open(rendered_path) as image:
                    width, height = image.size
            except (FileNotFoundError, OSError):
                pass
    if width is None or height is None:
        if require_dimensions:
            raise ValueError("panel lacks rendered image dimensions")
    elif x2 > float(width) or y2 > float(height):
        raise ValueError("display bbox exceeds rendered image bounds")
    return values


def bind_human_display_bbox(
    record: Mapping[str, Any], field_path: str, bbox: Any,
    panel: Mapping[str, Any], annotator_id: str,
) -> dict[str, Any]:
    """Return a record with human-drawn display evidence; field truth is unchanged."""
    annotator_id = validate_annotator_id(annotator_id)
    values = validate_display_bbox(bbox, panel)
    revised = copy.deepcopy(record)
    envelope = get_field(revised, field_path)
    envelope["display_bbox"] = values
    envelope["display_bbox_source"] = "human_drawn"
    envelope["display_bbox_annotator_id"] = annotator_id
    if envelope.get("source_page") is None:
        envelope["source_page"] = panel.get("source_page")
    validate_record(revised)
    return revised


def validate_display_bbox_edits(
    previous: Mapping[str, Any], revised: Mapping[str, Any],
    panel: Mapping[str, Any], annotator_id: str,
) -> None:
    """Require changed display evidence to be bounded and human-attributed."""
    annotator_id = validate_annotator_id(annotator_id)
    previous_envelopes = _field_envelopes(previous)
    for path, envelope in _field_envelopes(revised).items():
        prior = previous_envelopes.get(path, {})
        signature = (
            envelope.get("display_bbox"), envelope.get("display_bbox_source"),
            envelope.get("display_bbox_annotator_id"),
        )
        prior_signature = (
            prior.get("display_bbox"), prior.get("display_bbox_source"),
            prior.get("display_bbox_annotator_id"),
        )
        if signature == prior_signature:
            continue
        if envelope.get("display_bbox") is None:
            if envelope.get("display_bbox_source") is not None or envelope.get("display_bbox_annotator_id") is not None:
                raise ValueError(f"{path}: cleared display bbox must clear its provenance")
            continue
        validate_display_bbox(envelope["display_bbox"], panel)
        if envelope.get("display_bbox_source") != "human_drawn":
            raise ValueError(f"{path}: changed display bbox must be human_drawn")
        if envelope.get("display_bbox_annotator_id") != annotator_id:
            raise ValueError(f"{path}: display bbox annotator does not match save annotator")


def _field_envelopes(record: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result = {
        f"borehole.{name}": envelope
        for name, envelope in record.get("borehole", {}).items()
        if isinstance(envelope, Mapping)
    }
    for index, interval in enumerate(record.get("intervals", ())):
        result.update({
            f"intervals[{index}].{name}": envelope
            for name, envelope in interval.items()
            if name != "interval_id" and isinstance(envelope, Mapping)
        })
    return result


def human_empty_interval(interval_id: str, source_page: int) -> dict[str, Any]:
    """Create an editable interval without inventing any geological value."""
    if not interval_id:
        raise ValueError("interval_id must not be empty")
    if source_page < 1:
        raise ValueError("source_page must be one-based")
    interval = empty_interval(interval_id)
    for name, envelope in interval.items():
        if name == "interval_id":
            continue
        envelope.update({
            "source_page": source_page,
            "extraction_method": "human",
            "confidence": None,
            "validation_status": "not_validated",
        })
    return interval


@dataclass(frozen=True)
class PanelSpec:
    panel_id: str
    source_path: str
    source_page: int
    normalized_bbox: tuple[float, float, float, float]
    borehole_hint: str | None = None
    project_id: str | None = None
    template_id: str | None = None
    redistribution_status: str = "unknown"

    def validate(self) -> None:
        x1, y1, x2, y2 = self.normalized_bbox
        if self.source_page < 1:
            raise ValueError("source_page must be one-based")
        if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
            raise ValueError("normalized_bbox must satisfy 0 <= x1 < x2 <= 1")


def render_panel(spec: PanelSpec, output_path: Path, dpi: int = 150) -> dict[str, Any]:
    """Render a normalized visual-page crop and return trace metadata."""
    spec.validate()
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("panel rendering requires PyMuPDF") from exc
    source = Path(spec.source_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(source) as document:
        if spec.source_page > len(document):
            raise ValueError(f"source page {spec.source_page} exceeds document page count {len(document)}")
        page = document[spec.source_page - 1]
        visual_rect = page.rect
        x1, y1, x2, y2 = spec.normalized_bbox
        clip = pymupdf.Rect(
            visual_rect.x0 + visual_rect.width * x1,
            visual_rect.y0 + visual_rect.height * y1,
            visual_rect.x0 + visual_rect.width * x2,
            visual_rect.y0 + visual_rect.height * y2,
        )
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(dpi / 72, dpi / 72), clip=clip, alpha=False)
        pixmap.save(output_path)
        rotation_degrees = page.rotation
        rotation_matrix = [
            page.rotation_matrix.a, page.rotation_matrix.b, page.rotation_matrix.c,
            page.rotation_matrix.d, page.rotation_matrix.e, page.rotation_matrix.f,
        ]
        page_rect = [visual_rect.x0, visual_rect.y0, visual_rect.x1, visual_rect.y1]
        visual_clip = [clip.x0, clip.y0, clip.x1, clip.y1]
    return {
        **asdict(spec),
        "source_sha256": sha256_file(source),
        "render_dpi": dpi,
        "rendered_path": str(output_path),
        "rendered_sha256": sha256_file(output_path),
        "rendered_width_px": pixmap.width,
        "rendered_height_px": pixmap.height,
        "bbox_coordinate_space": "normalized_0_1_visual_page",
        "source_pdf_page_rect": page_rect,
        "source_pdf_rotation_degrees": rotation_degrees,
        "source_pdf_rotation_matrix": rotation_matrix,
        "visual_clip_points": visual_clip,
    }


def pdf_bbox_to_rendered_pixels(
    pdf_bbox: tuple[float, float, float, float] | list[float],
    panel: Mapping[str, Any],
) -> list[float]:
    """Transform an unrotated PDF-point bbox into rendered panel pixels."""
    required = {
        "source_pdf_rotation_matrix", "visual_clip_points",
        "rendered_width_px", "rendered_height_px",
    }
    missing = required - panel.keys()
    if missing:
        raise ValueError(f"panel lacks transform metadata: {', '.join(sorted(missing))}")
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("bbox transformation requires PyMuPDF") from exc
    matrix = pymupdf.Matrix(*panel["source_pdf_rotation_matrix"])
    source_rect = pymupdf.Rect(*pdf_bbox)
    visual_rect = source_rect * matrix
    clip = pymupdf.Rect(*panel["visual_clip_points"])
    scale_x = float(panel["rendered_width_px"]) / clip.width
    scale_y = float(panel["rendered_height_px"]) / clip.height
    result = [
        (visual_rect.x0 - clip.x0) * scale_x,
        (visual_rect.y0 - clip.y0) * scale_y,
        (visual_rect.x1 - clip.x0) * scale_x,
        (visual_rect.y1 - clip.y0) * scale_y,
    ]
    return [max(0.0, value) for value in result]


def create_annotation(
    annotation_id: str,
    panel: Mapping[str, Any],
    record: Mapping[str, Any],
    annotator_id: str,
    status: str = "auto",
) -> dict[str, Any]:
    if status not in ANNOTATION_STATUSES:
        raise ValueError(f"unsupported annotation status: {status}")
    validate_record(record)
    now = datetime.now(timezone.utc).isoformat()
    return {
        "annotation_schema_version": "v001",
        "annotation_id": annotation_id,
        "revision": 1,
        "annotation_status": status,
        "annotator_id": annotator_id,
        "created_at": now,
        "updated_at": now,
        "panel": dict(panel),
        "record": dict(record),
    }


def validate_annotation(annotation: Mapping[str, Any]) -> None:
    required = {
        "annotation_schema_version", "annotation_id", "revision", "annotation_status",
        "annotator_id", "created_at", "updated_at", "panel", "record",
    }
    missing = required - annotation.keys()
    if missing:
        raise ValueError(f"missing annotation keys: {', '.join(sorted(missing))}")
    if annotation["annotation_schema_version"] != "v001":
        raise ValueError("unsupported annotation schema version")
    if annotation["annotation_status"] not in ANNOTATION_STATUSES:
        raise ValueError("unsupported annotation status")
    if not isinstance(annotation["revision"], int) or annotation["revision"] < 1:
        raise ValueError("revision must be a positive integer")
    validate_record(annotation["record"])


def save_annotation(annotation: Mapping[str, Any], destination: Path) -> Path:
    """Atomically save a revision and preserve the prior file in history."""
    validate_annotation(annotation)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        previous = json.loads(destination.read_text(encoding="utf-8"))
        validate_annotation(previous)
        expected_revision = int(previous["revision"]) + 1
        if int(annotation["revision"]) != expected_revision:
            raise ValueError(f"revision conflict: expected {expected_revision}")
        history = destination.parent / "history" / str(previous["annotation_id"])
        history.mkdir(parents=True, exist_ok=True)
        history_path = history / f"revision_{previous['revision']:04d}.json"
        history_path.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(annotation), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, destination)
    return destination


def revise_annotation(
    annotation: Mapping[str, Any],
    record: Mapping[str, Any],
    annotator_id: str,
    status: str,
) -> dict[str, Any]:
    validate_annotation(annotation)
    if status not in ANNOTATION_STATUSES:
        raise ValueError(f"unsupported annotation status: {status}")
    validate_record(record)
    revised = dict(annotation)
    revised["record"] = dict(record)
    revised["annotator_id"] = annotator_id
    revised["annotation_status"] = status
    revised["revision"] = int(annotation["revision"]) + 1
    revised["updated_at"] = datetime.now(timezone.utc).isoformat()
    return revised
