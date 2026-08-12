"""Transparent surface interpolation and controlled boundary perturbations."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from math import hypot, sqrt
from statistics import mean
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class SurfacePoint:
    x: float
    y: float
    elevation: float
    borehole_id: str


def idw_predict(
    points: Sequence[SurfacePoint],
    query_x: float,
    query_y: float,
    power: float = 2.0,
) -> float:
    if not points:
        raise ValueError("IDW requires at least one point")
    if power <= 0:
        raise ValueError("IDW power must be positive")
    distances = [(hypot(point.x - query_x, point.y - query_y), point) for point in points]
    coincident = [point.elevation for distance, point in distances if distance == 0]
    if coincident:
        return mean(coincident)
    weights = [(1 / distance**power, point.elevation) for distance, point in distances]
    return sum(weight * elevation for weight, elevation in weights) / sum(weight for weight, _ in weights)


def boundary_surface_points(
    records: Sequence[Mapping[str, Any]],
    interval_index: int,
    boundary: str = "bottom_depth_m",
) -> list[SurfacePoint]:
    if boundary not in {"top_depth_m", "bottom_depth_m"}:
        raise ValueError("boundary must be top_depth_m or bottom_depth_m")
    points = []
    for record in records:
        borehole = record["borehole"]
        if interval_index >= len(record.get("intervals", ())):
            continue
        x = borehole["x_coordinate"]["value"]
        y = borehole["y_coordinate"]["value"]
        collar = borehole["collar_elevation_m"]["value"]
        depth = record["intervals"][interval_index][boundary]["value"]
        if None in (x, y, collar, depth):
            continue
        points.append(SurfacePoint(
            float(x), float(y), float(collar) - float(depth),
            str(borehole["borehole_id"]["value"]),
        ))
    return points


def perturb_interval_boundaries(
    records: Sequence[Mapping[str, Any]],
    magnitude_m: float,
    seed: int,
) -> list[dict[str, Any]]:
    if magnitude_m < 0:
        raise ValueError("perturbation magnitude must be non-negative")
    rng = random.Random(seed)
    perturbed = copy.deepcopy(records)
    for record in perturbed:
        intervals = record.get("intervals", ())
        # Perturb internal shared boundaries once, then restore interval
        # continuity and recompute thickness. First top and final bottom remain.
        for index in range(len(intervals) - 1):
            boundary = float(intervals[index]["bottom_depth_m"]["value"])
            delta = rng.choice((-magnitude_m, magnitude_m)) if magnitude_m else 0.0
            revised = boundary + delta
            intervals[index]["bottom_depth_m"]["value"] = revised
            intervals[index + 1]["top_depth_m"]["value"] = revised
        for interval in intervals:
            top = interval["top_depth_m"]["value"]
            bottom = interval["bottom_depth_m"]["value"]
            if top is not None and bottom is not None:
                interval["thickness_m"]["value"] = float(bottom) - float(top)
    return perturbed


def surface_error_metrics(reference: Sequence[float], prediction: Sequence[float]) -> dict[str, float | int | None]:
    if len(reference) != len(prediction):
        raise ValueError("surface arrays must have equal length")
    if not reference:
        return {"count": 0, "mae_m": None, "rmse_m": None, "max_abs_error_m": None}
    errors = [float(predicted) - float(expected) for expected, predicted in zip(reference, prediction)]
    return {
        "count": len(errors),
        "mae_m": mean(abs(error) for error in errors),
        "rmse_m": sqrt(mean(error**2 for error in errors)),
        "max_abs_error_m": max(abs(error) for error in errors),
    }
