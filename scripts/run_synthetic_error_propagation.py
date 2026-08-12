#!/usr/bin/env python3
"""Run a protocol-only synthetic surface error propagation smoke experiment."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from pathlib import Path

from geologparser.evaluation import (
    boundary_surface_points, idw_predict, perturb_interval_boundaries, surface_error_metrics,
)
from geologparser.experiment import create_run_directory


ROOT = Path(__file__).resolve().parents[1]


def synthetic_records() -> list[dict]:
    base = json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))
    records = []
    for index, (x, y, collar) in enumerate(((0, 0, 100), (10, 0, 102), (0, 10, 98), (10, 10, 101))):
        record = json.loads(json.dumps(base))
        record["document"]["document_id"] = f"SYNTH_{index}"
        record["borehole"]["borehole_id"]["value"] = f"SYNTH_ZK{index}"
        record["borehole"]["x_coordinate"]["value"] = x
        record["borehole"]["y_coordinate"]["value"] = y
        record["borehole"]["collar_elevation_m"]["value"] = collar
        records.append(record)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--seed", type=int, default=20260812)
    arguments = parser.parse_args()
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": git_commit,
        "date": "2026-08-12",
        "dataset_version": "synthetic_four_borehole_protocol_fixture_v001",
        "split_version": "not_applicable_protocol_smoke",
        "model": "idw_power_2",
        "model_revision": "geologparser_idw_v001",
        "prompt_version": "not_applicable",
        "seed": arguments.seed,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "magnitudes_m": [0.01, 0.05, 0.10, 0.50, 1.00],
            "interval_index": 0, "boundary": "bottom_depth_m", "idw_power": 2,
            "query_grid": {"x": [0, 2, 4, 6, 8, 10], "y": [0, 2, 4, 6, 8, 10]},
            "scope": "synthetic protocol smoke; not real-world evidence",
        },
    })
    records = synthetic_records()
    queries = [(x, y) for x in range(0, 11, 2) for y in range(0, 11, 2)]
    reference_points = boundary_surface_points(records, 0)
    reference_surface = [idw_predict(reference_points, x, y) for x, y in queries]
    predictions = []
    metrics = {"scope": "synthetic protocol smoke; not real-world evidence", "conditions": []}
    for condition_index, magnitude in enumerate((0.01, 0.05, 0.10, 0.50, 1.00)):
        condition_seed = arguments.seed + condition_index
        perturbed = perturb_interval_boundaries(records, magnitude, condition_seed)
        points = boundary_surface_points(perturbed, 0)
        surface = [idw_predict(points, x, y) for x, y in queries]
        condition_metrics = surface_error_metrics(reference_surface, surface)
        metrics["conditions"].append({
            "magnitude_m": magnitude, "seed": condition_seed, **condition_metrics,
        })
        predictions.append({
            "magnitude_m": magnitude, "seed": condition_seed,
            "queries": queries, "reference_surface_m": reference_surface,
            "predicted_surface_m": surface,
        })
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in predictions), encoding="utf-8",
    )
    (run / "run.log").write_text("status=completed\nscope=synthetic_protocol_smoke\n", encoding="utf-8")
    print(run)


if __name__ == "__main__":
    main()
