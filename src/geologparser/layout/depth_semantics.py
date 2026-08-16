"""Reference-blind depth-column semantics for heterogeneous borehole logs.

The module converts positioned OCR and page pixels into explicit candidate
evidence.  It deliberately separates candidate generation from candidate
ranking: labels may be used to train a ranker on a development source, but are
never consulted by the page parser or the geometric feature extractors.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Mapping, Sequence

import cv2
import numpy as np

from .long_page import LogPanelLayout
from .column_roles import assign_column_roles, infer_column_role_anchors, select_graphical_roles


@dataclass(frozen=True)
class NumericEvidence:
    value: float
    page: int
    bbox: tuple[float, float, float, float]
    max_confidence: float
    view_support: int
    competing_views: int
    full_page_support: bool
    source_texts: tuple[str, ...]

    @property
    def center_x(self) -> float:
        return (self.bbox[0] + self.bbox[2]) / 2

    @property
    def center_y(self) -> float:
        return (self.bbox[1] + self.bbox[3]) / 2


@dataclass(frozen=True)
class DepthScaleCalibration:
    depth_per_pixel: float
    intercept_m: float
    inlier_count: int
    rmse_m: float
    x_center_normalized: float

    def depth_at(self, y: float) -> float:
        return self.depth_per_pixel * y + self.intercept_m


@dataclass(frozen=True)
class DepthBoundaryCandidate:
    value_m: float
    page: int
    bbox: tuple[float, float, float, float]
    candidate_source: str
    features: Mapping[str, float]
    provenance: tuple[Mapping[str, object], ...]


def _center(bbox: Sequence[float]) -> tuple[float, float]:
    return (float(bbox[0] + bbox[2]) / 2, float(bbox[1] + bbox[3]) / 2)


def aggregate_numeric_evidence(
    rows: Iterable[Mapping[str, object]], *, page: int,
    spatial_tolerance_px: float = 12.0, value_tolerance: float = 1e-6,
) -> list[NumericEvidence]:
    """Fuse repeated OCR views while retaining conflicting readings.

    Repeated gray/Otsu and PSM views support the same value.  A different
    value at the same position contributes to ``competing_views`` rather than
    being silently discarded, which exposes OCR ambiguity to the ranker.
    """
    materialized = []
    for row in rows:
        try:
            value = float(row["value"])
            bbox = tuple(float(item) for item in row["bbox"])
        except (KeyError, TypeError, ValueError):
            continue
        if not math.isfinite(value) or len(bbox) != 4:
            continue
        materialized.append((value, bbox, row))
    groups: list[list[tuple[float, tuple[float, ...], Mapping[str, object]]]] = []
    for item in sorted(materialized, key=lambda row: (_center(row[1])[1], _center(row[1])[0], row[0])):
        value, bbox, _ = item
        cx, cy = _center(bbox)
        matching = None
        for group in groups:
            gv, gb, _ = group[0]
            gx, gy = _center(gb)
            if abs(value - gv) <= value_tolerance and math.hypot(cx - gx, cy - gy) <= spatial_tolerance_px:
                matching = group
                break
        if matching is None:
            groups.append([item])
        else:
            matching.append(item)
    output = []
    for group in groups:
        value = group[0][0]
        weights = [max(0.05, float(row.get("confidence") or 0.0)) for _, _, row in group]
        total = sum(weights)
        bbox = tuple(
            sum(weight * item[1][axis] for weight, item in zip(weights, group)) / total
            for axis in range(4)
        )
        cx, cy = _center(bbox)
        competitors = sum(
            1 for other_value, other_bbox, _ in materialized
            if abs(other_value - value) > value_tolerance
            and math.hypot(cx - _center(other_bbox)[0], cy - _center(other_bbox)[1]) <= spatial_tolerance_px
        )
        output.append(NumericEvidence(
            value=value,
            page=page,
            bbox=bbox,
            max_confidence=max(float(row.get("confidence") or 0.0) for _, _, row in group),
            view_support=len(group),
            competing_views=competitors,
            full_page_support=any(row.get("variant") is None for _, _, row in group),
            source_texts=tuple(sorted({str(row.get("text") or "") for _, _, row in group})),
        ))
    return output


def _least_squares(points: Sequence[tuple[float, float]]) -> tuple[float, float, float]:
    ys = np.asarray([point[0] for point in points], dtype=float)
    values = np.asarray([point[1] for point in points], dtype=float)
    matrix = np.column_stack([ys, np.ones(len(ys))])
    slope, intercept = np.linalg.lstsq(matrix, values, rcond=None)[0]
    residuals = values - (slope * ys + intercept)
    return float(slope), float(intercept), float(np.sqrt(np.mean(residuals ** 2)))


def fit_depth_scale(
    evidence: Sequence[NumericEvidence], layout: LogPanelLayout,
    *, width: int, height: int, x_tolerance: float = 0.045,
    residual_tolerance_m: float = 0.35, x_center_hint: float | None = None,
) -> DepthScaleCalibration | None:
    """Robustly calibrate a printed depth scale without terminal-depth input."""
    anchor = layout.anchors.get("depth")
    # A field-specific ROI estimate must take precedence over a generic depth
    # anchor: report headers frequently contain an unrelated TOTAL DEPTH label.
    anchor_x = x_center_hint if x_center_hint is not None else (anchor.center_x if anchor is not None else None)
    if anchor_x is None:
        return None
    candidates = [
        item for item in evidence
        if abs(item.center_x / width - anchor_x) <= x_tolerance
        and item.center_y / height >= layout.y_min
        and 0 <= item.value <= 5000
    ]
    if len(candidates) < 3:
        return None
    best: tuple[int, float, float, float, list[NumericEvidence]] | None = None
    for left_index, left in enumerate(candidates):
        for right in candidates[left_index + 1:]:
            dy = right.center_y - left.center_y
            dv = right.value - left.value
            if dy <= max(60.0, height * 0.015) or dv <= 1.0:
                continue
            slope = dv / dy
            if not 1e-5 < slope < 2.0:
                continue
            intercept = left.value - slope * left.center_y
            inliers = [
                item for item in candidates
                if abs(item.value - (slope * item.center_y + intercept)) <= residual_tolerance_m
            ]
            unique_depths = len({round(item.value, 3) for item in inliers})
            if unique_depths < 3:
                continue
            refined_slope, refined_intercept, rmse = _least_squares(
                [(item.center_y, item.value) for item in inliers]
            )
            score = (unique_depths, sum(item.view_support for item in inliers), -rmse)
            if best is None or score > (best[0], best[1], -best[2]):
                best = (unique_depths, float(score[1]), rmse, refined_slope, inliers)
                best_intercept = refined_intercept
    if best is None:
        return None
    _, _, rmse, slope, inliers = best
    return DepthScaleCalibration(
        depth_per_pixel=slope,
        intercept_m=best_intercept,
        inlier_count=len({round(item.value, 3) for item in inliers}),
        rmse_m=rmse,
        x_center_normalized=anchor_x,
    )


def horizontal_line_features(
    gray: np.ndarray, bbox: Sequence[float], *, left_x: float, right_x: float,
    threshold: int = 160,
) -> dict[str, float]:
    """Measure boundary-line evidence on both sides of a printed number."""
    height, width = gray.shape[:2]
    y = int(round((bbox[1] + bbox[3]) / 2))
    half_window = max(4, int(round(height * 0.0012)))

    def side(start: float, end: float) -> tuple[float, float]:
        x1 = max(0, min(width, int(round(start))))
        x2 = max(0, min(width, int(round(end))))
        if x2 <= x1 or y + half_window + 1 <= 0 or y - half_window >= height:
            return 0.0, 0.0
        binary = (gray[max(0, y - half_window):min(height, y + half_window + 1), x1:x2] < threshold).astype(np.uint8)
        longest = 0
        for row in binary:
            edges = np.flatnonzero(np.diff(np.r_[0, row, 0]))
            if len(edges):
                longest = max(longest, int(np.max(edges[1::2] - edges[::2])))
        return longest / max(1, x2 - x1), float(binary.mean())

    left_run, left_dark = side(left_x, float(bbox[0]) - 3)
    right_run, right_dark = side(float(bbox[2]) + 3, right_x)
    return {
        "line_left_run": left_run,
        "line_right_run": right_run,
        "line_left_dark": left_dark,
        "line_right_dark": right_dark,
    }


def detect_graphic_log_column(
    gray: np.ndarray, layout: LogPanelLayout, *, depth_x_hint: float | None = None,
) -> tuple[int, int] | None:
    """Locate the texture-bearing graphic-log column from vertical rules."""
    height, width = gray.shape[:2]
    depth = layout.anchors.get("depth")
    lithology = layout.anchors.get("lithology")
    depth_x = depth_x_hint if depth_x_hint is not None else (depth.center_x if depth is not None else None)
    if depth_x is None:
        return None
    y1 = max(0, int(layout.y_min * height))
    y2 = min(height, int(layout.y_max * height))
    # Historical templates place the graphic log on either side of the depth
    # scale. Search locally in both directions instead of encoding one order.
    semantic_right = lithology.center_x + 0.03 if lithology is not None else depth_x + 0.14
    x1 = max(0, int(max(layout.x_min, depth_x - 0.14) * width))
    x2 = min(width, int(min(layout.x_max, max(depth_x + 0.14, semantic_right)) * width))
    if x2 - x1 < width * 0.025 or y2 <= y1:
        return None
    binary = (gray[y1:y2, x1:x2] < 160).astype(np.uint8) * 255
    kernel_height = max(30, int((y2 - y1) * 0.18))
    vertical = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_height)),
    )
    score = (vertical > 0).sum(axis=0)
    threshold = max(20, int((y2 - y1) * 0.12))
    peaks: list[int] = []
    for local_x in np.flatnonzero(score >= threshold):
        absolute = x1 + int(local_x)
        if not peaks or absolute - peaks[-1] > 5:
            peaks.append(absolute)
        elif score[local_x] > score[peaks[-1] - x1]:
            peaks[-1] = absolute
    pairs = []
    for left_index, left in enumerate(peaks):
        for right in peaks[left_index + 1:]:
            span = right - left
            if not width * 0.025 <= span <= width * 0.12:
                continue
            interior = gray[y1:y2, left + 2:right - 2]
            texture = float((interior < 180).mean()) if interior.size else 0.0
            center = (left + right) / 2 / width
            proximity = min(abs(center - (depth_x - 0.045)), abs(center - (depth_x + 0.045)))
            pairs.append((texture - 0.8 * proximity, left, right))
    if not pairs:
        return None
    _, left, right = max(pairs)
    return left, right


def detect_graphic_log_columns(
    gray: np.ndarray,
    layout: LogPanelLayout,
    *,
    depth_x_hint: float | None = None,
    maximum_columns: int = 8,
) -> list[tuple[int, int, float]]:
    """Locate multiple narrow, structure-bearing columns around the depth field.

    Borehole boundaries may be expressed independently in recovery, interpreted
    lithology, graphic lithology, formation and description/contact columns. A
    single texture column therefore imposes a template-specific recall ceiling.
    Returned scores are reference-blind image activity measures.
    """
    height, width = gray.shape[:2]
    depth = layout.anchors.get("depth")
    description = layout.anchors.get("description")
    depth_x = depth_x_hint if depth_x_hint is not None else (depth.center_x if depth is not None else None)
    if depth_x is None:
        return []
    y1 = max(0, int(layout.y_min * height)); y2 = min(height, int(layout.y_max * height))
    right_limit = description.center_x + 0.025 if description is not None else depth_x + 0.22
    x1 = max(0, int(max(layout.x_min, depth_x - 0.24) * width))
    x2 = min(width, int(min(layout.x_max, depth_x + 0.24, right_limit) * width))
    if x2 - x1 < width * 0.04 or y2 <= y1:
        return []
    binary = (gray[y1:y2, x1:x2] < 165).astype(np.uint8) * 255
    kernel_height = max(30, int((y2 - y1) * 0.16))
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_height)))
    vertical_score = (vertical > 0).sum(axis=0)
    peak_threshold = max(20, int((y2 - y1) * 0.10))
    peaks: list[int] = []
    for local_x in np.flatnonzero(vertical_score >= peak_threshold):
        absolute = x1 + int(local_x)
        if not peaks or absolute - peaks[-1] > 5:
            peaks.append(absolute)
        elif vertical_score[local_x] > vertical_score[peaks[-1] - x1]:
            peaks[-1] = absolute
    candidates: list[tuple[float, int, int]] = []
    for left, right in zip(peaks, peaks[1:]):
        span = right - left
        if not width * 0.012 <= span <= width * 0.13:
            continue
        interior = gray[y1:y2, left + 2:right - 2]
        if interior.size == 0:
            continue
        darkness = (interior < 180).astype(np.float32)
        density = darkness.mean(axis=1)
        texture = float(darkness.mean())
        activity = float(np.std(density))
        gradient = float(np.percentile(np.abs(np.diff(density)), 90)) if len(density) > 1 else 0.0
        center = (left + right) / 2 / width
        proximity = abs(center - depth_x)
        score = 0.45 * texture + 1.8 * activity + 1.2 * gradient - 0.20 * proximity
        if texture < 0.003 and activity < 0.01:
            continue
        candidates.append((score, left, right))
    selected: list[tuple[int, int, float]] = []
    for score, left, right in sorted(candidates, reverse=True):
        if any(max(0, min(right, old_right) - max(left, old_left)) / max(1, min(right-left, old_right-old_left)) > 0.65 for old_left, old_right, _ in selected):
            continue
        selected.append((left, right, score))
        if len(selected) >= maximum_columns:
            break
    return sorted(selected, key=lambda item: item[0])


def _graphic_candidates_for_column(
    gray: np.ndarray,
    *,
    page: int,
    layout: LogPanelLayout,
    calibration: DepthScaleCalibration,
    column: tuple[int, int],
    column_rank: int = 0,
    column_activity: float = 0.0,
) -> list[DepthBoundaryCandidate]:
    height, width = gray.shape[:2]
    left, right = column
    y1 = max(0, int(layout.y_min * height)); y2 = min(height, int(layout.y_max * height))
    binary = (gray[y1:y2, left:right] < 160).astype(np.uint8) * 255
    span = max(1, right - left)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(5, int(span * 0.45)), 1)))
    line_score = (opened > 0).sum(axis=1) / span
    density = (binary > 0).mean(axis=1)
    smooth_width = max(3, int(height * 0.002)); kernel = np.ones(smooth_width) / smooth_width
    smooth_density = np.convolve(density, kernel, mode="same")
    window = max(5, int(height * 0.004)); change = np.zeros_like(smooth_density)
    for index in range(window, len(change) - window):
        change[index] = abs(float(smooth_density[index-window:index].mean()) - float(smooth_density[index:index+window].mean()))
    eligible = np.flatnonzero((line_score >= 0.24) | (change >= 0.065))
    peaks: list[int] = []; min_spacing = max(6, int(height * 0.002)); combined = line_score + 2.2 * change
    for local_y in eligible:
        absolute = y1 + int(local_y)
        if not peaks or absolute - peaks[-1] > min_spacing:
            peaks.append(absolute)
        elif combined[local_y] > combined[peaks[-1] - y1]:
            peaks[-1] = absolute
    output = []
    for y in peaks:
        raw_depth = calibration.depth_at(y)
        if not 0 <= raw_depth <= 5000:
            continue
        local_y = y - y1
        external_line = horizontal_line_features(gray, (float(left), float(y-2), float(right), float(y+2)), left_x=max(0,layout.x_min*width), right_x=min(width,layout.x_max*width))
        hypotheses: set[tuple[float,float]] = {(round(raw_depth*20)/20,0.05)}
        for step in (0.1,0.5,1.0):
            lower=math.floor(raw_depth/step)*step; upper=math.ceil(raw_depth/step)*step
            for value in (lower,upper):
                if abs(value-raw_depth) <= max(0.16,step*0.55): hypotheses.add((round(value,6),step))
        for rounded_depth,snap_step in sorted(hypotheses):
            features = {
                "source_printed":0.0,"source_graphic":1.0,"source_metadata":0.0,"ocr_confidence":0.0,
                "view_support":0.0,"view_agreement":1.0,"full_page_support":0.0,"line_left_run":0.0,
                "line_right_run":float(line_score[local_y]),"line_left_dark":0.0,"line_right_dark":float(density[local_y]),
                "external_left_run":external_line["line_left_run"],"external_right_run":external_line["line_right_run"],
                "external_left_dark":external_line["line_left_dark"],"external_right_dark":external_line["line_right_dark"],
                "texture_change":float(change[local_y]),"scale_inliers":min(1.0,calibration.inlier_count/6),
                "scale_rmse":min(1.0,calibration.rmse_m),"normalized_y":y/height,"description_x_distance":1.0,
                "depth_x_distance":abs(((left+right)/2)/width-calibration.x_center_normalized),"near_same_y_pair":0.0,
                "snap_step":snap_step,"snap_delta":min(1.0,abs(rounded_depth-raw_depth)),
                "snap_integer":float(abs(rounded_depth-round(rounded_depth))<1e-6),
                "snap_half":float(abs(rounded_depth*2-round(rounded_depth*2))<1e-6),
                "snap_tenth":float(abs(rounded_depth*10-round(rounded_depth*10))<1e-6),
                "printed_line_support":0.0,"printed_pair_support":0.0,"graphic_line_support":float(line_score[local_y]),
                "graphic_change_support":float(change[local_y]),"metadata_cross_field":0.0,
                "graphic_column_center":((left+right)/2)/width,"graphic_column_width":span/width,
                "graphic_column_activity":max(0.0,min(1.0,column_activity)),"graphic_column_rank":1/(1+column_rank),
                "graphic_cross_column_support":0.0,
            }
            output.append(DepthBoundaryCandidate(rounded_depth,page,(float(left),float(y-2),float(right),float(y+2)),"graphic_scale_transition",features,({"method":"multicolumn_graphic_scale_transition","raw_depth_m":raw_depth,"snap_step_m":snap_step,"calibration_inliers":calibration.inlier_count,"calibration_rmse_m":calibration.rmse_m,"graphic_column_bbox":[left,y1,right,y2],"column_rank":column_rank},)))
    return output


def multicolumn_graphic_boundary_candidates(
    gray: np.ndarray, *, page: int, layout: LogPanelLayout,
    calibration: DepthScaleCalibration, depth_x_hint: float | None = None,
) -> list[DepthBoundaryCandidate]:
    """Generate candidates from every plausible field column, not one column."""
    columns = detect_graphic_log_columns(gray, layout, depth_x_hint=depth_x_hint)
    output = [candidate for rank,(left,right,activity) in enumerate(columns) for candidate in _graphic_candidates_for_column(gray,page=page,layout=layout,calibration=calibration,column=(left,right),column_rank=rank,column_activity=activity)]
    for candidate in output:
        cy=(candidate.bbox[1]+candidate.bbox[3])/2
        peers={round(((other.bbox[0]+other.bbox[2])/2)/gray.shape[1],3) for other in output if other is not candidate and abs((other.bbox[1]+other.bbox[3])/2-cy)<=max(8,gray.shape[0]*0.0025)}
        candidate.features["graphic_cross_column_support"] = min(1.0,len(peers)/3)
    return output


def role_aware_multicolumn_graphic_boundary_candidates(
    gray: np.ndarray, *, page: int, layout: LogPanelLayout,
    calibration: DepthScaleCalibration, depth_x_hint: float | None = None,
    rows: Sequence[Mapping[str, object]] = (),
) -> list[DepthBoundaryCandidate]:
    """Generate graphic transitions only from semantically anchored columns.

    Texture-only multi-column detection frequently mistakes Stratigraphy,
    Depth Drilled and auxiliary log columns for the Graphic Log.  This route
    uses OCR header anchors as a reference-blind role gate and is kept
    separate so earlier experiments remain exactly reproducible.
    """
    height, width = gray.shape[:2]
    columns = detect_graphic_log_columns(gray, layout, depth_x_hint=depth_x_hint)
    anchors = infer_column_role_anchors(rows, width=width, height=height, header_y=layout.header_y)
    assignments = assign_column_roles(columns, anchors, width=width)
    selected = select_graphical_roles(assignments)
    # If the header has no recoverable Graphic Log token at all, preserve the
    # legacy multi-column route as an explicitly marked low-semantic-evidence
    # fallback.  A page that does expose a Graphic Log header but whose
    # geometry cannot be matched remains abstained rather than silently
    # reverting to texture-only evidence.
    if not selected and not any(anchor.role == "graphic_log" for anchor in anchors):
        fallback = multicolumn_graphic_boundary_candidates(
            gray, page=page, layout=layout, calibration=calibration,
            depth_x_hint=depth_x_hint,
        )
        output: list[DepthBoundaryCandidate] = []
        for candidate in fallback:
            features = dict(candidate.features)
            features.update({"graphic_role_score": 0.0, "graphic_role_primary": 0.0, "graphic_role_core": 0.0})
            provenance = tuple(candidate.provenance) + ({
                "column_role": "legacy_multicolumn_fallback",
                "column_role_score": 0.0,
                "column_role_evidence": ["header_graphic_role_missing"],
            },)
            output.append(DepthBoundaryCandidate(candidate.value_m, candidate.page, candidate.bbox, candidate.candidate_source, features, provenance))
        return output
    output: list[DepthBoundaryCandidate] = []
    for rank, assignment in enumerate(selected):
        activity = next(
            (float(value) for left, right, value in columns
             if left == assignment.left and right == assignment.right),
            0.0,
        )
        generated = _graphic_candidates_for_column(
            gray, page=page, layout=layout, calibration=calibration,
            column=(assignment.left, assignment.right), column_rank=rank,
            column_activity=activity,
        )
        for candidate in generated:
            features = dict(candidate.features)
            features.update({
                "graphic_role_score": float(assignment.score),
                "graphic_role_primary": float(assignment.role == "graphic_log"),
                "graphic_role_core": float(assignment.role == "core"),
            })
            provenance = tuple(candidate.provenance) + ({
                "column_role": assignment.role,
                "column_role_score": assignment.score,
                "column_role_anchor_x": assignment.anchor_x,
                "column_role_evidence": list(assignment.evidence),
            },)
            output.append(DepthBoundaryCandidate(
                candidate.value_m, candidate.page, candidate.bbox,
                candidate.candidate_source, features, provenance,
            ))
    for candidate in output:
        cy = (candidate.bbox[1] + candidate.bbox[3]) / 2
        peers = {
            round(((other.bbox[0] + other.bbox[2]) / 2) / width, 3)
            for other in output
            if other is not candidate and abs((other.bbox[1] + other.bbox[3]) / 2 - cy) <= max(8, height * 0.0025)
        }
        candidate.features["graphic_cross_column_support"] = min(1.0, len(peers) / 3)
    return output


def graphic_boundary_candidates(
    gray: np.ndarray, *, page: int, layout: LogPanelLayout,
    calibration: DepthScaleCalibration, depth_x_hint: float | None = None,
) -> list[DepthBoundaryCandidate]:
    """Generate depth candidates from graphic-layer transitions and a scale."""
    height, width = gray.shape[:2]
    column = detect_graphic_log_column(gray, layout, depth_x_hint=depth_x_hint)
    if column is None:
        return []
    left, right = column
    y1 = max(0, int(layout.y_min * height))
    y2 = min(height, int(layout.y_max * height))
    binary = (gray[y1:y2, left:right] < 160).astype(np.uint8) * 255
    span = max(1, right - left)
    opened = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(12, int(span * 0.45)), 1)),
    )
    line_score = (opened > 0).sum(axis=1) / span
    density = (binary > 0).mean(axis=1)
    smooth_width = max(3, int(height * 0.002))
    kernel = np.ones(smooth_width) / smooth_width
    smooth_density = np.convolve(density, kernel, mode="same")
    window = max(5, int(height * 0.004))
    change = np.zeros_like(smooth_density)
    for index in range(window, len(change) - window):
        change[index] = abs(
            float(smooth_density[index - window:index].mean())
            - float(smooth_density[index:index + window].mean())
        )
    eligible = np.flatnonzero((line_score >= 0.28) | (change >= 0.09))
    peaks: list[int] = []
    min_spacing = max(6, int(height * 0.002))
    combined_score = line_score + 2.0 * change
    for local_y in eligible:
        absolute = y1 + int(local_y)
        if not peaks or absolute - peaks[-1] > min_spacing:
            peaks.append(absolute)
        elif combined_score[local_y] > combined_score[peaks[-1] - y1]:
            peaks[-1] = absolute
    output = []
    for y in peaks:
        raw_depth = calibration.depth_at(y)
        if not 0 <= raw_depth <= 5000:
            continue
        local_y = y - y1
        external_line = horizontal_line_features(
            gray, (float(left), float(y - 2), float(right), float(y + 2)),
            left_x=max(0, layout.x_min * width), right_x=min(width, layout.x_max * width),
        )
        hypotheses: set[tuple[float, float]] = {(round(raw_depth * 20) / 20, 0.05)}
        for step in (0.1, 0.5, 1.0):
            lower = math.floor(raw_depth / step) * step
            upper = math.ceil(raw_depth / step) * step
            for value in (lower, upper):
                if abs(value - raw_depth) <= max(0.16, step * 0.55):
                    hypotheses.add((round(value, 6), step))
        for rounded_depth, snap_step in sorted(hypotheses):
            features = {
                "source_printed": 0.0,
                "source_graphic": 1.0,
                "source_metadata": 0.0,
                "ocr_confidence": 0.0,
                "view_support": 0.0,
                "view_agreement": 1.0,
                "full_page_support": 0.0,
                "line_left_run": 0.0,
                "line_right_run": float(line_score[local_y]),
                "line_left_dark": 0.0,
                "line_right_dark": float(density[local_y]),
                "external_left_run": external_line["line_left_run"],
                "external_right_run": external_line["line_right_run"],
                "external_left_dark": external_line["line_left_dark"],
                "external_right_dark": external_line["line_right_dark"],
                "texture_change": float(change[local_y]),
                "scale_inliers": min(1.0, calibration.inlier_count / 6),
                "scale_rmse": min(1.0, calibration.rmse_m),
                "normalized_y": y / height,
                "description_x_distance": 1.0,
                "depth_x_distance": 0.0,
                "near_same_y_pair": 0.0,
                "snap_step": snap_step,
                "snap_delta": min(1.0, abs(rounded_depth - raw_depth)),
                "snap_integer": float(abs(rounded_depth - round(rounded_depth)) < 1e-6),
                "snap_half": float(abs(rounded_depth * 2 - round(rounded_depth * 2)) < 1e-6),
                "snap_tenth": float(abs(rounded_depth * 10 - round(rounded_depth * 10)) < 1e-6),
                "printed_line_support": 0.0,
                "printed_pair_support": 0.0,
                "graphic_line_support": float(line_score[local_y]),
                "graphic_change_support": float(change[local_y]),
                "metadata_cross_field": 0.0,
            }
            output.append(DepthBoundaryCandidate(
                value_m=rounded_depth,
                page=page,
                bbox=(float(left), float(y - 2), float(right), float(y + 2)),
                candidate_source="graphic_scale_transition",
                features=features,
                provenance=({
                    "method": "graphic_scale_transition",
                    "raw_depth_m": raw_depth,
                    "snap_step_m": snap_step,
                    "calibration_inliers": calibration.inlier_count,
                    "calibration_rmse_m": calibration.rmse_m,
                    "graphic_column_bbox": [left, y1, right, y2],
                },),
            ))
    return output


def printed_boundary_candidates(
    evidence: Sequence[NumericEvidence], gray: np.ndarray, *, layout: LogPanelLayout,
    boundary_x_hint: float | None = None,
) -> Iterable[DepthBoundaryCandidate]:
    """Create field-aware candidates near explicit depth/description columns."""
    height, width = gray.shape[:2]
    description = layout.anchors.get("description")
    depth = layout.anchors.get("depth")
    if description is None:
        return
    boundary_x = boundary_x_hint if boundary_x_hint is not None else description.center_x - 0.04
    candidate_rows = []
    for item in evidence:
        x = item.center_x / width
        y = item.center_y / height
        description_distance = abs(x - boundary_x)
        depth_distance = abs(x - depth.center_x) if depth else 1.0
        if y < layout.y_min or item.value < 0 or item.value > 5000:
            continue
        # Explicit boundary labels normally sit immediately left of the
        # description field.  Depth-scale labels are handled separately by the
        # calibrated graphic parser and must not become interval boundaries.
        if description_distance > 0.035:
            continue
        candidate_rows.append(item)
    for item in candidate_rows:
        near_pair = any(
            other is not item
            and abs(other.center_y - item.center_y) <= max(18, height * 0.006)
            and abs(other.value - item.value) > 1e-6
            for other in candidate_rows
        )
        line = horizontal_line_features(
            gray, item.bbox,
            left_x=max(0, layout.x_min * width),
            right_x=min(width, (description.center_x + 0.22) * width if description else layout.x_max * width),
        )
        total_views = item.view_support + item.competing_views
        features = {
            "source_printed": 1.0,
            "source_graphic": 0.0,
            "source_metadata": 0.0,
            "ocr_confidence": item.max_confidence,
            "view_support": min(1.0, item.view_support / 5),
            "view_agreement": item.view_support / max(1, total_views),
            "full_page_support": float(item.full_page_support),
            **line,
            "texture_change": 0.0,
            "scale_inliers": 0.0,
            "scale_rmse": 1.0,
            "normalized_y": item.center_y / height,
            "description_x_distance": min(1.0, abs(item.center_x / width - boundary_x) / 0.04),
            "depth_x_distance": min(1.0, abs(item.center_x / width - depth.center_x) / 0.1) if depth else 1.0,
            "near_same_y_pair": float(near_pair),
            "printed_line_support": max(line["line_left_run"], line["line_right_run"]),
            "printed_pair_support": float(near_pair),
            "graphic_line_support": 0.0,
            "graphic_change_support": 0.0,
            "metadata_cross_field": 0.0,
        }
        yield DepthBoundaryCandidate(
            value_m=item.value,
            page=item.page,
            bbox=item.bbox,
            candidate_source="printed_depth",
            features=features,
            provenance=({
                "method": "multiview_numeric_ocr",
                "source_texts": list(item.source_texts),
                "view_support": item.view_support,
                "competing_views": item.competing_views,
            },),
        )


def metadata_final_depth_candidates(
    evidence: Sequence[NumericEvidence], text_regions: Sequence[Mapping[str, object]],
    *, layout: LogPanelLayout, width: int, height: int,
) -> list[DepthBoundaryCandidate]:
    """Find final/total-depth values from header geometry, without a reference."""
    labels = []
    for region in text_regions:
        text = str(region.get("text") or "").strip().lower()
        if "final" not in text and "total" not in text:
            continue
        try:
            bbox = tuple(float(value) for value in region["bbox"])
        except (KeyError, TypeError, ValueError):
            continue
        labels.append((text, bbox))
    output = []
    for item in evidence:
        if item.center_y / height >= layout.y_min or not 0 < item.value <= 5000:
            continue
        best = None
        for label_text, label_bbox in labels:
            label_x, label_y = _center(label_bbox)
            dy = abs(item.center_y - label_y) / height
            dx = (item.center_x - label_x) / width
            if dy <= 0.025 and -0.04 <= dx <= 0.30:
                score = max(0.0, 1.0 - dy / 0.025) * max(0.0, 1.0 - abs(dx - 0.08) / 0.22)
                if best is None or score > best[0]:
                    best = (score, label_text, label_bbox)
        if best is None:
            continue
        score, label_text, label_bbox = best
        features = {
            "source_printed": 0.0,
            "source_graphic": 0.0,
            "source_metadata": 1.0,
            "ocr_confidence": item.max_confidence,
            "view_support": min(1.0, item.view_support / 2),
            "view_agreement": item.view_support / max(1, item.view_support + item.competing_views),
            "full_page_support": float(item.full_page_support),
            "line_left_run": 0.0,
            "line_right_run": 0.0,
            "line_left_dark": 0.0,
            "line_right_dark": 0.0,
            "texture_change": 0.0,
            "scale_inliers": 0.0,
            "scale_rmse": 1.0,
            "normalized_y": item.center_y / height,
            "description_x_distance": 1.0,
            "depth_x_distance": 1.0,
            "near_same_y_pair": 0.0,
            "metadata_label_score": score,
            "printed_line_support": 0.0,
            "printed_pair_support": 0.0,
            "graphic_line_support": 0.0,
            "graphic_change_support": 0.0,
            "metadata_cross_field": 0.0,
        }
        output.append(DepthBoundaryCandidate(
            value_m=item.value,
            page=item.page,
            bbox=item.bbox,
            candidate_source="metadata_final_depth",
            features=features,
            provenance=({
                "method": "header_label_geometry",
                "label_text": label_text,
                "label_bbox": list(label_bbox),
                "source_texts": list(item.source_texts),
            },),
        ))
    return output


class LogisticCandidateRanker:
    """Small deterministic probabilistic ranker with no heavyweight runtime."""

    def __init__(self, feature_names: Sequence[str]):
        self.feature_names = tuple(feature_names)
        self.mean = np.zeros(len(self.feature_names), dtype=float)
        self.scale = np.ones(len(self.feature_names), dtype=float)
        self.weights = np.zeros(len(self.feature_names), dtype=float)
        self.bias = 0.0

    def _matrix(self, candidates: Sequence[DepthBoundaryCandidate]) -> np.ndarray:
        return np.asarray([
            [float(candidate.features.get(name, 0.0)) for name in self.feature_names]
            for candidate in candidates
        ], dtype=float)

    def fit(
        self, candidates: Sequence[DepthBoundaryCandidate], labels: Sequence[int],
        *, iterations: int = 1200, learning_rate: float = 0.04, l2: float = 0.02,
    ) -> "LogisticCandidateRanker":
        matrix = self._matrix(candidates)
        target = np.asarray(labels, dtype=float)
        if len(matrix) == 0 or len(matrix) != len(target) or len(set(target.tolist())) < 2:
            raise ValueError("ranker training requires non-empty positive and negative candidates")
        self.mean = matrix.mean(axis=0)
        self.scale = matrix.std(axis=0)
        self.scale[self.scale < 1e-8] = 1.0
        normalized = (matrix - self.mean) / self.scale
        positive_weight = max(1.0, float((target == 0).sum()) / max(1, int((target == 1).sum())))
        sample_weight = np.where(target == 1, positive_weight, 1.0)
        for _ in range(iterations):
            logits = np.clip(normalized @ self.weights + self.bias, -30, 30)
            probability = 1.0 / (1.0 + np.exp(-logits))
            error = (probability - target) * sample_weight
            self.weights -= learning_rate * ((normalized.T @ error) / sample_weight.sum() + l2 * self.weights)
            self.bias -= learning_rate * float(error.sum() / sample_weight.sum())
        return self

    def predict_proba(self, candidates: Sequence[DepthBoundaryCandidate]) -> np.ndarray:
        if not candidates:
            return np.asarray([], dtype=float)
        normalized = (self._matrix(candidates) - self.mean) / self.scale
        logits = np.clip(normalized @ self.weights + self.bias, -30, 30)
        return 1.0 / (1.0 + np.exp(-logits))

    def to_dict(self) -> dict[str, object]:
        return {
            "feature_names": list(self.feature_names),
            "mean": self.mean.tolist(),
            "scale": self.scale.tolist(),
            "weights": self.weights.tolist(),
            "bias": self.bias,
        }

    @classmethod
    def from_dict(cls, values: Mapping[str, object]) -> "LogisticCandidateRanker":
        output = cls(values["feature_names"])
        output.mean = np.asarray(values["mean"], dtype=float)
        output.scale = np.asarray(values["scale"], dtype=float)
        output.weights = np.asarray(values["weights"], dtype=float)
        output.bias = float(values["bias"])
        return output
