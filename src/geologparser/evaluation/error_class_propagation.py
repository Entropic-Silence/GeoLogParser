"""Controlled error-class injection for ordered borehole boundaries.

The utilities in this module deliberately separate numeric boundary error,
coordinate error, spatial-support loss, and sequence-topology error.  They do
not repair an injected record with reference values before downstream scoring.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from statistics import mean, stdev
from typing import Any, Iterable, Sequence

from .error_propagation import SurfacePoint, idw_predict, surface_error_metrics


@dataclass(frozen=True)
class OrderedBoundaryRecord:
    record_id: str
    x: float
    y: float
    collar_elevation_m: float
    boundaries_m: tuple[float | None, ...]


def convex_hull(points: Iterable[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(origin, first, second):
        return (
            (first[0] - origin[0]) * (second[1] - origin[1])
            - (first[1] - origin[1]) * (second[0] - origin[0])
        )

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def point_in_convex_polygon(
    point: tuple[float, float], polygon: Sequence[tuple[float, float]],
) -> bool:
    if len(polygon) < 3:
        return True
    signs = []
    for first, second in zip(polygon, tuple(polygon[1:]) + (polygon[0],)):
        value = (
            (second[0] - first[0]) * (point[1] - first[1])
            - (second[1] - first[1]) * (point[0] - first[0])
        )
        if abs(value) > 1e-9:
            signs.append(value > 0)
    return not signs or all(value == signs[0] for value in signs)


def fixed_reference_grid(
    points: Sequence[SurfacePoint], size: int,
) -> list[tuple[float, float]]:
    if size < 2:
        raise ValueError("grid size must be at least two")
    hull = convex_hull((point.x, point.y) for point in points)
    if len(hull) < 3:
        return [(point.x, point.y) for point in points]
    xs = [point.x for point in points]
    ys = [point.y for point in points]
    output = []
    for row in range(size):
        y = min(ys) + (max(ys) - min(ys)) * row / (size - 1)
        for column in range(size):
            x = min(xs) + (max(xs) - min(xs)) * column / (size - 1)
            if point_in_convex_polygon((x, y), hull):
                output.append((x, y))
    return output


def _sample_count(population: int, fraction: float) -> int:
    if not 0 < fraction <= 1:
        raise ValueError("affected fraction must be in (0, 1]")
    return min(population, max(1, round(population * fraction)))


def inject_error_class(
    records: Sequence[OrderedBoundaryRecord],
    error_type: str,
    parameter: float,
    seed: int,
    *,
    affected_fraction: float = 0.25,
) -> tuple[list[OrderedBoundaryRecord], list[dict[str, Any]]]:
    """Inject one error class and return changed records plus an audit trail.

    For numeric and coordinate errors, ``parameter`` is a magnitude in metres
    and ``affected_fraction`` controls prevalence.  For missing/merged/split/
    duplicate errors, ``parameter`` itself is the affected-document fraction.
    """

    supported = {
        "boundary_shift", "coordinate_shift", "missing_boundary",
        "merged_layer", "split_layer", "duplicate_boundary",
    }
    if error_type not in supported:
        raise ValueError(f"unsupported error type: {error_type}")
    if parameter <= 0:
        raise ValueError("error parameter must be positive")
    rng = random.Random(seed)
    changed = copy.deepcopy(list(records))
    audit: list[dict[str, Any]] = []

    if error_type == "boundary_shift":
        candidates: list[tuple[int, int, tuple[int, ...]]] = []
        for record_index, record in enumerate(changed):
            values = record.boundaries_m
            for boundary_index, value in enumerate(values):
                if value is None:
                    continue
                directions = []
                previous = 0.0 if boundary_index == 0 else values[boundary_index - 1]
                following = values[boundary_index + 1] if boundary_index + 1 < len(values) else None
                if previous is not None and value - parameter > previous:
                    directions.append(-1)
                if following is None or value + parameter < following:
                    directions.append(1)
                if directions:
                    candidates.append((record_index, boundary_index, tuple(directions)))
        count = _sample_count(len(candidates), affected_fraction)
        for record_index, boundary_index, directions in rng.sample(candidates, count):
            record = changed[record_index]
            before = float(record.boundaries_m[boundary_index])
            direction = rng.choice(directions)
            values = list(record.boundaries_m)
            values[boundary_index] = before + direction * parameter
            changed[record_index] = OrderedBoundaryRecord(
                record.record_id, record.x, record.y, record.collar_elevation_m,
                tuple(values),
            )
            audit.append({
                "record_id": record.record_id, "operation": error_type,
                "boundary_index": boundary_index + 1, "before_m": before,
                "after_m": values[boundary_index], "delta_m": direction * parameter,
            })
        return changed, audit

    if error_type == "coordinate_shift":
        count = _sample_count(len(changed), affected_fraction)
        for record_index in rng.sample(range(len(changed)), count):
            record = changed[record_index]
            angle = rng.random() * 2 * pi
            dx, dy = parameter * cos(angle), parameter * sin(angle)
            changed[record_index] = OrderedBoundaryRecord(
                record.record_id, record.x + dx, record.y + dy,
                record.collar_elevation_m, record.boundaries_m,
            )
            audit.append({
                "record_id": record.record_id, "operation": error_type,
                "before_xy": [record.x, record.y],
                "after_xy": [record.x + dx, record.y + dy],
                "dx_m": dx, "dy_m": dy, "distance_m": parameter,
            })
        return changed, audit

    eligible = [index for index, record in enumerate(changed) if record.boundaries_m]
    if error_type == "merged_layer":
        eligible = [index for index in eligible if len(changed[index].boundaries_m) >= 2]
    count = _sample_count(len(eligible), parameter)
    for record_index in rng.sample(eligible, count):
        record = changed[record_index]
        values = list(record.boundaries_m)
        if error_type == "missing_boundary":
            boundary_index = rng.randrange(len(values))
            before = values[boundary_index]
            values[boundary_index] = None
            detail = {"boundary_index": boundary_index + 1, "before_m": before}
        elif error_type == "merged_layer":
            # Removing one boundary merges the intervals on either side and
            # shifts all deeper position-indexed boundaries by one slot.
            boundary_index = rng.randrange(len(values) - 1)
            before = values.pop(boundary_index)
            detail = {"boundary_index": boundary_index + 1, "removed_m": before}
        elif error_type == "split_layer":
            interval_index = rng.randrange(len(values))
            top = 0.0 if interval_index == 0 else float(values[interval_index - 1])
            bottom = float(values[interval_index])
            inserted = (top + bottom) / 2
            values.insert(interval_index, inserted)
            detail = {"boundary_index": interval_index + 1, "inserted_m": inserted}
        else:  # duplicate_boundary
            boundary_index = rng.randrange(len(values))
            duplicate = values[boundary_index]
            values.insert(boundary_index, duplicate)
            detail = {"boundary_index": boundary_index + 1, "duplicated_m": duplicate}
        changed[record_index] = OrderedBoundaryRecord(
            record.record_id, record.x, record.y, record.collar_elevation_m,
            tuple(values),
        )
        audit.append({"record_id": record.record_id, "operation": error_type, **detail})
    return changed, audit


def prepare_reference_surfaces(
    records: Sequence[OrderedBoundaryRecord], grid_size: int,
) -> list[dict[str, Any]]:
    prepared = []
    maximum = max(len(record.boundaries_m) for record in records)
    for boundary_index in range(maximum):
        eligible = [
            record for record in records
            if len(record.boundaries_m) > boundary_index
            and record.boundaries_m[boundary_index] is not None
        ]
        points = [
            SurfacePoint(
                record.x, record.y,
                record.collar_elevation_m - float(record.boundaries_m[boundary_index]),
                record.record_id,
            )
            for record in eligible
        ]
        queries = fixed_reference_grid(points, grid_size)
        prepared.append({
            "boundary_index": boundary_index,
            "record_ids": [record.record_id for record in eligible],
            "reference_depth_by_id": {
                record.record_id: float(record.boundaries_m[boundary_index])
                for record in eligible
            },
            "queries": queries,
            "surface": [idw_predict(points, x, y) for x, y in queries],
        })
    return prepared


def evaluate_error_propagation(
    reference: Sequence[OrderedBoundaryRecord],
    prediction: Sequence[OrderedBoundaryRecord],
    prepared_surfaces: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    reference_by_id = {record.record_id: record for record in reference}
    prediction_by_id = {record.record_id: record for record in prediction}
    if reference_by_id.keys() != prediction_by_id.keys():
        raise ValueError("reference and prediction record IDs must match")

    boundary_errors: list[float] = []
    surface_reference: list[float] = []
    surface_prediction: list[float] = []
    predicted_observations = 0
    reference_observations = 0
    per_boundary = []
    for prepared in prepared_surfaces:
        index = prepared["boundary_index"]
        points = []
        errors = []
        for record_id in prepared["record_ids"]:
            record = prediction_by_id[record_id]
            if index >= len(record.boundaries_m) or record.boundaries_m[index] is None:
                continue
            depth = float(record.boundaries_m[index])
            points.append(SurfacePoint(
                record.x, record.y, record.collar_elevation_m - depth, record_id,
            ))
            errors.append(abs(depth - prepared["reference_depth_by_id"][record_id]))
        predicted = [
            idw_predict(points, x, y) for x, y in prepared["queries"]
        ] if points else []
        surface = (
            surface_error_metrics(prepared["surface"], predicted)
            if len(predicted) == len(prepared["surface"])
            else {"count": 0, "mae_m": None, "rmse_m": None, "max_abs_error_m": None}
        )
        reference_count = len(prepared["record_ids"])
        predicted_observations += len(points)
        reference_observations += reference_count
        boundary_errors.extend(errors)
        if predicted:
            surface_reference.extend(prepared["surface"])
            surface_prediction.extend(predicted)
        per_boundary.append({
            "boundary_index": index + 1,
            "reference_point_count": reference_count,
            "predicted_point_count": len(points),
            "coverage": len(points) / reference_count,
            "boundary_mae_m": mean(errors) if errors else None,
            "surface_error": surface,
        })

    topology_mismatch = 0
    count_difference = 0
    missing_slots = 0
    ordering_violations = 0
    positional_mismatches = 0
    for record_id, expected in reference_by_id.items():
        observed = prediction_by_id[record_id]
        expected_count = len(expected.boundaries_m)
        available = [value for value in observed.boundaries_m if value is not None]
        count_difference += abs(len(available) - expected_count)
        missing_slots += sum(value is None for value in observed.boundaries_m)
        violations = sum(
            float(second) <= float(first)
            for first, second in zip(available, available[1:])
        )
        ordering_violations += violations
        positional_mismatches += sum(
            index >= len(observed.boundaries_m)
            or observed.boundaries_m[index] is None
            or abs(float(observed.boundaries_m[index]) - float(value)) > 1e-9
            for index, value in enumerate(expected.boundaries_m)
        )
        if len(available) != expected_count or violations or any(
            value is None for value in observed.boundaries_m
        ):
            topology_mismatch += 1

    return {
        "reference_boundary_observation_count": reference_observations,
        "predicted_boundary_observation_count": predicted_observations,
        "spatial_support_coverage": predicted_observations / reference_observations,
        "boundary_mae_m": mean(boundary_errors) if boundary_errors else None,
        "surface_error": surface_error_metrics(surface_reference, surface_prediction),
        "topology": {
            "mismatched_document_count": topology_mismatch,
            "mismatched_document_rate": topology_mismatch / len(reference),
            "boundary_count_absolute_difference": count_difference,
            "missing_slot_count": missing_slots,
            "ordering_violation_count": ordering_violations,
            "positional_mismatch_count": positional_mismatches,
        },
        "per_boundary": per_boundary,
    }


def summarize_scalar(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "mean": None, "std": None, "ci95_normal": None}
    average = mean(values)
    deviation = stdev(values) if len(values) > 1 else None
    half_width = 1.96 * deviation / sqrt(len(values)) if deviation is not None else None
    return {
        "n": len(values), "mean": average, "std": deviation,
        "ci95_normal": (
            [average - half_width, average + half_width]
            if half_width is not None else None
        ),
    }
