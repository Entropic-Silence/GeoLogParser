"""Reference-blind graphical boundary grounding for scanned borehole pages.

The detector separates two tasks which are often conflated by OCR pipelines:
recovering a page depth axis and finding horizontal geological contact evidence.
It deliberately returns evidence and abstains when the page has no stable
numeric axis.  Official intervals are not accepted by this module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Mapping, Sequence

import cv2
import numpy as np

from .long_page import LogPanelLayout


@dataclass(frozen=True)
class DepthAxis:
    slope_m_per_px: float
    intercept_m: float
    x_center_px: float
    inlier_count: int
    rmse_m: float
    source_tokens: tuple[Mapping[str, object], ...]

    def depth_at(self, y_px: float) -> float:
        return self.slope_m_per_px * float(y_px) + self.intercept_m

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GraphicalBoundaryEvent:
    y_px: float
    depth_m: float
    line_support: float
    transition_support: float
    x1_px: int
    x2_px: int
    confidence: float
    provenance: tuple[Mapping[str, object], ...]

    def to_dict(self) -> dict:
        return asdict(self)


_NUMBER = re.compile(r"^\s*([0-9]{1,4}(?:[.,][0-9]{1,3})?)\s*m?\s*$", re.I)


def _numeric_rows(rows: Sequence[Mapping[str, object]], *, width: int, height: int, layout: LogPanelLayout) -> list[tuple[float, float, float, Mapping[str, object]]]:
    output = []
    for row in rows:
        match = _NUMBER.fullmatch(str(row.get("text") or ""))
        if not match:
            continue
        try:
            value = float(match.group(1).replace(",", "."))
            bbox = tuple(float(item) for item in row["bbox"])
        except (KeyError, TypeError, ValueError):
            continue
        x = (bbox[0] + bbox[2]) / 2.0
        y = (bbox[1] + bbox[3]) / 2.0
        if not (0.0 <= value <= 5000.0 and layout.y_min * height <= y <= layout.y_max * height):
            continue
        output.append((value, x, y, row))
    return output


def fit_reference_blind_depth_axis(
    rows: Sequence[Mapping[str, object]], *, width: int, height: int,
    layout: LogPanelLayout, x_cluster_tolerance: float = 0.018,
    residual_tolerance_m: float = 0.40, minimum_inliers: int = 3,
) -> DepthAxis | None:
    """Fit a positive y-to-depth line using only positioned page tokens.

    Pairwise hypotheses make the fit robust to a stray date, water depth, or
    terminal metadata value that happens to be close to the depth column.
    """
    values = _numeric_rows(rows, width=width, height=height, layout=layout)
    if len(values) < minimum_inliers:
        return None
    groups: list[list[tuple[float, float, float, Mapping[str, object]]]] = []
    for item in sorted(values, key=lambda row: row[1]):
        if not groups or item[1] - groups[-1][-1][1] > max(24.0, width * x_cluster_tolerance):
            groups.append([item])
        else:
            groups[-1].append(item)
    best: tuple[tuple[float, ...], float, float, float, list[tuple[float, float, float, Mapping[str, object]]] ] | None = None
    for group in groups:
        if len(group) < minimum_inliers:
            continue
        for left_index, left in enumerate(group[:-1]):
            for right in group[left_index + 1:]:
                dv = right[0] - left[0]
                dy = right[2] - left[2]
                if dv <= 1.0 or dy <= max(40.0, height * 0.012):
                    continue
                slope = dv / dy
                intercept = left[0] - slope * left[2]
                inliers = [row for row in group if abs(row[0] - (slope * row[2] + intercept)) <= residual_tolerance_m]
                if len(inliers) < minimum_inliers:
                    continue
                ys = np.asarray([row[2] for row in inliers], dtype=float)
                depths = np.asarray([row[0] for row in inliers], dtype=float)
                refined_slope, refined_intercept = np.polyfit(ys, depths, 1)
                if refined_slope <= 0:
                    continue
                residuals = depths - (refined_slope * ys + refined_intercept)
                rmse = float(np.sqrt(np.mean(residuals ** 2)))
                score = (float(len(inliers)), float(ys[-1] - ys[0]), -rmse, float(sum(row[0] > previous[0] for previous, row in zip(inliers, inliers[1:]))))
                if best is None or score > best[0]:
                    best = (score, float(refined_slope), float(refined_intercept), float(np.median([row[1] for row in inliers])), inliers)
    if best is None:
        return None
    _, slope, intercept, x_center, inliers = best
    rmse = float(np.sqrt(np.mean([(row[0] - (slope * row[2] + intercept)) ** 2 for row in inliers])))
    return DepthAxis(
        slope_m_per_px=slope, intercept_m=intercept, x_center_px=x_center,
        inlier_count=len(inliers), rmse_m=rmse,
        source_tokens=tuple({"text": str(row[3].get("text") or ""), "value_m": row[0], "bbox": list(row[3]["bbox"])} for row in inliers),
    )


def _group_peaks(values: np.ndarray, threshold: float, minimum_spacing: int) -> list[int]:
    indices = np.flatnonzero(values >= threshold)
    groups: list[list[int]] = []
    for index in indices:
        if not groups or int(index) - groups[-1][-1] > minimum_spacing:
            groups.append([int(index)])
        else:
            groups[-1].append(int(index))
    return [max(group, key=lambda index: float(values[index])) for group in groups]


def detect_graphical_boundary_events(
    gray: np.ndarray, *, layout: LogPanelLayout, axis: DepthAxis,
    description_x_center: float | None = None, minimum_line_fraction: float = 0.26,
) -> list[GraphicalBoundaryEvent]:
    """Detect long horizontal contacts between the depth and description fields.

    The search band is anchored by the recovered depth-column x position and
    the semantic description header when available.  A second transition
    signal captures contacts that are printed as a change of fill rather than
    a fully continuous line.  Table/header borders outside the calibrated
    depth range are discarded without reference access.
    """
    if gray.ndim != 2:
        raise ValueError("gray must be a 2-D grayscale image")
    height, width = gray.shape
    y1 = max(0, int(round(layout.y_min * height)))
    y2 = min(height, int(round(layout.y_max * height)))
    if y2 <= y1:
        return []
    x_center = axis.x_center_px
    desc_x = description_x_center if description_x_center is not None else x_center / width + 0.18
    x1 = max(0, int(round(x_center - max(18.0, width * 0.015))))
    x2 = min(width, int(round(max(desc_x, x_center / width + 0.10) * width + width * 0.15)))
    if x2 - x1 < max(80, int(width * 0.08)):
        return []
    crop = gray[y1:y2, x1:x2]
    dark = (crop < 180).astype(np.uint8) * 255
    line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(24, int(width * 0.055)), 1))
    horizontal = cv2.morphologyEx(dark, cv2.MORPH_OPEN, line_kernel)
    line_score = (horizontal > 0).sum(axis=1) / max(1, x2 - x1)
    density = (dark > 0).mean(axis=1)
    smooth_width = max(5, int(round(height * 0.0018)))
    smooth = np.convolve(density, np.ones(smooth_width) / smooth_width, mode="same")
    window = max(8, int(round(height * 0.0035)))
    transition = np.zeros_like(smooth)
    for index in range(window, len(smooth) - window):
        transition[index] = abs(float(smooth[index - window:index].mean()) - float(smooth[index:index + window].mean()))
    combined = line_score + 1.8 * transition
    peaks = _group_peaks(combined, max(minimum_line_fraction, 0.20), max(6, int(height * 0.0018)))
    output: list[GraphicalBoundaryEvent] = []
    for local_y in peaks:
        y = y1 + local_y
        depth = axis.depth_at(y)
        if not 0.0 <= depth <= 5000.0:
            continue
        line = float(line_score[local_y])
        change = float(transition[local_y])
        confidence = min(1.0, 0.55 * min(1.0, line / 0.70) + 0.45 * min(1.0, change / 0.12))
        output.append(GraphicalBoundaryEvent(
            y_px=float(y), depth_m=float(depth), line_support=line,
            transition_support=change, x1_px=x1, x2_px=x2,
            confidence=confidence,
            provenance=({
                "method": "horizontal_contact_and_density_transition",
                "axis_inlier_count": axis.inlier_count,
                "axis_rmse_m": axis.rmse_m,
                "search_band_normalized": [x1 / width, x2 / width],
            },),
        ))
    return output


def ground_graphical_boundaries(
    rows: Sequence[Mapping[str, object]], gray: np.ndarray, *, layout: LogPanelLayout,
) -> tuple[DepthAxis | None, list[GraphicalBoundaryEvent]]:
    """Convenience reference-blind page expert with explicit abstention."""
    axis = fit_reference_blind_depth_axis(rows, width=gray.shape[1], height=gray.shape[0], layout=layout)
    if axis is None or axis.rmse_m > 0.45 or axis.inlier_count < 3:
        return axis, []
    description = layout.anchors.get("description")
    events = detect_graphical_boundary_events(
        gray, layout=layout, axis=axis,
        description_x_center=description.center_x if description is not None else None,
    )
    return axis, events
