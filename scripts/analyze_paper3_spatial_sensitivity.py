#!/usr/bin/env python3
"""Reanalyse frozen Swissgeol outputs as a spatial-sensitivity diagnostic.

The script separates full-support and matched-subset comparisons, quantifies
spatial support, sweeps transparent IDW choices, and performs leave-one-
borehole-out diagnostics.  It does not change upstream predictions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(
    "/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v003/"
    "gold_interval_manifest_heldout_v003.jsonl"
)
DEFAULT_PREDICTIONS = ROOT / "results/2026-08-16/P3_SWISSGEOL_RISK_AWARE_DOWNSTREAM_INPUT_001/predictions.jsonl"


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def summary(values: list[float]) -> dict:
    return {
        "count": len(values),
        "mean": sum(values) / len(values) if values else None,
        "median": percentile(values, 0.5),
        "p90": percentile(values, 0.9),
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
    }


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(origin, left, right):
        return (left[0] - origin[0]) * (right[1] - origin[1]) - (left[1] - origin[1]) * (right[0] - origin[0])

    lower = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def polygon_area(polygon: list[tuple[float, float]]) -> float:
    if len(polygon) < 3:
        return 0.0
    # Evaluate the shoelace sum in a local frame.  Projected survey
    # coordinates can be O(10^6) m, and subtracting large cross-products
    # otherwise makes the reported area depend on an arbitrary map origin.
    origin_x, origin_y = polygon[0]
    local = [(x - origin_x, y - origin_y) for x, y in polygon]
    return abs(sum(
        local[index][0] * local[(index + 1) % len(local)][1]
        - local[(index + 1) % len(local)][0] * local[index][1]
        for index in range(len(local))
    )) / 2


def inside(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    if len(polygon) < 3:
        return point in polygon
    extent = max(
        max(x for x, _ in polygon) - min(x for x, _ in polygon),
        max(y for _, y in polygon) - min(y for _, y in polygon),
        1.0,
    )
    cross_tolerance = max(1e-9, extent * extent * 1e-12)
    signs = []
    for left, right in zip(polygon, polygon[1:] + polygon[:1]):
        value = (right[0] - left[0]) * (point[1] - left[1]) - (right[1] - left[1]) * (point[0] - left[0])
        if abs(value) > cross_tolerance:
            signs.append(value > 0)
    return not signs or all(value == signs[0] for value in signs)


def make_grid(points: list[tuple[float, float]], size: int) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) < 3:
        return unique
    # Construct and clip the grid in a local coordinate frame so that hull
    # membership is invariant to removal of an absolute survey origin.
    origin_x = min(point[0] for point in unique)
    origin_y = min(point[1] for point in unique)
    local = [(x - origin_x, y - origin_y) for x, y in unique]
    hull = convex_hull(local)
    if len(hull) < 3:
        return unique
    xs = [point[0] for point in local]
    ys = [point[1] for point in local]
    output = []
    for row in range(size):
        y = min(ys) + (max(ys) - min(ys)) * row / (size - 1)
        for column in range(size):
            x = min(xs) + (max(xs) - min(xs)) * column / (size - 1)
            if inside((x, y), hull):
                output.append((x + origin_x, y + origin_y))
    return output


def idw(points: list[tuple[float, float, float]], query: tuple[float, float], power: float, neighbours: int | None) -> float:
    distances = []
    for x, y, value in points:
        distance = math.hypot(x - query[0], y - query[1])
        # Treat sub-micrometre coordinate differences as the same support
        # location.  This keeps the diagnostic invariant to the documented
        # rigid coordinate transform and avoids a near-zero IDW weight
        # singularity after decimal serialization.
        if distance <= 1e-6:
            return value
        distances.append((distance, value))
    if not distances:
        raise ValueError("IDW requires at least one point")
    distances.sort()
    if neighbours is not None:
        distances = distances[:neighbours]
    weights = [(1 / distance ** power, value) for distance, value in distances]
    denominator = sum(weight for weight, _ in weights)
    return sum(weight * value for weight, value in weights) / denominator


def boundary_value(record: dict, variant: str, boundary: int) -> float | None:
    rows = record[variant]
    if len(rows) <= boundary:
        return None
    return record["collar"] - float(rows[boundary]["bottom_depth_m"])


def spatial_points(records: list[dict], variant: str, boundary: int) -> list[tuple[float, float, float]]:
    points = []
    for record in records:
        value = boundary_value(record, variant, boundary)
        if value is not None:
            points.append((record["x"], record["y"], value))
    return points


def nearest_neighbour_distances(points: list[tuple[float, float]]) -> list[float]:
    return [
        min(math.hypot(x - other_x, y - other_y) for other_x, other_y in points if (x, y) != (other_x, other_y))
        for x, y in points
    ] if len(set(points)) > 1 else []


def support_diagnostics(records: list[dict], variant: str, boundary: int, grid_size: int) -> dict:
    eligible = [record for record in records if len(record["reference"]) > boundary]
    reference_xy = [(record["x"], record["y"]) for record in eligible]
    available = [record for record in eligible if boundary_value(record, variant, boundary) is not None]
    available_xy = [(record["x"], record["y"]) for record in available]
    reference_area = polygon_area(convex_hull(reference_xy))
    available_area = polygon_area(convex_hull(available_xy))
    nearest = nearest_neighbour_distances(available_xy)
    expected_random_nn = 0.5 * math.sqrt(available_area / len(available_xy)) if available_area > 0 and available_xy else None
    queries = make_grid(reference_xy, grid_size)
    grid_distances = [
        min(math.hypot(x - ox, y - oy) for ox, oy in available_xy)
        for x, y in queries
    ] if available_xy else []
    return {
        "boundary_index": boundary + 1,
        "variant": variant,
        "reference_point_count": len(eligible),
        "effective_point_count": len(available),
        "point_coverage": len(available) / len(eligible) if eligible else None,
        "reference_convex_hull_area_m2": reference_area,
        "accepted_convex_hull_area_m2": available_area,
        "convex_hull_area_ratio": available_area / reference_area if reference_area else None,
        "nearest_neighbour_distance_m": summary(nearest),
        "clark_evans_nearest_neighbour_ratio_diagnostic": (
            (sum(nearest) / len(nearest)) / expected_random_nn
            if nearest and expected_random_nn else None
        ),
        "grid_to_nearest_observation_distance_m": summary(grid_distances),
        "grid_size": grid_size,
    }


def layer_diagnostic(
    records: list[dict],
    layer: int,
    variant: str,
    power: float,
    neighbours: int | None,
    grid_size: int,
) -> dict | None:
    eligible = [record for record in records if len(record["reference"]) > layer + 1]
    if not eligible:
        return None
    queries = make_grid([(record["x"], record["y"]) for record in eligible], grid_size)
    area = polygon_area(convex_hull([(record["x"], record["y"]) for record in eligible]))
    ref_top = spatial_points(eligible, "reference", layer)
    ref_bottom = spatial_points(eligible, "reference", layer + 1)
    pred_top = spatial_points(eligible, variant, layer)
    pred_bottom = spatial_points(eligible, variant, layer + 1)
    if not pred_top or not pred_bottom or not queries:
        return None
    reference_thickness = [
        idw(ref_top, query, power, neighbours) - idw(ref_bottom, query, power, neighbours)
        for query in queries
    ]
    predicted_thickness = [
        idw(pred_top, query, power, neighbours) - idw(pred_bottom, query, power, neighbours)
        for query in queries
    ]
    errors = [abs(reference - predicted) for reference, predicted in zip(reference_thickness, predicted_thickness)]
    reference_volume = area * sum(reference_thickness) / len(reference_thickness)
    predicted_volume = area * sum(predicted_thickness) / len(predicted_thickness)
    return {
        "layer_index": layer + 1,
        "variant": variant,
        "domain_record_count": len(eligible),
        "query_count": len(queries),
        "domain_area_m2": area,
        "top_support": len(pred_top) / len(eligible),
        "bottom_support": len(pred_bottom) / len(eligible),
        "thickness_mae_m": sum(errors) / len(errors),
        "thickness_rmse_m": math.sqrt(sum(error * error for error in errors) / len(errors)),
        "reference_volume_m3": reference_volume,
        "predicted_volume_m3": predicted_volume,
        "absolute_volume_error_m3": abs(predicted_volume - reference_volume),
        "relative_absolute_volume_error": abs(predicted_volume - reference_volume) / abs(reference_volume) if reference_volume else None,
        "negative_thickness_query_fraction": sum(value < 0 for value in predicted_thickness) / len(predicted_thickness),
    }


def aggregate_layers(rows: list[dict]) -> dict:
    valid = [row for row in rows if row is not None]
    reference_volume = sum(abs(row["reference_volume_m3"]) for row in valid)
    return {
        "layer_count": len(valid),
        "mean_thickness_mae_m": sum(row["thickness_mae_m"] for row in valid) / len(valid) if valid else None,
        "sum_absolute_volume_error_m3": sum(row["absolute_volume_error_m3"] for row in valid) if valid else None,
        "sum_reference_volume_m3": reference_volume if valid else None,
        "relative_absolute_volume_error": sum(row["absolute_volume_error_m3"] for row in valid) / reference_volume if reference_volume else None,
        "mean_top_support": sum(row["top_support"] for row in valid) / len(valid) if valid else None,
        "mean_bottom_support": sum(row["bottom_support"] for row in valid) / len(valid) if valid else None,
        "layers_with_negative_thickness": sum(row["negative_thickness_query_fraction"] > 0 for row in valid),
    }


def compare(records: list[dict], variants: list[str], power: float, neighbours: int | None, grid_size: int) -> dict:
    max_layers = max(len(record["reference"]) for record in records) - 1
    output = {}
    for variant in variants:
        rows = [
            layer_diagnostic(records, layer, variant, power, neighbours, grid_size)
            for layer in range(max_layers)
        ]
        output[variant] = {"aggregate": aggregate_layers(rows), "layers": [row for row in rows if row]}
    return output


def loocv(records: list[dict], variants: list[str], power: float, neighbours: int | None) -> dict:
    max_boundaries = max(len(record["reference"]) for record in records)
    output = {}
    for variant in variants:
        errors = []
        by_boundary = []
        for boundary in range(max_boundaries):
            boundary_errors = []
            eligible = [record for record in records if len(record["reference"]) > boundary]
            for target in eligible:
                training = [record for record in eligible if record["record_id"] != target["record_id"]]
                points = spatial_points(training, variant, boundary)
                if not points:
                    continue
                prediction = idw(points, (target["x"], target["y"]), power, neighbours)
                reference = boundary_value(target, "reference", boundary)
                boundary_errors.append(abs(prediction - reference))
            errors.extend(boundary_errors)
            by_boundary.append({"boundary_index": boundary + 1, "absolute_error_m": summary(boundary_errors)})
        output[variant] = {"absolute_error_m": summary(errors), "by_boundary": by_boundary}
    return output


def document_boundary_errors(records: list[dict], variant: str) -> dict[str, list[float]]:
    output = {}
    for record in records:
        errors = []
        for boundary in range(min(len(record["reference"]), len(record[variant]))):
            errors.append(abs(
                boundary_value(record, variant, boundary)
                - boundary_value(record, "reference", boundary)
            ))
        output[record["record_id"]] = errors
    return output


def document_bootstrap(records: list[dict], variants: list[str], repetitions: int, rng: random.Random) -> dict:
    errors = {variant: document_boundary_errors(records, variant) for variant in variants}
    ids = [record["record_id"] for record in records]
    output = {}
    for variant in variants:
        observed_values = [value for record_id in ids for value in errors[variant][record_id]]
        distribution = []
        for _ in range(repetitions):
            sample_ids = [ids[rng.randrange(len(ids))] for _ in ids]
            values = [value for record_id in sample_ids for value in errors[variant][record_id]]
            distribution.append(sum(values) / len(values) if values else 0.0)
        output[variant] = {
            "ordered_boundary_mae_m": sum(observed_values) / len(observed_values) if observed_values else None,
            "document_cluster_percentile_95_ci": [percentile(distribution, 0.025), percentile(distribution, 0.975)],
            "evaluated_boundary_count": len(observed_values),
        }
    return output


def acceptance_group_diagnostics(records: list[dict], accepted: bool) -> dict:
    group = [record for record in records if record["risk_acceptance"] is accepted]
    all_area = polygon_area(convex_hull([(record["x"], record["y"]) for record in records]))
    group_xy = [(record["x"], record["y"]) for record in group]
    errors = []
    exact = 0
    for record in group:
        aligned = min(len(record["reference"]), len(record["raw"]))
        document_errors = [abs(boundary_value(record, "raw", index) - boundary_value(record, "reference", index)) for index in range(aligned)]
        errors.extend(document_errors)
        exact += len(record["raw"]) == len(record["reference"]) and all(error <= 0.05 for error in document_errors)
    group_area = polygon_area(convex_hull(group_xy))
    return {
        "risk_acceptance": accepted,
        "document_count": len(group),
        "reference_boundary_count": sum(len(record["reference"]) for record in group),
        "raw_available_boundary_count": sum(len(record["raw"]) for record in group),
        "raw_missing_boundary_count": sum(max(0, len(record["reference"]) - len(record["raw"])) for record in group),
        "raw_order_aligned_boundary_mae_m": sum(errors) / len(errors) if errors else None,
        "raw_exact_document_count": exact,
        "convex_hull_area_ratio_to_all_records": group_area / all_area if all_area else None,
        "nearest_neighbour_distance_m": summary(nearest_neighbour_distances(group_xy)),
    }


def volume_jackknife(records: list[dict], variants: list[str], power: float, neighbours: int | None, grid_size: int) -> dict:
    values = {variant: {"relative_absolute_volume_error": [], "mean_thickness_mae_m": []} for variant in variants}
    for held_out in records:
        training = [record for record in records if record["record_id"] != held_out["record_id"]]
        comparison = compare(training, variants, power, neighbours, grid_size)
        for variant in variants:
            aggregate = comparison[variant]["aggregate"]
            for metric in values[variant]:
                value = aggregate[metric]
                if value is not None:
                    values[variant][metric].append(float(value))
    return {
        "unit": "leave_one_borehole_out_recomputed_surface_and_volume",
        "held_out_borehole_count": len(records),
        "variants": {
            variant: {metric: summary(metric_values) for metric, metric_values in metrics.items()}
            for variant, metrics in values.items()
        },
    }


def stripped_intervals(rows: list[dict]) -> list[dict]:
    return [{
        "top_depth_m": round(float(row["top_depth_m"]), 6),
        "bottom_depth_m": round(float(row["bottom_depth_m"]), 6),
        "thickness_m": round(float(row["bottom_depth_m"]) - float(row["top_depth_m"]), 6),
    } for row in rows]


def write_public_spatial_input(records: list[dict], destination: Path) -> dict:
    """Transform absolute origins while preserving analysis distances."""
    center_x = sum(record["x"] for record in records) / len(records)
    center_y = sum(record["y"] for record in records) / len(records)
    collar_origin = sum(record["collar"] for record in records) / len(records)
    angle = math.radians(17.0)
    cosine, sine = math.cos(angle), math.sin(angle)
    public_rows = []
    for record in records:
        translated_x, translated_y = record["x"] - center_x, record["y"] - center_y
        x_relative = cosine * translated_x - sine * translated_y
        y_relative = sine * translated_x + cosine * translated_y
        public_rows.append({
            "record_key": "spatial_" + hashlib.sha256(f"paper3-spatial-v001:{record['record_id']}".encode()).hexdigest()[:20],
            "x_relative_m": round(x_relative, 12),
            "y_relative_m": round(y_relative, 12),
            "collar_relative_m": round(record["collar"] - collar_origin, 9),
            "risk_acceptance": record["risk_acceptance"],
            "reference": stripped_intervals(record["reference"]),
            "raw": stripped_intervals(record["raw"]),
            "reread": stripped_intervals(record["reread"]),
            "risk": stripped_intervals(record["risk"]),
        })
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in public_rows), encoding="utf-8")
    metadata = {
        "schema_version": "paper3_spatial_input_public_v001",
        "record_count": len(public_rows),
        "transform": "subtract horizontal centroid; rotate 17 degrees; subtract mean collar elevation",
        "invariance": "pairwise horizontal distances, relative elevations, interval depths, risk decisions, and IDW diagnostics are preserved up to decimal rounding",
        "privacy_classification": "transformed_pseudonymized_not_anonymous",
        "linkage_warning": "The rigid transform preserves pairwise-distance fingerprints and may be linked to a matching public point set.",
        "excluded": ["source record ID", "absolute easting/northing", "absolute vertical datum origin", "source paths", "document text"],
        "evidence_tier": "SOURCE_AGREEMENT_REFERENCE_WITH_AUTHORITATIVE_SPATIAL_METADATA",
        "rights_review": "AUTHOR_VERIFIED_FOR_PUBLIC_PAPER4_PACKAGE",
        "rights_review_supersedes": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        "rights_reviewed_by": "Yifan Du",
        "rights_reviewed_on": "2026-08-20",
        "rights_review_scope": "Paper 4 result-reproduction package; transformed input remains linkable and is not anonymous",
    }
    destination.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def load_records(manifest_path: Path, prediction_path: Path) -> list[dict]:
    manifest = {
        row["record_id"]: row
        for row in (json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    predictions = {
        row["record_id"]: row
        for row in (json.loads(line) for line in prediction_path.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    if set(manifest) != set(predictions):
        raise ValueError("manifest and predictions do not align")
    records = []
    for record_id in sorted(manifest):
        reference = json.loads(Path(manifest[record_id]["reference_path"]).read_text(encoding="utf-8"))
        intervals = sorted(reference["stratigraphy"]["intervals"], key=lambda row: (float(row["top_depth_m"]), float(row["bottom_depth_m"])))
        prediction = predictions[record_id]
        records.append({
            "record_id": record_id,
            "x": float(reference["borehole"]["x_coordinate"]),
            "y": float(reference["borehole"]["y_coordinate"]),
            "collar": float(reference["borehole"]["collar_elevation_m"]),
            "reference": intervals,
            "raw": prediction["first_pass_intervals"],
            "reread": prediction["final_intervals"],
            "risk": prediction["risk_aware_final_intervals"],
            "risk_acceptance": bool(prediction["risk_acceptance"]),
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--bootstrap-repetitions", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--public-input", type=Path, default=ROOT / "experiments/paper3/public/spatial_input_v001.jsonl")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json",
    )
    arguments = parser.parse_args()
    records = load_records(arguments.manifest, arguments.predictions)
    accepted = [record for record in records if record["risk_acceptance"]]
    variants = ["raw", "reread", "risk"]
    full_support = compare(records, variants, power=2, neighbours=None, grid_size=25)
    matched_subset = compare(accepted, variants, power=2, neighbours=None, grid_size=25)
    public_metadata = write_public_spatial_input(records, arguments.public_input)

    support = []
    for boundary in range(max(len(record["reference"]) for record in records)):
        for variant in variants:
            support.append(support_diagnostics(records, variant, boundary, grid_size=25))

    sensitivity = []
    for domain_name, domain_records in (("full_reference_hull", records), ("matched_accepted_hull", accepted)):
        for power in (1.0, 2.0, 3.0):
            for neighbours in (None, 4, 8):
                for grid_size in (15, 25, 41):
                    comparison = compare(domain_records, variants, power, neighbours, grid_size)
                    sensitivity.append({
                        "domain": domain_name,
                        "power": power,
                        "neighbours": "all" if neighbours is None else neighbours,
                        "grid_size": grid_size,
                        "variants": {name: value["aggregate"] for name, value in comparison.items()},
                    })

    loocv_rows = []
    for domain_name, domain_records in (("all_reference_targets", records), ("matched_accepted_targets", accepted)):
        for power in (1.0, 2.0, 3.0):
            for neighbours in (None, 4, 8):
                loocv_rows.append({
                    "domain": domain_name,
                    "power": power,
                    "neighbours": "all" if neighbours is None else neighbours,
                    "variants": loocv(domain_records, ["reference", *variants], power, neighbours),
                })

    rng = random.Random(arguments.seed)
    payload = {
        "analysis_version": "swissgeol_spatial_sensitivity_v001",
        "evidence_tier": "SOURCE_AGREEMENT_REFERENCE_WITH_AUTHORITATIVE_SPATIAL_METADATA",
        "positioning": "stratigraphic surface and volume sensitivity diagnostic; not a validated geological model",
        "document_count": len(records),
        "risk_accepted_document_count": len(accepted),
        "risk_document_coverage": len(accepted) / len(records),
        "default_idw": {"power": 2, "neighbours": "all", "grid_size": 25},
        "full_support_comparison": full_support,
        "matched_subset_comparison": matched_subset,
        "matched_subset_interpretation": "Risk and reread values are identical on accepted records; any full-support difference between them is therefore attributable to selection/support, not an additional correction.",
        "spatial_support": support,
        "idw_parameter_sensitivity": sensitivity,
        "leave_one_borehole_out": loocv_rows,
        "acceptance_group_diagnostics": {
            "accepted": acceptance_group_diagnostics(records, True),
            "rejected": acceptance_group_diagnostics(records, False),
        },
        "volume_jackknife": {
            "full_support": volume_jackknife(records, variants, 2, None, 25),
            "matched_accepted_subset": volume_jackknife(accepted, variants, 2, None, 25),
        },
        "public_spatial_input": {
            "path": arguments.public_input.relative_to(ROOT).as_posix(),
            **public_metadata,
        },
        "matched_subset_document_bootstrap": {
            "unit": "borehole/document",
            "repetitions": arguments.bootstrap_repetitions,
            "seed": arguments.seed,
            "ordered_boundary_error": document_bootstrap(
                accepted, variants, arguments.bootstrap_repetitions, rng
            ),
        },
        "uncertainty_separation": {
            "borehole_sampling_variability": "document-cluster bootstrap over matched accepted records",
            "spatial_model_variability": "IDW power/neighbour/grid/domain sweep",
            "perturbation_seed_variability": "reported only by the separate controlled error-injection experiment; seeds are not independent sites",
        },
        "limitations": [
            "Coordinates and collar elevations are authoritative database fields rather than page-extracted values.",
            "Ordered boundary positions are compared without geological unit correlation.",
            "Matched-subset estimates condition on the frozen risk router accepting a document.",
            "IDW is a transparent surface proxy and does not model faults, anisotropy, or stratigraphic correlation uncertainty.",
        ],
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(arguments.output)


if __name__ == "__main__":
    main()
