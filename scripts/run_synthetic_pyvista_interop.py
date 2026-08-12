#!/usr/bin/env python3
"""Run a protocol-only synthetic IDW-to-PyVista interoperability check."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess

from geologparser.evaluation import boundary_surface_points
from geologparser.experiment import create_run_directory
from geologparser.visualization import idw_surface_grid, write_pyvista_surface


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records() -> list[dict]:
    base = json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))
    result = []
    for index, (x, y, collar) in enumerate(((0, 0, 100), (10, 0, 102), (0, 10, 98), (10, 10, 101))):
        record = json.loads(json.dumps(base))
        record["document"]["document_id"] = f"SYNTH_{index}"
        record["borehole"]["borehole_id"]["value"] = f"SYNTH_ZK{index}"
        record["borehole"]["x_coordinate"]["value"] = x
        record["borehole"]["y_coordinate"]["value"] = y
        record["borehole"]["collar_elevation_m"]["value"] = collar
        result.append(record)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    arguments = parser.parse_args()
    import pyvista
    import vtk

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": git_commit,
        "date": "2026-08-12",
        "dataset_version": "synthetic_four_borehole_protocol_fixture_v001",
        "split_version": "not_applicable_protocol_smoke",
        "model": "idw_power_2_to_pyvista_polydata",
        "model_revision": "geologparser_surface3d_v001",
        "prompt_version": "not_applicable",
        "seed": 20260812,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {
            "python": platform.python_version(), "pyvista": pyvista.__version__,
            "vtk": vtk.vtkVersion.GetVTKVersion(),
        },
        "config": {
            "interval_index": 0, "boundary": "bottom_depth_m", "idw_power": 2,
            "grid": {"x": list(range(0, 11)), "y": list(range(0, 11))},
            "scope": "synthetic interoperability protocol; not real-world evidence",
        },
    })
    points = boundary_surface_points(records(), 0)
    grid = idw_surface_grid(points, range(0, 11), range(0, 11), power=2)
    exported = write_pyvista_surface(grid, run / "surface.vtp", run / "surface.png")
    predictions = {
        "surface_grid": {
            "x_values": grid.x_values, "y_values": grid.y_values,
            "elevations_m": grid.elevations,
        },
        "input_points": [point.__dict__ for point in points],
    }
    (run / "predictions.jsonl").write_text(json.dumps(predictions) + "\n", encoding="utf-8")
    metrics = {
        "scope": "synthetic interoperability protocol; not real-world evidence",
        "point_count": exported["point_count"], "triangle_cell_count": exported["cell_count"],
        "bounds": exported["bounds"], "array_names": exported["array_names"],
        "surface_vtp_sha256": sha256(run / "surface.vtp"),
        "surface_png_sha256": sha256(run / "surface.png"),
        "interpretation": "artifact interoperability only; no geological accuracy claim",
    }
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (run / "run.log").write_text(
        "status=completed\nscope=synthetic_interoperability_protocol\ngpu_used=false\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
