#!/usr/bin/env python3
"""Propagate frozen image-derived boundary predictions into a real-site surface.

The upstream predictions are read from a completed, reference-blinded Paper II
held-out run.  This script adds only authoritative spatial metadata and computes
the downstream surface diagnostic; it never changes the upstream predictions.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import platform
import resource
import subprocess
import time
from pathlib import Path

from geologparser.evaluation import SurfacePoint, idw_predict, surface_error_metrics
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest

ROOT = Path(__file__).resolve().parents[1]


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

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


def inside(point, polygon):
    if len(polygon) < 3:
        return True
    signs = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        value = (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])
        if abs(value) > 1e-9:
            signs.append(value > 0)
    return not signs or all(value == signs[0] for value in signs)


def grid(points: list[SurfacePoint], size: int) -> list[tuple[float, float]]:
    hull = convex_hull([(p.x, p.y) for p in points])
    if len(hull) < 3:
        return [(p.x, p.y) for p in points]
    xs, ys = [p.x for p in points], [p.y for p in points]
    queries = []
    for row in range(size):
        y = min(ys) + (max(ys) - min(ys)) * row / (size - 1)
        for col in range(size):
            x = min(xs) + (max(xs) - min(xs)) * col / (size - 1)
            if inside((x, y), hull):
                queries.append((x, y))
    return queries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--prediction-run", type=Path, required=True)
    parser.add_argument("--evaluation-manifest", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--grid-size", type=int, default=25)
    args = parser.parse_args()
    prediction_path = args.prediction_run / "predictions.jsonl"
    prediction_rows = [json.loads(line) for line in prediction_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest_rows = [json.loads(line) for line in args.evaluation_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest_by_id = {row["record_id"]: row for row in manifest_rows}
    if not prediction_rows:
        raise ValueError("prediction run is empty")
    if any(row["record_id"] not in manifest_by_id for row in prediction_rows):
        raise ValueError("prediction run contains records outside evaluation manifest")
    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": "swissgeol_thurgau_paired_v003_boundary_surface_from_frozen_reread",
        "split_version": "v003_heldout_inherited_from_p2_reread",
        "model": "frozen_paper2_image_boundary_predictions_plus_idw",
        "model_revision": "upstream_prediction_run_frozen",
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "ground_truth_sha256": file_sha256(args.evaluation_manifest),
            "upstream_prediction_run": str(args.prediction_run),
            "upstream_prediction_sha256": file_sha256(prediction_path),
            "prediction_reference_conditioning": "none_inherited_from_upstream_run",
            "reference_boundary": "first_interval_bottom_depth_m",
            "spatial_metadata_source": "authoritative_structured_reference_borehole_coordinates_and_collar_elevation",
            "coordinate_system": "CH1903+/LV95",
            "interpolator": "IDW_power_2",
            "grid_size": args.grid_size,
            "domain": "authoritative_reference_convex_hull",
            "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        },
        "started_utc": started.isoformat(),
    })
    wall_started = time.perf_counter()
    records = []
    for prediction in prediction_rows:
        source = manifest_by_id[prediction["record_id"]]
        reference_path = Path(source["reference_path"])
        if file_sha256(reference_path) != source["reference_sha256"]:
            raise ValueError(f"reference hash mismatch: {reference_path}")
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        borehole = reference["borehole"]
        intervals = sorted(reference["stratigraphy"]["intervals"], key=lambda item: (float(item["top_depth_m"]), float(item["bottom_depth_m"])))
        if not intervals:
            continue
        ref_depth = float(intervals[0]["bottom_depth_m"])
        raw_depth = prediction["first_pass_intervals"][0]["bottom_depth_m"] if prediction["first_pass_intervals"] else None
        final_depth = prediction["final_intervals"][0]["bottom_depth_m"] if prediction["final_intervals"] else None
        collar = float(borehole["collar_elevation_m"])
        records.append({
            "record_id": prediction["record_id"], "x": float(borehole["x_coordinate"]), "y": float(borehole["y_coordinate"]),
            "reference_elevation_m": collar - ref_depth,
            "raw_elevation_m": collar - raw_depth if raw_depth is not None else None,
            "final_elevation_m": collar - final_depth if final_depth is not None else None,
            "reference_depth_m": ref_depth, "raw_depth_m": raw_depth, "final_depth_m": final_depth,
            "decision": prediction["decision"], "triggers": prediction["triggers"],
        })
    reference_points = [SurfacePoint(r["x"], r["y"], r["reference_elevation_m"], r["record_id"]) for r in records]
    queries = grid(reference_points, args.grid_size)
    reference_surface = [idw_predict(reference_points, x, y) for x, y in queries]
    variant_metrics = {}
    variant_surfaces = {}
    for variant in ("raw", "final"):
        points = [SurfacePoint(r["x"], r["y"], r[f"{variant}_elevation_m"], r["record_id"]) for r in records if r[f"{variant}_elevation_m"] is not None]
        surface = [idw_predict(points, x, y) for x, y in queries] if len(points) >= 1 else []
        variant_surfaces[variant] = surface
        variant_metrics[variant] = {
            "point_count": len(points), "query_count": len(surface),
            "surface_error": surface_error_metrics(reference_surface, surface) if len(surface) == len(reference_surface) else {"count": 0, "mae_m": None, "rmse_m": None, "max_abs_error_m": None},
            "boundary_mae_m": sum(abs(r[f"{variant}_depth_m"] - r["reference_depth_m"]) for r in records if r[f"{variant}_depth_m"] is not None) / sum(r[f"{variant}_depth_m"] is not None for r in records),
            "boundary_available_count": sum(r[f"{variant}_depth_m"] is not None for r in records),
        }
    (run / "predictions.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records), encoding="utf-8")
    metrics = {
        "scope": "real image-derived first-boundary downstream surface diagnostic",
        "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "data_status": "real_image_pdf_with_authoritative_structured_spatial_metadata",
        "comparison": "raw_image_boundary_vs_constraint_reread_boundary_vs_authoritative_reference_surface",
        "prediction_reference_conditioning": "none",
        "reference_blinded_decision_policy": True,
        "document_count": len(records), "reference_point_count": len(reference_points), "query_count": len(queries),
        "triggered_document_count": sum(bool(r["triggers"]) for r in records),
        "accepted_reread_count": sum(r["decision"] == "ACCEPT_REREAD" for r in records),
        "needs_review_count": sum(str(r["decision"]).startswith("NEEDS_REVIEW") for r in records),
        "surface": variant_metrics,
        "spatial_metadata_limitation": "coordinates and collar elevations come from the authoritative structured record; image extraction of spatial metadata is not evaluated",
        "selection_limitation": "source-agreement explicit-table held-out pilot from one canton/source family; not a representative random sample or cross-source evaluation",
        "upstream_prediction_run": str(args.prediction_run),
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        "wall_time_seconds": time.perf_counter() - wall_started,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "errors.jsonl").write_text("", encoding="utf-8")
    ended = datetime.now(timezone.utc)
    (run / "run.log").write_text(f"started_utc={started.isoformat()}\nended_utc={ended.isoformat()}\ndocuments={len(records)}\nqueries={len(queries)}\nstatus=completed\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
