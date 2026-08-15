#!/usr/bin/env python3
"""Export a real Swissgeol boundary surface for visual inspection.

The source records and frozen boundary predictions are reference-independent;
the reference surface is exported alongside the reread surface for downstream
comparison.  This artifact is visualization evidence, not an engineering model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

from geologparser.evaluation import SurfacePoint
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest
from geologparser.visualization import idw_surface_grid, write_pyvista_surface

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v003/gold_interval_manifest_heldout_v003.jsonl")
PREDICTION = ROOT / "results/2026-08-14/P2_SWISSGEOL_TG_CONSTRAINT_REREAD_HELDOUT_V003_001"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hull(points):
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower = []
    for p in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default="P3_SWISSGEOL_REAL_SURFACE_VTP_001")
    parser.add_argument("--boundary-index", type=int, default=0)
    parser.add_argument("--grid-size", type=int, default=25)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    manifest = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    predictions = {
        row["record_id"]: row
        for row in (json.loads(line) for line in (PREDICTION / "predictions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    }
    records = []
    for item in manifest:
        reference = json.loads(Path(item["reference_path"]).read_text(encoding="utf-8"))
        intervals = sorted(reference["stratigraphy"]["intervals"], key=lambda x: (float(x["top_depth_m"]), float(x["bottom_depth_m"])))
        if len(intervals) <= args.boundary_index:
            continue
        prediction = predictions[item["record_id"]]
        records.append({
            "record_id": item["record_id"],
            "x": float(reference["borehole"]["x_coordinate"]),
            "y": float(reference["borehole"]["y_coordinate"]),
            "collar": float(reference["borehole"]["collar_elevation_m"]),
            "reference": float(intervals[args.boundary_index]["bottom_depth_m"]),
            "final": float(prediction["final_intervals"][args.boundary_index]["bottom_depth_m"])
            if len(prediction["final_intervals"]) > args.boundary_index else None,
        })
    points_xy = [(r["x"], r["y"]) for r in records]
    polygon = hull(points_xy)
    xs = [p[0] for p in polygon] or points_xy
    ys = [p[1] for p in polygon] or points_xy
    x_values = [min(xs) + (max(xs) - min(xs)) * i / (args.grid_size - 1) for i in range(args.grid_size)]
    y_values = [min(ys) + (max(ys) - min(ys)) * i / (args.grid_size - 1) for i in range(args.grid_size)]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": "2026-08-15",
        "dataset_version": "swissgeol_thurgau_v003_real_surface_visualization",
        "split_version": "v003_heldout_frozen_boundary_predictions",
        "model": "idw_real_boundary_surface_to_pyvista",
        "model_revision": "v001",
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {"manifest_sha256": file_sha256(MANIFEST), "prediction_sha256": file_sha256(PREDICTION / "predictions.jsonl"), "boundary_index": args.boundary_index, "grid_size": args.grid_size, "interpretation": "visualization artifact only; not validated geological model"},
    })
    ref_points = [SurfacePoint(r["x"], r["y"], r["collar"] - r["reference"], r["record_id"]) for r in records]
    final_records = [r for r in records if r["final"] is not None]
    final_points = [SurfacePoint(r["x"], r["y"], r["collar"] - r["final"], r["record_id"]) for r in final_records]
    ref_grid = idw_surface_grid(ref_points, x_values, y_values)
    final_grid = idw_surface_grid(final_points, x_values, y_values) if len(final_points) >= 2 else None
    exports = {"reference": write_pyvista_surface(ref_grid, run / "reference_surface.vtp", run / "reference_surface.png")}
    if final_grid is not None:
        exports["final"] = write_pyvista_surface(final_grid, run / "final_surface.vtp", run / "final_surface.png")
    (run / "predictions.jsonl").write_text(json.dumps({"records": records, "boundary_index": args.boundary_index, "x_values": x_values, "y_values": y_values}, ensure_ascii=False) + "\n", encoding="utf-8")
    metrics = {"scope": "real surface visualization artifact", "document_count": len(records), "boundary_index": args.boundary_index, "reference_point_count": len(ref_points), "final_point_count": len(final_points), "exports": exports, "surface_vtp_sha256": {name: sha256(run / f"{name}_surface.vtp") for name in exports}, "surface_png_sha256": {name: sha256(run / f"{name}_surface.png") for name in exports}, "interpretation": "visualization and interoperability evidence only; no geological validity claim"}
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run / "errors.jsonl").write_text("", encoding="utf-8")
    (run / "run.log").write_text("status=completed\nscope=real_surface_visualization_artifact\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
