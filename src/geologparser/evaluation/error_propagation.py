"""Transparent surface interpolation and controlled boundary perturbations."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from math import hypot, sqrt
from statistics import mean, stdev
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


def spatial_model_readiness(
    records: Sequence[Mapping[str, Any]], interval_index: int,
    boundary: str = "bottom_depth_m", minimum_points: int = 3,
) -> dict[str, Any]:
    """Gate real surface modelling on spatial and human stratigraphic evidence."""
    if minimum_points < 3:
        raise ValueError("minimum_points must be at least 3 for a surface")
    if boundary not in {"top_depth_m", "bottom_depth_m"}:
        raise ValueError("boundary must be top_depth_m or bottom_depth_m")
    eligible, rejected = [], []
    coordinate_systems = set()
    for record in records:
        document_id = str(record["document"]["document_id"])
        reasons = []
        borehole = record["borehole"]
        for name in ("x_coordinate", "y_coordinate", "coordinate_system"):
            if borehole[name].get("value") is None:
                reasons.append(f"MISSING_{name.upper()}")
        system = borehole["coordinate_system"].get("value")
        if system is not None:
            coordinate_systems.add(str(system))
        collar = borehole["collar_elevation_m"]
        if collar.get("value") is None:
            reasons.append("MISSING_COLLAR_ELEVATION")
        elif collar.get("validation_status") != "human_verified":
            reasons.append("COLLAR_ELEVATION_NOT_HUMAN_VERIFIED")
        intervals = record.get("intervals", [])
        if interval_index >= len(intervals):
            reasons.append("MISSING_TARGET_INTERVAL")
        else:
            envelope = intervals[interval_index][boundary]
            if envelope.get("value") is None:
                reasons.append("MISSING_TARGET_BOUNDARY")
            elif envelope.get("validation_status") != "human_verified":
                reasons.append("TARGET_BOUNDARY_NOT_HUMAN_VERIFIED")
        if reasons:
            rejected.append({"document_id": document_id, "reasons": reasons})
        else:
            eligible.append(document_id)
    global_reasons = []
    if len(coordinate_systems) > 1:
        global_reasons.append("MIXED_COORDINATE_SYSTEMS")
    if len(eligible) < minimum_points:
        global_reasons.append("INSUFFICIENT_ELIGIBLE_POINTS")
    return {
        "ready": not global_reasons and len(eligible) >= minimum_points,
        "minimum_points": minimum_points, "eligible_count": len(eligible),
        "eligible_document_ids": eligible, "rejected": rejected,
        "coordinate_systems": sorted(coordinate_systems),
        "global_reasons": global_reasons,
        "coordinate_note": "source-provided coordinate status is retained separately; readiness does not certify survey accuracy",
    }


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


def aggregate_repeated_metrics(
    repetitions: Sequence[Mapping[str, float | int | None]],
    confidence_z: float = 1.96,
) -> dict[str, Any]:
    """Aggregate repeated runs with normal-approximation CIs, explicitly named.

    This utility does not imply independent geological samples. The caller must
    state what was repeated (for example, random perturbation seeds).
    """
    if confidence_z <= 0:
        raise ValueError("confidence_z must be positive")
    output: dict[str, Any] = {"repetitions": len(repetitions), "confidence_z": confidence_z}
    for key in ("mae_m", "rmse_m", "max_abs_error_m"):
        values = [float(item[key]) for item in repetitions if item.get(key) is not None]
        if not values:
            output[key] = {"n": 0, "mean": None, "std": None, "ci95_normal": None}
            continue
        average = mean(values)
        standard_deviation = stdev(values) if len(values) > 1 else None
        half_width = confidence_z * standard_deviation / sqrt(len(values)) if standard_deviation is not None else None
        output[key] = {
            "n": len(values),
            "mean": average,
            "std": standard_deviation,
            "ci95_normal": [average - half_width, average + half_width] if half_width is not None else None,
        }
    return output
