#!/usr/bin/env python3
"""Evaluate frozen direct-text spatial parsing on an external Swissgeol set."""

from __future__ import annotations

import argparse
import json
import math
import platform
from geologparser.runtime_resources import peak_process_rss_kib
import subprocess
import time
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import mean

import yaml

from geologparser.experiment import create_run_directory
from geologparser.extraction.swissgeol_spatial import parse_swissgeol_spatial_text
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(
    "/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v003/"
    "spatial_external_manifest_v001.jsonl"
)


def ratio(numerator: int, denominator: int) -> dict:
    return {
        "value": numerator / denominator if denominator else None,
        "numerator": numerator,
        "denominator": denominator,
    }


def error_summary(errors: list[float]) -> dict:
    return {
        "count": len(errors),
        "mae": mean(abs(value) for value in errors) if errors else None,
        "rmse": math.sqrt(mean(value * value for value in errors)) if errors else None,
        "max_abs_error": max(abs(value) for value in errors) if errors else None,
    }


def first_page_text(pdf_path: Path) -> str:
    completed = subprocess.run(
        ["pdftotext", "-layout", "-f", "1", "-l", "1", str(pdf_path), "-"],
        text=True, capture_output=True, check=True,
    )
    return completed.stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path,
        default=ROOT / "configs/experiments/P3_SWISSGEOL_EXTERNAL_SPATIAL_METADATA_002.yaml",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if config["paper_eligibility"] != "formal_authoritative_spatial_extraction":
        raise ValueError("unexpected paper eligibility")
    manifest = [
        json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not manifest or any(row["spatial_evaluation_role"] != "external_all_records_outside_interval_v003" for row in manifest):
        raise ValueError("unexpected external spatial manifest")

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        capture_output=True, check=True,
    ).stdout.strip()
    started_utc = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": config["experiment_id"],
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": config["dataset_version"],
        "split_version": config["split_version"],
        "model": config["model"],
        "model_revision": config["model_revision"],
        "prompt_version": config["prompt_version"],
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {
            "python": platform.python_version(),
            "pdftotext": subprocess.run(
                ["pdftotext", "-v"], text=True, capture_output=True,
            ).stderr.splitlines()[0],
        },
        "config": {
            **config,
            "ground_truth_sha256": file_sha256(args.manifest),
            "prediction_reference_conditioning": "none",
            "development_split": "gold_interval_manifest_development_v003",
            "development_evaluation_overlap_count": 0,
            "external_selection_uses_document_content": False,
            "external_selection_uses_spatial_reference_values": False,
            "reference_policy": "official database values used only after page-text prediction is frozen",
            "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        },
        "started_utc": started_utc.isoformat(),
    })

    wall = time.perf_counter()
    predictions = []
    coordinate_status = Counter()
    collar_status = Counter()
    x_errors: list[float] = []
    y_errors: list[float] = []
    collar_errors: list[float] = []
    pair_exact = x_exact = y_exact = collar_exact = 0
    errors = []
    for row in manifest:
        pdf_path = Path(row["pdf_path"])
        reference_path = Path(row["reference_path"])
        if file_sha256(pdf_path) != row["pdf_sha256"]:
            raise ValueError(f"PDF hash mismatch: {pdf_path}")
        if file_sha256(reference_path) != row["reference_sha256"]:
            raise ValueError(f"reference hash mismatch: {reference_path}")
        reference = json.loads(reference_path.read_text(encoding="utf-8"))["borehole"]
        prediction = parse_swissgeol_spatial_text(first_page_text(pdf_path))
        coordinate_status[prediction.coordinate_status] += 1
        collar_status[prediction.collar_status] += 1
        x_reference = float(reference["x_coordinate"])
        y_reference = float(reference["y_coordinate"])
        collar_reference = float(reference["collar_elevation_m"])
        if prediction.x_coordinate is not None:
            x_error = prediction.x_coordinate - x_reference
            y_error = prediction.y_coordinate - y_reference
            x_errors.append(x_error); y_errors.append(y_error)
            x_exact += x_error == 0
            y_exact += y_error == 0
            pair_exact += x_error == 0 and y_error == 0
            if x_error != 0 or y_error != 0:
                errors.append({
                    "record_id": row["record_id"],
                    "error_type": "PAGE_DATABASE_COORDINATE_DISAGREEMENT",
                    "x_absolute_difference_m": abs(x_error),
                    "y_absolute_difference_m": abs(y_error),
                    "interpretation": "may reflect page/database source disagreement or text extraction error",
                })
        if prediction.collar_elevation_m is not None:
            collar_error = prediction.collar_elevation_m - collar_reference
            collar_errors.append(collar_error)
            collar_exact += collar_error == 0
            if collar_error != 0:
                errors.append({
                    "record_id": row["record_id"],
                    "error_type": "PAGE_DATABASE_COLLAR_DISAGREEMENT",
                    "absolute_difference_m": abs(collar_error),
                })
        predictions.append({
            "record_id": row["record_id"],
            "prediction": {
                "x_coordinate": prediction.x_coordinate,
                "y_coordinate": prediction.y_coordinate,
                "collar_elevation_m": prediction.collar_elevation_m,
                "coordinate_status": prediction.coordinate_status,
                "collar_status": prediction.collar_status,
                "coordinate_candidate_count": prediction.coordinate_candidate_count,
                "coordinate_source_text": prediction.coordinate_source_text,
                "collar_source_text": prediction.collar_source_text,
                "coordinate_system_inference": "CH1903+/LV95_from_strict_numeric_range",
            },
            "reference": {
                "x_coordinate": x_reference,
                "y_coordinate": y_reference,
                "collar_elevation_m": collar_reference,
                "coordinate_system": reference["coordinate_system"],
            },
        })

    document_count = len(manifest)
    coordinate_prediction_count = len(x_errors)
    collar_prediction_count = len(collar_errors)
    elapsed = time.perf_counter() - wall
    metrics = {
        "scope": "authoritative heldout spatial-metadata extraction evaluation",
        "reference_ground_truth_tier": "AUTHORITATIVE_METADATA",
        "data_status": "native_pdf_direct_text_vs_authoritative_spatial_record",
        "comparison": "page_explicit_spatial_values_vs_authoritative_database",
        "prediction_reference_conditioning": "none",
        "development_evaluation_overlap_count": 0,
        "human_ground_truth_evidence": False,
        "document_count": document_count,
        "coordinate_reference_count": document_count,
        "coordinate_prediction_count": coordinate_prediction_count,
        "coordinate_pair_coverage": ratio(coordinate_prediction_count, document_count),
        "coordinate_pair_exact_over_all": ratio(pair_exact, document_count),
        "coordinate_pair_exact_when_predicted": ratio(pair_exact, coordinate_prediction_count),
        "x_exact_when_predicted": ratio(x_exact, coordinate_prediction_count),
        "y_exact_when_predicted": ratio(y_exact, coordinate_prediction_count),
        "x_error_m": error_summary(x_errors),
        "y_error_m": error_summary(y_errors),
        "coordinate_status_counts": dict(sorted(coordinate_status.items())),
        "page_database_coordinate_disagreement_count": coordinate_prediction_count - pair_exact,
        "collar_reference_count": document_count,
        "collar_prediction_count": collar_prediction_count,
        "collar_coverage": ratio(collar_prediction_count, document_count),
        "collar_exact_when_predicted": ratio(collar_exact, collar_prediction_count),
        "collar_error_m": error_summary(collar_errors),
        "collar_status_counts": dict(sorted(collar_status.items())),
        "coordinate_system_accuracy_evaluated": False,
        "coordinate_system_note": "LV95 is inferred from numeric shape; the page line generally does not state a CRS",
        "evaluation_semantics": "database disagreement is not automatically attributed to recognition because page and database values can differ",
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        "wall_time_seconds": elapsed,
        "latency_seconds_per_document": elapsed / document_count,
        "peak_process_rss_kib": peak_process_rss_kib(),
    }
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in predictions),
        encoding="utf-8",
    )
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in errors),
        encoding="utf-8",
    )
    (run / "run.log").write_text(
        f"started_utc={started_utc.isoformat()}\nstatus=completed\n"
        f"documents={document_count}\ncoordinate_predictions={coordinate_prediction_count}\n"
        f"collar_predictions={collar_prediction_count}\nwall_time_seconds={elapsed:.9f}\n",
        encoding="utf-8",
    )
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
