#!/usr/bin/env python3
"""Build a real multi-layer stratigraphic surface model from frozen boundaries.

The upstream boundary predictions are frozen before references are loaded.  For
each adjacent pair of ordered boundaries, a transparent IDW surface is built
for the reference, first-pass, and reread channels.  Layer thickness and
volume discrepancies are then evaluated on a common reference-domain grid.
This is a diagnostic baseline, not a claim of geological interpretation.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import resource
import subprocess
import time
from datetime import date, datetime, timezone
from pathlib import Path

from geologparser.evaluation import SurfacePoint, idw_predict
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(
    "/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v003/"
    "gold_interval_manifest_heldout_v003.jsonl"
)
DEFAULT_PREDICTION = ROOT / "results/2026-08-14/P2_SWISSGEOL_TG_CONSTRAINT_REREAD_HELDOUT_V003_001"


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

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


def polygon_area(polygon: list[tuple[float, float]]) -> float:
    if len(polygon) < 3:
        return 0.0
    return abs(sum(
        polygon[i][0] * polygon[(i + 1) % len(polygon)][1]
        - polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
        for i in range(len(polygon))
    )) / 2.0


def inside(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    if len(polygon) < 3:
        return True
    signs = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        value = (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])
        if abs(value) > 1e-9:
            signs.append(value > 0)
    return not signs or all(value == signs[0] for value in signs)


def grid(points: list[tuple[float, float]], size: int) -> list[tuple[float, float]]:
    hull = convex_hull(points)
    if len(hull) < 3:
        return sorted(set(points))
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    output = []
    for row in range(size):
        y = min(ys) + (max(ys) - min(ys)) * row / (size - 1)
        for col in range(size):
            x = min(xs) + (max(xs) - min(xs)) * col / (size - 1)
            if inside((x, y), hull):
                output.append((x, y))
    return output


def surface(points: list[SurfacePoint], queries: list[tuple[float, float]]) -> list[float]:
    return [idw_predict(points, x, y) for x, y in queries]


def summarize_layer(records: list[dict], layer_index: int, variant: str, grid_size: int) -> dict:
    eligible = [r for r in records if len(r["reference"]) > layer_index + 1]
    reference_xy = [(r["x"], r["y"]) for r in eligible]
    queries = grid(reference_xy, grid_size)
    area = polygon_area(convex_hull(reference_xy))
    reference_points = []
    variant_points = {0: [], 1: []}
    for r in eligible:
        for boundary in (0, 1):
            depth = float(r["reference"][layer_index + boundary]["bottom_depth_m"])
            point = SurfacePoint(r["x"], r["y"], r["collar"] - depth, r["record_id"])
            if boundary == 0:
                reference_points.append(point)
            values = r[variant]
            if len(values) > layer_index + boundary:
                depth = float(values[layer_index + boundary]["bottom_depth_m"])
                variant_points[boundary].append(
                    SurfacePoint(r["x"], r["y"], r["collar"] - depth, r["record_id"])
                )

    # Rebuild the reference top and bottom surfaces separately.
    ref_top = surface([
        SurfacePoint(r["x"], r["y"], r["collar"] - float(r["reference"][layer_index]["bottom_depth_m"]), r["record_id"])
        for r in eligible
    ], queries)
    ref_bottom = surface([
        SurfacePoint(r["x"], r["y"], r["collar"] - float(r["reference"][layer_index + 1]["bottom_depth_m"]), r["record_id"])
        for r in eligible
    ], queries)
    pred_top = surface(variant_points[0], queries) if variant_points[0] else []
    pred_bottom = surface(variant_points[1], queries) if variant_points[1] else []
    reference_thickness = [top - bottom for top, bottom in zip(ref_top, ref_bottom)]
    predicted_thickness = [top - bottom for top, bottom in zip(pred_top, pred_bottom)] if pred_top and pred_bottom else []
    errors = [abs(a - b) for a, b in zip(reference_thickness, predicted_thickness)]
    signed_delta = [b - a for a, b in zip(reference_thickness, predicted_thickness)]
    ref_volume = area * (sum(reference_thickness) / len(reference_thickness)) if reference_thickness else None
    pred_volume = area * (sum(predicted_thickness) / len(predicted_thickness)) if predicted_thickness else None
    return {
        "layer_index": layer_index + 1,
        "reference_record_count": len(eligible),
        "query_count": len(queries),
        "reference_domain_area_m2": area,
        "variant": variant,
        "top_boundary_support": len(variant_points[0]) / len(eligible) if eligible else None,
        "bottom_boundary_support": len(variant_points[1]) / len(eligible) if eligible else None,
        "layer_thickness_mae_m": sum(errors) / len(errors) if errors else None,
        "layer_thickness_rmse_m": math.sqrt(sum(x * x for x in errors) / len(errors)) if errors else None,
        "negative_predicted_thickness_fraction": sum(x < 0 for x in predicted_thickness) / len(predicted_thickness) if predicted_thickness else None,
        "reference_volume_m3": ref_volume,
        "predicted_volume_m3": pred_volume,
        "absolute_volume_error_m3": abs(pred_volume - ref_volume) if pred_volume is not None and ref_volume is not None else None,
        "signed_volume_delta_m3": pred_volume - ref_volume if pred_volume is not None and ref_volume is not None else None,
        "mean_reference_thickness_m": sum(reference_thickness) / len(reference_thickness) if reference_thickness else None,
        "mean_predicted_thickness_m": sum(predicted_thickness) / len(predicted_thickness) if predicted_thickness else None,
        "mean_signed_thickness_delta_m": sum(signed_delta) / len(signed_delta) if signed_delta else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default="P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_001")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--prediction-run", type=Path, default=DEFAULT_PREDICTION)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--grid-size", type=int, default=25)
    args = parser.parse_args()
    manifest = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    predictions = {
        row["record_id"]: row
        for row in (json.loads(line) for line in (args.prediction_run / "predictions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    }
    if set(predictions) != {row["record_id"] for row in manifest}:
        raise ValueError("prediction and evaluation records must match exactly")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": "swissgeol_thurgau_v003_real_stratigraphic_layer_model",
        "split_version": "v003_heldout_frozen_boundary_predictions",
        "model": "idw_stratigraphic_layer_volume_from_ordered_boundaries",
        "model_revision": "v001",
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "ground_truth_sha256": file_sha256(args.manifest),
            "prediction_run": str(args.prediction_run),
            "prediction_sha256": file_sha256(args.prediction_run / "predictions.jsonl"),
            "prediction_reference_conditioning": "none_inherited_from_upstream_run",
            "reference_spatial_metadata": "authoritative_structured_coordinates_and_collar_elevation",
            "boundary_alignment": "ordered_interval_index_without_reference_guided_repair",
            "interpolator": "IDW_power_2",
            "grid_size": args.grid_size,
            "units": {"coordinates": "m_CH1903_plus_LV95", "elevation": "m", "volume": "m3"},
            "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        },
        "started_utc": started.isoformat(),
    })
    wall_started = time.perf_counter()
    records = []
    for item in manifest:
        ref_path = Path(item["reference_path"])
        if file_sha256(ref_path) != item["reference_sha256"]:
            raise ValueError(f"reference hash mismatch: {ref_path}")
        reference = json.loads(ref_path.read_text(encoding="utf-8"))
        intervals = sorted(reference["stratigraphy"]["intervals"], key=lambda x: (float(x["top_depth_m"]), float(x["bottom_depth_m"])))
        prediction = predictions[item["record_id"]]
        records.append({
            "record_id": item["record_id"],
            "x": float(reference["borehole"]["x_coordinate"]),
            "y": float(reference["borehole"]["y_coordinate"]),
            "collar": float(reference["borehole"]["collar_elevation_m"]),
            "reference": intervals,
            "raw": prediction["first_pass_intervals"],
            "final": prediction["final_intervals"],
        })
        if "risk_aware_final_intervals" in prediction:
            records[-1]["risk_aware"] = prediction["risk_aware_final_intervals"]
    variants = ["raw", "final"]
    if any("risk_aware" in record for record in records):
        variants.append("risk_aware")
    max_boundaries = max(len(r["reference"]) for r in records) - 1
    layer_rows = []
    for layer_index in range(max_boundaries):
        for variant in variants:
            layer_rows.append(summarize_layer(records, layer_index, variant, args.grid_size))
    by_variant = {}
    for variant in variants:
        rows = [r for r in layer_rows if r["variant"] == variant]
        volumes = [r["absolute_volume_error_m3"] for r in rows if r["absolute_volume_error_m3"] is not None]
        reference_volumes = [r["reference_volume_m3"] for r in rows if r["reference_volume_m3"] is not None]
        thickness = [r["layer_thickness_mae_m"] for r in rows if r["layer_thickness_mae_m"] is not None]
        by_variant[variant] = {
            "layer_count": len(rows),
            "mean_layer_thickness_mae_m": sum(thickness) / len(thickness) if thickness else None,
            "sum_absolute_volume_error_m3": sum(volumes) if volumes else None,
            "sum_reference_volume_m3": sum(reference_volumes) if reference_volumes else None,
            "relative_absolute_volume_error": (
                sum(volumes) / sum(reference_volumes)
                if volumes and reference_volumes and sum(reference_volumes) != 0
                else None
            ),
            "layers_with_negative_thickness": sum((r["negative_predicted_thickness_fraction"] or 0) > 0 for r in rows),
            "mean_top_boundary_support": sum(r["top_boundary_support"] for r in rows if r["top_boundary_support"] is not None) / len([r for r in rows if r["top_boundary_support"] is not None]),
            "mean_bottom_boundary_support": sum(r["bottom_boundary_support"] for r in rows if r["bottom_boundary_support"] is not None) / len([r for r in rows if r["bottom_boundary_support"] is not None]),
        }
    metrics = {
        "scope": "real image-derived stratigraphic layer-model diagnostic",
        "comparison": "gold_vs_raw_vs_constraint_reread_vs_risk_aware_abstention_boundary_surface",
        "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "data_status": "real_image_pdf_with_authoritative_structured_spatial_metadata",
        "human_ground_truth_evidence": False,
        "prediction_reference_conditioning": "none",
        "reference_blinded_decision_policy": True,
        "document_count": len(records),
        "boundary_count": max_boundaries + 1,
        "reference_point_count": sum(len(r["reference"]) for r in records),
        "layer_count": max_boundaries,
        "model_type": "IDW surfaces converted to adjacent stratigraphic layer thickness and volume",
        "spatial_metadata_limitation": "coordinates and collar elevations come from authoritative structured records rather than page extraction",
        "alignment_limitation": "ordered interval index is used without reference-guided repair",
        "layer_rows": layer_rows,
        "by_variant": by_variant,
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        "wall_time_seconds": time.perf_counter() - wall_started,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (run / "predictions.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in layer_rows), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "errors.jsonl").write_text("", encoding="utf-8")
    (run / "run.log").write_text(f"started_utc={started.isoformat()}\ndocuments={len(records)}\nlayers={max_boundaries}\nstatus=completed\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
