#!/usr/bin/env python3
"""Controlled dual-channel QC and downstream propagation on coal-602 source data."""

from __future__ import annotations

import argparse
import json
import platform
import random
from math import comb, sqrt
from statistics import mean, stdev
import subprocess
import time
from pathlib import Path

import yaml

from geologparser.evaluation import (
    SurfacePoint, aggregate_repeated_metrics, convex_hull_xy, idw_predict,
    load_coal_602_roof_depth_surface, regular_queries_within_hull, surface_error_metrics,
)
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256


ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = Path("/data/GeoLogParser/datasets/public/mendeley_coal_boreholes_602_v001")
AUDIT = Path("/data/GeoLogParser/artifacts/structured_data_audits/mendeley_coal_boreholes_602_v001_audit_v002/structured_content_audit.json")


def corrupt_channel(points: tuple[SurfacePoint, ...], magnitude: float, rate: float, seed: int):
    rng = random.Random(seed)
    output, corrupted = [], set()
    for index, point in enumerate(points):
        delta = 0.0
        if rng.random() < rate:
            delta = rng.choice((-magnitude, magnitude))
            corrupted.add(index)
        output.append(SurfacePoint(point.x, point.y, point.elevation + delta, point.borehole_id))
    return tuple(output), corrupted


def consensus_points(left: tuple[SurfacePoint, ...], right: tuple[SurfacePoint, ...], tolerance=1e-9):
    accepted, rejected = [], []
    for index, (a, b) in enumerate(zip(left, right)):
        if (a.x, a.y) != (b.x, b.y):
            raise ValueError("channel coordinates differ")
        if abs(a.elevation - b.elevation) <= tolerance:
            accepted.append(a)
        else:
            rejected.append(index)
    return tuple(accepted), tuple(rejected)


def mean_fusion_points(left: tuple[SurfacePoint, ...], right: tuple[SurfacePoint, ...]):
    """Preserve spatial support and average two independent scalar channels."""
    output = []
    for a, b in zip(left, right):
        if (a.x, a.y) != (b.x, b.y):
            raise ValueError("channel coordinates differ")
        output.append(SurfacePoint(
            a.x, a.y, (a.elevation + b.elevation) / 2.0, a.borehole_id,
        ))
    return tuple(output)


def paired_improvement_summary(raw: list[dict], fused: list[dict]) -> dict:
    """Summarize paired raw-minus-fused MAE with an exact two-sided sign test."""
    differences = [
        float(raw_row["mae_m"]) - float(fused_row["mae_m"])
        for raw_row, fused_row in zip(raw, fused)
    ]
    non_ties = [value for value in differences if value != 0.0]
    positive = sum(value > 0 for value in non_ties)
    negative = sum(value < 0 for value in non_ties)
    tail = min(positive, negative)
    sign_p = min(
        1.0,
        2.0 * sum(comb(len(non_ties), k) for k in range(tail + 1)) / (2 ** len(non_ties)),
    ) if non_ties else None
    average = mean(differences)
    standard_deviation = stdev(differences) if len(differences) > 1 else None
    half_width = 1.96 * standard_deviation / sqrt(len(differences)) if standard_deviation is not None else None
    raw_total = sum(float(row["mae_m"]) for row in raw)
    return {
        "n": len(differences), "fusion_better_count": positive,
        "fusion_worse_count": negative, "tie_count": len(differences) - len(non_ties),
        "mean_mae_reduction_m": average,
        "mean_mae_reduction_ci95_normal": (
            [average - half_width, average + half_width] if half_width is not None else None
        ),
        "relative_mae_reduction": sum(differences) / raw_total if raw_total else None,
        "two_sided_exact_sign_test_p": sign_p,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs/experiments/P3_COAL602_CONSENSUS_QC_CONTROLLED_001.yaml")
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--audit", type=Path, default=AUDIT)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if config["paper_eligibility"] != "formal_source_controlled_downstream":
        raise ValueError("unexpected eligibility")
    acquisition = args.dataset_root / "metadata/acquisition.json"
    workbook = args.dataset_root / "raw/minimum_reproducible_borehole_dataset_602.xlsx"
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    if audit["content_audit"]["record_count"] != 602:
        raise ValueError("coal-602 audit record count changed")

    started = time.perf_counter()
    surface = load_coal_602_roof_depth_surface(workbook)
    hull = convex_hull_xy(surface.points)
    queries = regular_queries_within_hull(hull, int(config["grid_size"]))
    reference = [idw_predict(surface.points, x, y) for x, y in queries]
    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    run = create_run_directory(args.results_root, {
        "experiment_id": config["experiment_id"], "git_commit": git_commit,
        "date": "2026-08-13", "dataset_version": config["dataset_version"],
        "split_version": config["split_version"], "model": config["model"],
        "model_revision": config["model_revision"], "prompt_version": config["prompt_version"],
        "seed": int(config["base_seed"]),
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            **config,
            "ground_truth_sha256": file_sha256(args.audit),
            "reference_policy": "source values used only for post-decision scoring",
            "source_workbook_sha256": file_sha256(workbook),
            "source_acquisition_sha256": file_sha256(acquisition),
            "source_audit_sha256": file_sha256(args.audit),
            "coordinate_origin_persisted": False,
            "source_identifiers_persisted": False,
        },
    })

    conditions, rows = [], []
    for magnitude_index, magnitude_value in enumerate(config["magnitudes_m"]):
        magnitude = float(magnitude_value)
        raw_repetitions, qc_repetitions, mean_repetitions = [], [], []
        coverage_values, false_accept_values = [], []
        for repetition in range(int(config["repetitions"])):
            seed_a = int(config["base_seed"]) + magnitude_index * 10000 + repetition * 2
            seed_b = seed_a + 1
            left, corrupted_a = corrupt_channel(surface.points, magnitude, float(config["per_channel_error_rate"]), seed_a)
            right, corrupted_b = corrupt_channel(surface.points, magnitude, float(config["per_channel_error_rate"]), seed_b)
            accepted, rejected = consensus_points(left, right)
            mean_fused = mean_fusion_points(left, right)
            raw_prediction = [idw_predict(left, x, y) for x, y in queries]
            qc_prediction = [idw_predict(accepted, x, y) for x, y in queries]
            mean_prediction = [idw_predict(mean_fused, x, y) for x, y in queries]
            raw_metrics = surface_error_metrics(reference, raw_prediction)
            qc_metrics = surface_error_metrics(reference, qc_prediction)
            mean_metrics = surface_error_metrics(reference, mean_prediction)
            false_accepted = len((corrupted_a & corrupted_b) - set(rejected))
            coverage = len(accepted) / len(surface.points)
            raw_repetitions.append(raw_metrics); qc_repetitions.append(qc_metrics)
            mean_repetitions.append(mean_metrics)
            coverage_values.append(coverage); false_accept_values.append(false_accepted)
            rows.append({
                "magnitude_m": magnitude, "repetition": repetition,
                "seed_a": seed_a, "seed_b": seed_b,
                "corrupted_a": len(corrupted_a), "corrupted_b": len(corrupted_b),
                "accepted_points": len(accepted), "rejected_points": len(rejected),
                "false_accepted_corruptions": false_accepted, "coverage": coverage,
                "raw": raw_metrics, "qc": qc_metrics, "mean_fusion": mean_metrics,
            })
        conditions.append({
            "magnitude_m": magnitude,
            "raw": aggregate_repeated_metrics(raw_repetitions),
            "qc": aggregate_repeated_metrics(qc_repetitions),
            "mean_fusion": aggregate_repeated_metrics(mean_repetitions),
            "mean_fusion_vs_raw_paired": paired_improvement_summary(
                raw_repetitions, mean_repetitions,
            ),
            "coverage_mean": sum(coverage_values) / len(coverage_values),
            "false_accepted_corruptions_total": sum(false_accept_values),
        })
    elapsed = time.perf_counter() - started
    metrics = {
        "scope": "real structured-source controlled downstream consensus-QC evaluation",
        "data_status": "real_structured_source_controlled_error_injection",
        "comparison": config["comparison"],
        "reference_ground_truth_tier": "AUTHORITATIVE_STRUCTURED_SOURCE",
        "source_record_count": len(surface.points), "query_points": len(queries),
        "repetitions_per_condition": int(config["repetitions"]),
        "per_channel_error_rate": float(config["per_channel_error_rate"]),
        "coordinate_origin_persisted": False, "source_identifier_values_persisted": False,
        "conditions": conditions, "latency_seconds_total": elapsed,
        "image_extraction_evidence": False, "human_ground_truth_evidence": False,
    }
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (run / "predictions.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    (run / "run.log").write_text(
        f"status=completed\nsource_records={len(surface.points)}\nquery_points={len(queries)}\n"
        f"repetitions={config['repetitions']}\nlatency_seconds_total={elapsed:.9f}\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
