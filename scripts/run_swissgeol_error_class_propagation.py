#!/usr/bin/env python3
"""Run multi-seed controlled downstream error-class propagation on Swissgeol.

The authoritative interval and spatial records are used as the unperturbed
reference.  Each condition injects one known error class, then evaluates the
perturbed ordered sequence directly on fixed reference-derived query grids.
No reference-guided correction is applied before interpolation.
"""

from __future__ import annotations

import argparse
import json
import platform
import resource
import subprocess
import time
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from geologparser.evaluation.error_class_propagation import (
    OrderedBoundaryRecord,
    evaluate_error_propagation,
    inject_error_class,
    prepare_reference_surfaces,
    summarize_scalar,
)
from geologparser.evaluation.error_propagation import aggregate_repeated_metrics
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(
    "/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v003/"
    "gold_interval_manifest_heldout_v003.jsonl"
)


def load_reference(manifest_path: Path) -> list[OrderedBoundaryRecord]:
    manifest = [
        json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records = []
    for item in manifest:
        reference_path = Path(item["reference_path"])
        if file_sha256(reference_path) != item["reference_sha256"]:
            raise ValueError(f"reference hash mismatch: {reference_path}")
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        borehole = reference["borehole"]
        intervals = sorted(
            reference["stratigraphy"]["intervals"],
            key=lambda value: (
                float(value["top_depth_m"]), float(value["bottom_depth_m"]),
            ),
        )
        boundaries = tuple(float(value["bottom_depth_m"]) for value in intervals)
        if any(second <= first for first, second in zip(boundaries, boundaries[1:])):
            raise ValueError(f"non-monotonic authoritative boundaries: {item['record_id']}")
        records.append(OrderedBoundaryRecord(
            record_id=item["record_id"],
            x=float(borehole["x_coordinate"]),
            y=float(borehole["y_coordinate"]),
            collar_elevation_m=float(borehole["collar_elevation_m"]),
            boundaries_m=boundaries,
        ))
    if len(records) < 3:
        raise ValueError("at least three authoritative records are required")
    return records


def summarize_repetitions(repetitions: list[dict]) -> dict:
    surface_rows = [row["surface_error"] for row in repetitions]
    return {
        "repetitions": len(repetitions),
        "surface_error": aggregate_repeated_metrics(surface_rows),
        "boundary_mae_m": summarize_scalar([
            float(row["boundary_mae_m"]) for row in repetitions
            if row["boundary_mae_m"] is not None
        ]),
        "spatial_support_coverage": summarize_scalar([
            float(row["spatial_support_coverage"]) for row in repetitions
        ]),
        "topological_mismatch_document_rate": summarize_scalar([
            float(row["topology"]["mismatched_document_rate"])
            for row in repetitions
        ]),
        "boundary_count_absolute_difference": summarize_scalar([
            float(row["topology"]["boundary_count_absolute_difference"])
            for row in repetitions
        ]),
        "positional_mismatch_count": summarize_scalar([
            float(row["topology"]["positional_mismatch_count"])
            for row in repetitions
        ]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path,
        default=ROOT / "configs/experiments/P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002.yaml",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if config["paper_eligibility"] != "formal_authoritative_controlled_error_downstream":
        raise ValueError("unexpected paper eligibility")

    reference = load_reference(args.manifest)
    prepared = prepare_reference_surfaces(reference, int(config["grid_size"]))
    clean = evaluate_error_propagation(reference, reference, prepared)
    if clean["surface_error"]["mae_m"] != 0 or clean["spatial_support_coverage"] != 1:
        raise ValueError("clean reference self-check failed")

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        capture_output=True, check=True,
    ).stdout.strip()
    started_utc = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": config["experiment_id"],
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": config["dataset_version"],
        "split_version": config["split_version"],
        "model": config["model"],
        "model_revision": config["model_revision"],
        "prompt_version": config["prompt_version"],
        "seed": int(config["base_seed"]),
        "hardware": {
            "device": "cpu", "processor": platform.processor(), "gpu_used": False,
        },
        "software": {"python": platform.python_version()},
        "config": {
            **config,
            "ground_truth_sha256": file_sha256(args.manifest),
            "reference_policy": "authoritative values used for injection and post-injection scoring",
            "prediction_reference_conditioning": "controlled_injection_only_no_reference_guided_repair",
            "coordinate_system": "CH1903+/LV95",
            "spatial_metadata_source": "authoritative structured borehole records",
            "query_domain": "fixed per-boundary authoritative reference convex hull",
            "interpolator": "IDW_power_2",
            "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        },
        "started_utc": started_utc.isoformat(),
    })

    wall_start = time.perf_counter()
    condition_summaries = []
    prediction_rows = []
    condition_index = 0
    for error_type, specification in config["conditions"].items():
        for severity_index, value in enumerate(specification["values"]):
            repetitions = []
            for repetition in range(int(config["repetitions"])):
                seed = int(config["base_seed"]) + condition_index * 1000 + repetition
                prediction, audit = inject_error_class(
                    reference, error_type, float(value), seed,
                    affected_fraction=float(config["affected_fraction_numeric"]),
                )
                evaluated = evaluate_error_propagation(reference, prediction, prepared)
                repetitions.append(evaluated)
                prediction_rows.append({
                    "error_type": error_type,
                    "error_family": specification["family"],
                    "severity_index": severity_index + 1,
                    "parameter": float(value),
                    "parameter_unit": specification["unit"],
                    "repetition": repetition,
                    "seed": seed,
                    "affected_operation_count": len(audit),
                    "affected_operations": audit,
                    "evaluation": evaluated,
                })
            condition_summaries.append({
                "error_type": error_type,
                "error_family": specification["family"],
                "severity_index": severity_index + 1,
                "parameter": float(value),
                "parameter_unit": specification["unit"],
                **summarize_repetitions(repetitions),
            })
            condition_index += 1

    elapsed = time.perf_counter() - wall_start
    reference_point_count = sum(
        len(item["record_ids"]) for item in prepared
    )
    query_count = sum(len(item["queries"]) for item in prepared)
    metrics = {
        "scope": "authoritative controlled multi-error downstream propagation evaluation",
        "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "data_status": "real_authoritative_records_controlled_error_injection",
        "comparison": "clean_authoritative_reference_vs_independently_injected_error_classes",
        "human_ground_truth_evidence": False,
        "prediction_reference_conditioning": "controlled_injection_only_no_reference_guided_repair",
        "fixed_reference_query_domain": True,
        "document_count": len(reference),
        "boundary_count": len(prepared),
        "reference_point_count": reference_point_count,
        "query_count": query_count,
        "error_type_count": len(config["conditions"]),
        "condition_count": len(condition_summaries),
        "repetitions_per_condition": int(config["repetitions"]),
        "total_repetitions": len(prediction_rows),
        "clean_reference_self_comparison": clean,
        "conditions": condition_summaries,
        "error_type_definitions": {
            "boundary_shift": "one ordered depth value is displaced while strict order is retained",
            "coordinate_shift": "one borehole location is displaced without changing boundary values",
            "missing_boundary": "one ordered boundary slot is unavailable without shifting deeper slots",
            "merged_layer": "one internal boundary is deleted, merging adjacent layers and shifting deeper positions",
            "split_layer": "one midpoint boundary is inserted, splitting a layer and shifting deeper positions",
            "duplicate_boundary": "one boundary is duplicated, creating a non-strict sequence and positional shift",
        },
        "alignment_policy": "ordered boundary index; no reference-guided repair or rematching",
        "spatial_metadata_limitation": "coordinates and collar elevations are authoritative structured fields, not image-derived predictions",
        "selection_limitation": "one canton/source family, 35 held-out records, and at most four ordered boundaries",
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        "wall_time_seconds": elapsed,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in prediction_rows),
        encoding="utf-8",
    )
    (run / "errors.jsonl").write_text("", encoding="utf-8")
    (run / "run.log").write_text(
        f"started_utc={started_utc.isoformat()}\n"
        f"documents={len(reference)}\nreference_points={reference_point_count}\n"
        f"query_points={query_count}\nconditions={len(condition_summaries)}\n"
        f"total_repetitions={len(prediction_rows)}\n"
        f"wall_time_seconds={elapsed:.9f}\nstatus=completed\n",
        encoding="utf-8",
    )
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
