#!/usr/bin/env python3
"""Execute raw/reference/constrained downstream comparison on known Synthetic data."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
import random
import subprocess
from pathlib import Path

from geologparser.evaluation import aggregate_repeated_metrics, boundary_surface_points, idw_predict, surface_error_metrics
from geologparser.experiment import create_run_directory
from geologparser.rereading import Candidate, decide_reread

ROOT = Path(__file__).resolve().parents[1]


def records() -> list[dict]:
    base = json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))
    output = []
    for index, (x, y, collar) in enumerate(((0, 0, 100), (10, 0, 102), (0, 10, 98), (10, 10, 101))):
        row = copy.deepcopy(base)
        row["document"]["document_id"] = f"SYNTH_{index}"
        row["borehole"]["borehole_id"]["value"] = f"SYNTH_ZK{index}"
        row["borehole"]["x_coordinate"]["value"] = x
        row["borehole"]["y_coordinate"]["value"] = y
        row["borehole"]["collar_elevation_m"]["value"] = collar
        output.append(row)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--base-seed", type=int, default=20260813)
    parser.add_argument("--repetitions", type=int, default=30)
    args = parser.parse_args()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    source = ROOT / "examples/boreholes/synthetic_valid.json"
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id, "git_commit": commit, "date": "2026-08-13",
        "dataset_version": "executed_synthetic_downstream_v001", "split_version": "synthetic_controlled_no_training",
        "model": "idw_power_2_plus_geologparser_reread", "model_revision": "rereading_core_v001",
        "prompt_version": "not_applicable", "seed": args.base_seed,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {"ground_truth_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                   "repetitions": args.repetitions, "boundary": "intervals[0].bottom_depth_m",
                   "magnitudes_m": [.01, .05, .10, .50, 1.00], "idw_power": 2,
                   "comparison": "raw_vs_constrained_vs_synthetic_reference"},
    })
    reference_records = records()
    queries = [(x, y) for x in range(0, 11, 2) for y in range(0, 11, 2)]
    reference_points = boundary_surface_points(reference_records, 0)
    reference_surface = [idw_predict(reference_points, x, y) for x, y in queries]
    rows, conditions = [], []
    for magnitude_index, magnitude in enumerate((.01, .05, .10, .50, 1.00)):
        raw_metrics, constrained_metrics = [], []
        accepted = abstained = 0
        for repetition in range(args.repetitions):
            seed = args.base_seed + magnitude_index * 10000 + repetition
            rng = random.Random(seed)
            raw = copy.deepcopy(reference_records)
            constrained = copy.deepcopy(reference_records)
            decisions = []
            for index, record in enumerate(raw):
                reference = float(reference_records[index]["intervals"][0]["bottom_depth_m"]["value"])
                observed = reference + rng.choice((-magnitude, magnitude))
                record["intervals"][0]["bottom_depth_m"]["value"] = observed
                constrained[index] = copy.deepcopy(record)
                decision = decide_reread(constrained[index], "intervals[0].bottom_depth_m", [
                    Candidate(reference, "ocr_reread", str(reference), .90, .90, .85),
                    Candidate(reference, "vlm_reread", str(reference), .86, .85, .90),
                    Candidate(observed, "first_pass", str(observed), .94, .94, .90),
                ])
                decisions.append({"borehole": index, "status": decision.status,
                                  "original": observed, "accepted": decision.accepted_value,
                                  "reason": decision.reason})
                if decision.status == "ACCEPT_PROPOSAL":
                    constrained[index] = copy.deepcopy(decision.proposed_record)
                    accepted += 1
                else:
                    abstained += 1
            raw_surface = [idw_predict(boundary_surface_points(raw, 0), x, y) for x, y in queries]
            constrained_surface = [idw_predict(boundary_surface_points(constrained, 0), x, y) for x, y in queries]
            raw_result = surface_error_metrics(reference_surface, raw_surface)
            constrained_result = surface_error_metrics(reference_surface, constrained_surface)
            raw_metrics.append(raw_result); constrained_metrics.append(constrained_result)
            rows.append({"magnitude_m": magnitude, "seed": seed, "raw": raw_result,
                         "constrained": constrained_result, "decisions": decisions})
        conditions.append({"magnitude_m": magnitude,
                           "raw": aggregate_repeated_metrics(raw_metrics),
                           "constrained": aggregate_repeated_metrics(constrained_metrics),
                           "accepted_corrections": accepted, "abstentions": abstained})
    metrics = {"scope": "executed Synthetic raw/constrained/reference downstream comparison; not real-site evidence",
               "data_status": "synthetic_known_reference", "comparison": "raw_vs_constrained_vs_synthetic_reference",
               "conditions": conditions}
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (run / "predictions.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    (run / "errors.jsonl").write_text("", encoding="utf-8")
    (run / "run.log").write_text(f"status=completed\nrepetitions={args.repetitions}\nscope=synthetic_executed_downstream\n", encoding="utf-8")
    print(run)


if __name__ == "__main__": main()
