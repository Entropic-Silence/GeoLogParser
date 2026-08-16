"""Deterministic decoding of NativeMM intermediate structural graphs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .geometry import GeometryDecodeResult, decode_depth_geometry


BOUNDARY_EVENT_TYPES = frozenset(
    {
        "geological_boundary",
        "interval_boundary",
        "lithology_start",
        "stratum_start",
        "layer_start",
        "boundary",
        "lithology_change",
        "description_change",
    }
)
BOUNDARY_OWNERS = frozenset(
    {
        "geological_description",
        "lithology",
        "stratigraphy",
        "graphic_log",
        "table_structure",
        "unknown",
    }
)


@dataclass(frozen=True)
class StructuralGraphDecode:
    boundary_y: tuple[float, ...]
    geometry: GeometryDecodeResult
    selected_events: int
    rejected_events: int
    warnings: tuple[str, ...]


def _center_y(event: dict[str, Any]) -> float | None:
    bbox = event.get("bbox_xyxy")
    if not isinstance(bbox, list) or len(bbox) != 4:
        return None
    try:
        y0, y1 = float(bbox[1]), float(bbox[3])
    except (TypeError, ValueError):
        return None
    return (y0 + y1) / 2.0


def decode_structural_graph(
    graph: dict[str, Any] | None,
    *,
    residual_tolerance_m: float = 0.10,
    minimum_gap_m: float = 0.005,
    final_depth_m: float | None = None,
) -> StructuralGraphDecode:
    """Select structural boundary evidence and hand it to geometry decoding.

    The model is not allowed to emit interval depths directly.  Only events
    whose type/owner identifies a possible geological boundary are selected;
    depths are reconstructed from the model's axis points by the deterministic
    line-fitting decoder.
    """
    if not isinstance(graph, dict):
        return StructuralGraphDecode((), decode_depth_geometry([], []), 0, 0, ("GRAPH_UNAVAILABLE",))
    selected: list[float] = []
    rejected = 0
    for event in graph.get("events", []):
        if not isinstance(event, dict):
            rejected += 1
            continue
        event_type = str(event.get("event_type", "")).lower()
        owner = str(event.get("owner", "")).lower()
        confidence = float(event.get("confidence", 0.0) or 0.0)
        y = _center_y(event)
        if event_type not in BOUNDARY_EVENT_TYPES or owner not in BOUNDARY_OWNERS or y is None or confidence < 0.50:
            rejected += 1
            continue
        selected.append(y)

    axis = graph.get("depth_geometry") or {}
    points: list[tuple[float, float]] = []
    for item in axis.get("axis_points", []):
        if not isinstance(item, dict) or item.get("depth_m") is None:
            continue
        try:
            points.append((float(item["y"]), float(item["depth_m"])))
        except (TypeError, ValueError):
            continue
    geometry = decode_depth_geometry(
        selected,
        points,
        residual_tolerance_m=residual_tolerance_m,
        minimum_gap_m=minimum_gap_m,
        final_depth_m=final_depth_m,
    )
    warnings = list(geometry.warnings)
    if not selected:
        warnings.append("NO_BOUNDARY_EVENTS_SELECTED")
    return StructuralGraphDecode(tuple(sorted(selected)), geometry, len(selected), rejected, tuple(warnings))
