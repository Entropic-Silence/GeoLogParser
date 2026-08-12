"""Panel rendering and revisioned annotation records."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from geologparser.datasets.manifest import sha256_file
from geologparser.schema import validate_record


ANNOTATION_STATUSES = {"auto", "single_verified", "double_verified", "expert_verified"}


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
    return {
        **asdict(spec),
        "source_sha256": sha256_file(source),
        "render_dpi": dpi,
        "rendered_path": str(output_path),
        "rendered_sha256": sha256_file(output_path),
        "rendered_width_px": pixmap.width,
        "rendered_height_px": pixmap.height,
        "bbox_coordinate_space": "normalized_0_1_visual_page",
    }


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
