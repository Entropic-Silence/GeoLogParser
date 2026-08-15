"""Source-agnostic semantic anchoring and tiling for long borehole-log pages."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping, Sequence

from geologparser.ocr import TextRegion


SEMANTIC_PATTERNS: Mapping[str, re.Pattern[str]] = {
    "depth": re.compile(r"\b(depth|metres?\s+below|feet\s+below)\b", re.I),
    "lithology": re.compile(r"\b(lithology|lithological|stratigraphy)\b", re.I),
    "description": re.compile(r"\b(description|material\s+description)\b", re.I),
    "sample": re.compile(r"\b(samples?|sub[ .-]*samples?)\b", re.I),
    "comments": re.compile(r"\b(comments?|remarks?)\b", re.I),
}


@dataclass(frozen=True)
class SemanticAnchor:
    semantic: str
    text: str
    confidence: float
    center_x: float
    center_y: float
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class LogPanelLayout:
    header_y: float
    anchor_row_score: int
    anchors: Mapping[str, SemanticAnchor]
    x_min: float
    x_max: float
    y_min: float
    y_max: float


@dataclass(frozen=True)
class PageTile:
    tile_id: str
    bbox: tuple[int, int, int, int]
    overlap_top_px: int
    overlap_bottom_px: int


def semantic_anchors(
    regions: Sequence[TextRegion], width: int, height: int,
) -> list[SemanticAnchor]:
    if width <= 0 or height <= 0:
        raise ValueError("page dimensions must be positive")
    output: list[SemanticAnchor] = []
    for region in regions:
        if region.bbox is None:
            continue
        for semantic, pattern in SEMANTIC_PATTERNS.items():
            if pattern.search(region.text):
                x1, y1, x2, y2 = region.bbox
                output.append(SemanticAnchor(
                    semantic=semantic,
                    text=region.text,
                    confidence=float(region.confidence or 0.0),
                    center_x=((x1 + x2) / 2) / width,
                    center_y=((y1 + y2) / 2) / height,
                    bbox=tuple(float(value) for value in region.bbox),
                ))
    return output


def infer_log_panel_layout(
    regions: Sequence[TextRegion], width: int, height: int,
    *, row_tolerance: float = 0.035,
) -> LogPanelLayout | None:
    """Infer the table header row from semantic co-occurrence, not fixed columns.

    Header candidates are clustered by normalized y.  Rows containing both a
    lithology/description concept and at least one additional field receive
    priority; lower rows break ties because report metadata often contains an
    unrelated ``depth`` label near the page top.
    """
    anchors = semantic_anchors(regions, width, height)
    if not anchors:
        return None
    candidates: list[tuple[int, float, dict[str, SemanticAnchor]]] = []
    for pivot in anchors:
        row = [item for item in anchors if abs(item.center_y - pivot.center_y) <= row_tolerance]
        by_semantic: dict[str, SemanticAnchor] = {}
        for item in sorted(row, key=lambda value: value.confidence, reverse=True):
            by_semantic.setdefault(item.semantic, item)
        core = int("lithology" in by_semantic) + int("description" in by_semantic)
        if core == 0:
            continue
        score = 4 * core + len(by_semantic)
        candidates.append((score, pivot.center_y, by_semantic))
    if not candidates:
        return None
    score, header_y, selected = max(candidates, key=lambda item: (item[0], item[1]))
    xs = [item.center_x for item in selected.values()]
    x_min = max(0.0, min(xs) - 0.16)
    x_max = min(1.0, max(xs) + 0.22)
    return LogPanelLayout(
        header_y=header_y,
        anchor_row_score=score,
        anchors=selected,
        x_min=x_min,
        x_max=x_max,
        y_min=max(0.0, header_y - 0.015),
        y_max=0.995,
    )


def long_page_tiles(
    width: int, height: int, layout: LogPanelLayout,
    *, target_height_px: int = 1800, overlap_px: int = 180,
) -> list[PageTile]:
    """Create overlapping, traceable tiles over the inferred log panel."""
    if target_height_px <= 0 or overlap_px < 0 or overlap_px >= target_height_px:
        raise ValueError("invalid tile height/overlap")
    x1 = max(0, int(width * layout.x_min))
    x2 = min(width, max(x1 + 1, int(width * layout.x_max)))
    y1 = max(0, int(height * layout.y_min))
    y2 = min(height, max(y1 + 1, int(height * layout.y_max)))
    step = target_height_px - overlap_px
    output: list[PageTile] = []
    start = y1
    index = 0
    while start < y2:
        end = min(y2, start + target_height_px)
        output.append(PageTile(
            tile_id=f"tile_{index:03d}", bbox=(x1, start, x2, end),
            overlap_top_px=0 if index == 0 else overlap_px,
            overlap_bottom_px=0 if end == y2 else overlap_px,
        ))
        if end == y2:
            break
        start += step
        index += 1
    return output


def tile_bbox_to_page(
    bbox: tuple[float, float, float, float], tile: PageTile, *, scale: float = 1.0,
) -> tuple[float, float, float, float]:
    if scale <= 0:
        raise ValueError("scale must be positive")
    x1, y1, _, _ = tile.bbox
    return tuple(
        value
        for pair in (
            (x1 + bbox[0] / scale, y1 + bbox[1] / scale),
            (x1 + bbox[2] / scale, y1 + bbox[3] / scale),
        )
        for value in pair
    )
