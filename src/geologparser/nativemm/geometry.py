"""Deterministic geometry handoff for NativeMM structural predictions."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class GeometryDecodeResult:
    boundaries_m: tuple[float, ...]
    depth_per_y: float | None
    intercept_m: float | None
    scale_rmse_m: float | None
    scale_inliers: int
    rejected_boundary_count: int
    warnings: tuple[str, ...]


def _fit_line(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    if len(points) < 2:
        return None
    mean_y = sum(row[0] for row in points) / len(points)
    mean_depth = sum(row[1] for row in points) / len(points)
    denominator = sum((row[0] - mean_y) ** 2 for row in points)
    if denominator <= 1e-12:
        return None
    slope = sum((y - mean_y) * (depth - mean_depth) for y, depth in points) / denominator
    if slope <= 0:
        return None
    return slope, mean_depth - slope * mean_y


def _robust_scale(points: list[tuple[float, float]], residual_tolerance_m: float) -> tuple[float, float, list[int]] | None:
    """Small deterministic RANSAC suitable for the sparse depth scales here."""
    if len(points) < 2:
        return None
    best: tuple[tuple[int, float], float, float, list[int]] | None = None
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            y0, d0 = points[left]
            y1, d1 = points[right]
            if abs(y1 - y0) <= 1e-9:
                continue
            slope = (d1 - d0) / (y1 - y0)
            if slope <= 0:
                continue
            intercept = d0 - slope * y0
            residuals = [abs(depth - (slope * y + intercept)) for y, depth in points]
            inliers = [index for index, value in enumerate(residuals) if value <= residual_tolerance_m]
            if len(inliers) < 2:
                continue
            key = (len(inliers), -sum(residuals[index] for index in inliers))
            if best is None or key > best[0]:
                best = (key, slope, intercept, inliers)
    if best is None:
        return None
    fitted = _fit_line([points[index] for index in best[3]])
    if fitted is None:
        return None
    return fitted[0], fitted[1], best[3]


def decode_depth_geometry(
    boundary_y: Iterable[float],
    scale_points: Iterable[tuple[float, float]],
    *,
    residual_tolerance_m: float = 0.10,
    minimum_gap_m: float = 0.005,
    final_depth_m: float | None = None,
) -> GeometryDecodeResult:
    """Convert grounded boundary positions to depths without generative guessing.

    Coordinates may be pixels or normalized page coordinates, provided the
    boundary and scale-point coordinates use the same space.
    """
    ys = sorted(float(value) for value in boundary_y if math.isfinite(float(value)))
    points = sorted(
        (float(y), float(depth))
        for y, depth in scale_points
        if math.isfinite(float(y)) and math.isfinite(float(depth))
    )
    warnings: list[str] = []
    robust = _robust_scale(points, residual_tolerance_m)
    if robust is None:
        return GeometryDecodeResult((), None, None, None, 0, len(ys), ("DEPTH_SCALE_UNAVAILABLE",))
    slope, intercept, inlier_indices = robust
    residuals = [abs(points[index][1] - (slope * points[index][0] + intercept)) for index in inlier_indices]
    rmse = math.sqrt(sum(value * value for value in residuals) / len(residuals))
    decoded = [slope * y + intercept for y in ys]
    accepted: list[float] = []
    rejected = 0
    for value in decoded:
        if value < -residual_tolerance_m:
            rejected += 1
            continue
        value = max(0.0, value)
        if final_depth_m is not None and value > final_depth_m + residual_tolerance_m:
            rejected += 1
            continue
        if accepted and value <= accepted[-1] + minimum_gap_m:
            rejected += 1
            continue
        accepted.append(value)
    if rejected:
        warnings.append("NON_MONOTONIC_OR_OUT_OF_RANGE_BOUNDARIES_REJECTED")
    if rmse > residual_tolerance_m / 2:
        warnings.append("DEPTH_SCALE_HIGH_RESIDUAL")
    return GeometryDecodeResult(
        tuple(accepted), slope, intercept, rmse, len(inlier_indices), rejected, tuple(warnings),
    )
