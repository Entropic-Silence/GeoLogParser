#!/usr/bin/env python3
"""Propagate frozen page coordinates and image boundaries to a fixed surface.

Page coordinates and interval predictions are frozen without reference access.
Authoritative collar elevations are still supplied because the evaluated pages
do not expose usable collar elevations; this is therefore a partial, explicitly
bounded spatial workflow rather than a complete end-to-end experiment.
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
from statistics import mean

from geologparser.evaluation.error_class_propagation import fixed_reference_grid
from geologparser.evaluation.error_propagation import SurfacePoint, idw_predict, surface_error_metrics
from geologparser.experiment import create_run_directory
from geologparser.extraction.swissgeol_spatial import parse_swissgeol_spatial_text
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(
    "/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v003/"
    "gold_interval_manifest_heldout_v003.jsonl"
)
DEFAULT_BOUNDARIES = ROOT / "results/2026-08-14/P2_SWISSGEOL_TG_CONSTRAINT_REREAD_HELDOUT_V003_001"


def first_page_text(pdf_path: Path) -> str:
    return subprocess.run(
        ["pdftotext", "-layout", "-f", "1", "-l", "1", str(pdf_path), "-"],
        text=True, capture_output=True, check=True,
    ).stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default="P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--boundary-run", type=Path, default=DEFAULT_BOUNDARIES)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--grid-size", type=int, default=25)
    args = parser.parse_args()
    boundary_path = args.boundary_run / "predictions.jsonl"
    boundary_predictions = {
        item["record_id"]: item for item in (
            json.loads(line) for line in boundary_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    manifest = [
        json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if set(boundary_predictions) != {row["record_id"] for row in manifest}:
        raise ValueError("boundary predictions and evaluation manifest must match exactly")

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        capture_output=True, check=True,
    ).stdout.strip()
    started_utc = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": "swissgeol_thurgau_v003_page_coordinate_surface",
        "split_version": "v003_heldout_frozen_boundary_and_spatial_parsers",
        "model": "direct_text_coordinate_plus_frozen_image_boundary_plus_idw",
        "model_revision": "swissgeol_spatial_v002_and_frozen_p2_v2",
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "ground_truth_sha256": file_sha256(args.manifest),
            "boundary_prediction_sha256": file_sha256(boundary_path),
            "boundary_prediction_run": str(args.boundary_run),
            "prediction_reference_conditioning": "none",
            "reference_blinded_decision_policy": True,
            "coordinate_parser": "swissgeol_spatial_v002_strict_unambiguous",
            "coordinate_multiple_candidate_policy": "abstain",
            "collar_source": "authoritative_structured_record_due_zero_page_extraction_coverage",
            "grid_size": args.grid_size,
            "query_domain": "fixed_authoritative_first_boundary_convex_hull",
            "interpolator": "IDW_power_2",
            "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        },
        "started_utc": started_utc.isoformat(),
    })

    wall = time.perf_counter()
    records = []
    coordinate_exact = 0
    for item in manifest:
        reference_path = Path(item["reference_path"])
        pdf_path = Path(item["pdf_path"])
        if file_sha256(reference_path) != item["reference_sha256"]:
            raise ValueError(f"reference hash mismatch: {reference_path}")
        if file_sha256(pdf_path) != item["pdf_sha256"]:
            raise ValueError(f"PDF hash mismatch: {pdf_path}")
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        borehole = reference["borehole"]
        intervals = sorted(
            reference["stratigraphy"]["intervals"],
            key=lambda value: (float(value["top_depth_m"]), float(value["bottom_depth_m"])),
        )
        coordinate = parse_swissgeol_spatial_text(first_page_text(pdf_path))
        boundary = boundary_predictions[item["record_id"]]
        if coordinate.x_coordinate is not None:
            coordinate_exact += (
                coordinate.x_coordinate == float(borehole["x_coordinate"])
                and coordinate.y_coordinate == float(borehole["y_coordinate"])
            )
        records.append({
            "record_id": item["record_id"],
            "reference_x": float(borehole["x_coordinate"]),
            "reference_y": float(borehole["y_coordinate"]),
            "page_x": coordinate.x_coordinate,
            "page_y": coordinate.y_coordinate,
            "coordinate_status": coordinate.coordinate_status,
            "collar": float(borehole["collar_elevation_m"]),
            "reference_depth": float(intervals[0]["bottom_depth_m"]),
            "raw_depth": (
                float(boundary["first_pass_intervals"][0]["bottom_depth_m"])
                if boundary["first_pass_intervals"] else None
            ),
            "final_depth": (
                float(boundary["final_intervals"][0]["bottom_depth_m"])
                if boundary["final_intervals"] else None
            ),
            "decision": boundary["decision"],
        })

    reference_points = [
        SurfacePoint(
            row["reference_x"], row["reference_y"],
            row["collar"] - row["reference_depth"], row["record_id"],
        ) for row in records
    ]
    queries = fixed_reference_grid(reference_points, args.grid_size)
    reference_surface = [idw_predict(reference_points, x, y) for x, y in queries]

    variants = {}
    specifications = {
        "page_coordinate_reference_boundary": ("page", "reference_depth"),
        "page_coordinate_raw_boundary": ("page", "raw_depth"),
        "page_coordinate_reread_boundary": ("page", "final_depth"),
        "authoritative_coordinate_reread_boundary": ("reference", "final_depth"),
    }
    prediction_rows = []
    for name, (coordinate_source, depth_field) in specifications.items():
        available = [
            row for row in records
            if row[depth_field] is not None
            and (coordinate_source == "reference" or row["page_x"] is not None)
        ]
        points = [
            SurfacePoint(
                row["reference_x"] if coordinate_source == "reference" else row["page_x"],
                row["reference_y"] if coordinate_source == "reference" else row["page_y"],
                row["collar"] - row[depth_field], row["record_id"],
            ) for row in available
        ]
        predicted_surface = [idw_predict(points, x, y) for x, y in queries]
        depth_errors = [abs(row[depth_field] - row["reference_depth"]) for row in available]
        variants[name] = {
            "point_count": len(points),
            "coverage": len(points) / len(reference_points),
            "boundary_mae_m": mean(depth_errors) if depth_errors else None,
            "surface_error": surface_error_metrics(reference_surface, predicted_surface),
        }
        prediction_rows.extend({
            "variant": name,
            "record_id": row["record_id"],
            "x": row["reference_x"] if coordinate_source == "reference" else row["page_x"],
            "y": row["reference_y"] if coordinate_source == "reference" else row["page_y"],
            "collar_elevation_m": row["collar"],
            "boundary_depth_m": row[depth_field],
            "coordinate_status": row["coordinate_status"],
            "decision": row["decision"],
        } for row in available)

    coordinate_count = sum(row["page_x"] is not None for row in records)
    elapsed = time.perf_counter() - wall
    metrics = {
        "scope": "real page-coordinate image-boundary downstream surface diagnostic",
        "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "data_status": "real_pdf_page_coordinates_image_boundaries_authoritative_collar",
        "comparison": "authoritative_reference_vs_page_coordinate_reference_boundary_vs_page_coordinate_raw_and_reread_boundary",
        "prediction_reference_conditioning": "none",
        "reference_blinded_decision_policy": True,
        "human_ground_truth_evidence": False,
        "document_count": len(records),
        "reference_point_count": len(reference_points),
        "query_count": len(queries),
        "page_coordinate_prediction_count": coordinate_count,
        "page_coordinate_coverage": coordinate_count / len(records),
        "page_coordinate_database_exact_count": coordinate_exact,
        "page_collar_prediction_count": 0,
        "authoritative_collar_supplied_count": len(records),
        "variants": variants,
        "collar_limitation": "all collar elevations are authoritative structured values because the frozen page parser abstained on every held-out page",
        "coordinate_limitation": "page/database coordinate disagreement is not automatically attributed to recognition",
        "selection_limitation": "one canton/source family and the first ordered boundary",
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
        f"started_utc={started_utc.isoformat()}\nstatus=completed\n"
        f"documents={len(records)}\npage_coordinate_predictions={coordinate_count}\n"
        f"query_points={len(queries)}\nwall_time_seconds={elapsed:.9f}\n",
        encoding="utf-8",
    )
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
