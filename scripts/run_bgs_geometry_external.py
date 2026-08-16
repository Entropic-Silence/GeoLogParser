#!/usr/bin/env python3
"""Run the frozen BGS v023 model once on an untouched external manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np

from geologparser.layout import LogisticCandidateRanker
from scripts.analyze_bgs_column_gate import Ranker, build_columns, gated_candidates
from scripts.analyze_bgs_geometry_refinement import refine_sequence
from scripts.run_bgs_layout_method_development import (
    PlattCalibrator,
    boundary_metrics,
    generate_document_candidates,
    interval_metrics,
    predict_family_rankers,
    serialize_candidate,
    monotonic_sequence,
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_run_hash(source_run: Path) -> str:
    candidate = source_run / "predictions.jsonl"
    if not candidate.exists():
        candidate = source_run / "source_run_manifest.json"
    return file_sha256(candidate)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def references(source: dict) -> list[float]:
    return sorted(
        {float(interval[key]) for interval in source["intervals"] for key in ("top_depth_m", "bottom_depth_m")}
    )


def load_column_ranker(values: dict) -> Ranker:
    ranker = Ranker()
    ranker.mean = np.asarray(values["mean"], dtype=float)
    ranker.scale = np.asarray(values["scale"], dtype=float)
    ranker.weights = np.asarray(values["weights"], dtype=float)
    ranker.bias = float(values["bias"])
    return ranker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--multiscale-analysis", type=Path, required=True)
    parser.add_argument("--field-roi-analysis", type=Path, required=True)
    parser.add_argument("--frozen-model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", default="P2_BGS_V023_EXTERNAL_V002_001")
    parser.add_argument("--evaluation-role", choices=("external", "validation"), default="external")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"one-time external output already exists: {args.output}")
    started = time.perf_counter()

    frozen = json.loads(args.frozen_model.read_text())
    if frozen["status"] != "frozen_before_external_evaluation":
        raise ValueError("external model is not frozen")
    if args.evaluation_role == "external" and frozen["external_protocol"]["dataset"] != "bgs_offshore_gold_v002":
        raise ValueError("frozen model names a different external dataset")
    base_model_path = Path(frozen["base_candidate_model"])
    if file_sha256(base_model_path) != frozen["base_candidate_model_sha256"]:
        raise ValueError("base candidate model hash mismatch")
    if file_sha256(args.manifest) == frozen["development_manifest_sha256"]:
        raise ValueError("external manifest equals the development manifest")

    sources = load_jsonl(args.manifest)
    multiscale_report = json.loads(args.multiscale_analysis.read_text())
    field_report = json.loads(args.field_roi_analysis.read_text())
    multiscale = {
        row["record_id"]: {"record_id": row["record_id"], "page_layout": row["page_layout"]}
        for row in multiscale_report["documents"]
    }
    field_documents = {
        row["record_id"]: {"record_id": row["record_id"], "pages": row["pages"]}
        for row in field_report["documents"]
    }
    sanitized_field_report = {"documents": list(field_documents.values())}

    base_model = json.loads(base_model_path.read_text())
    rankers = {
        family: LogisticCandidateRanker.from_dict(values)
        for family, values in base_model["experts"].items()
    }
    calibrator = PlattCalibrator()
    calibrator.slope = float(base_model["calibrator"]["slope"])
    calibrator.intercept = float(base_model["calibrator"]["intercept"])
    column_ranker = load_column_ranker(frozen["column_gate"]["model"])
    full_threshold = float(frozen["sequence_decoder"]["full_sequence_threshold"])
    selective_threshold = float(frozen["sequence_decoder"]["selective_threshold"])
    geometry = frozen["geometry_refinement"]
    geometry_parameters = (
        float(geometry["integer_snap_radius_m"]),
        int(geometry["continuous_depth_decimal_places"]),
        float(geometry["maximum_page_scale_rmse"]),
    )

    # Prediction creation is reference-blind.  The interval arrays remain in
    # the manifest rows but are not passed to candidate generation or ranking.
    predictions = {}
    selective_predictions = {}
    evidence = {}
    selective_evidence = {}
    diagnostic_rows = []
    for source in sources:
        record_id = source["record_id"]
        generation_source = {
            "record_id": record_id,
            "evaluation_pages": list(source["evaluation_pages"]),
        }
        generated = generate_document_candidates(
            generation_source,
            multiscale[record_id],
            args.source_run,
            field_roi=sanitized_field_report,
            graphic_mode="multi",
        )
        raw_probabilities = predict_family_rankers(rankers, generated["all"])
        probabilities = calibrator.transform(raw_probabilities)
        serialized = {
            "record_id": record_id,
            "ranked_candidates": [
                serialize_candidate(candidate, probability)
                for candidate, probability in zip(generated["all"], probabilities)
            ],
        }
        columns = build_columns(serialized, [])
        column_scores = column_ranker.predict(columns).tolist()
        gated, gated_probabilities = gated_candidates(
            serialized,
            columns,
            column_scores,
            int(frozen["column_gate"]["top_k_columns_per_page"]),
            float(frozen["column_gate"]["column_score_power"]),
        )
        full_sequence = monotonic_sequence(gated, gated_probabilities, full_threshold)
        selective_sequence = monotonic_sequence(gated, gated_probabilities, selective_threshold)
        predictions[record_id], evidence[record_id] = refine_sequence(full_sequence, geometry_parameters)
        selective_predictions[record_id], selective_evidence[record_id] = refine_sequence(
            selective_sequence, geometry_parameters,
        )
        diagnostic_rows.append(
            {
                "record_id": record_id,
                "page_count": len(source["evaluation_pages"]),
                "layout_detected_pages": sum(bool(page["layout_detected"]) for page in generated["pages"]),
                "candidate_count": len(generated["all"]),
                "graphic_column_count": len(columns),
                "gated_candidate_count": len(gated),
                "predicted_boundaries_m": predictions[record_id],
                "selective_boundaries_m": selective_predictions[record_id],
                "evidence": evidence[record_id],
                "selective_evidence": selective_evidence[record_id],
            }
        )

    # References are accessed only after every external prediction is fixed.
    references_by_id = {source["record_id"]: references(source) for source in sources}
    metrics_by_tolerance = {}
    for tolerance in (0.01, 0.05, 0.10):
        metrics_by_tolerance[f"{tolerance:.2f}"] = {
            "boundary": boundary_metrics(predictions, references_by_id, tolerance),
            "interval": interval_metrics(predictions, references_by_id, tolerance),
        }
    selective_boundary = boundary_metrics(selective_predictions, references_by_id, 0.05)
    selective_interval = interval_metrics(selective_predictions, references_by_id, 0.05)
    accepted = sum(map(len, selective_predictions.values()))
    reference_count = sum(map(len, references_by_id.values()))
    provenance_count = sum(map(len, evidence.values()))
    provenance_complete = sum(
        1
        for rows in evidence.values()
        for row in rows
        if row["page"] >= 0 and len(row["bbox"]) == 4
    )
    report = {
        "experiment_id": args.experiment_id,
        "status": f"completed_{args.evaluation_role}_evaluation",
        "evaluation_role": args.evaluation_role,
        "method_version": frozen["model_id"],
        "git_commit_before_external": "9ce6fd6",
        "manifest": str(args.manifest),
        "manifest_sha256": file_sha256(args.manifest),
        "frozen_model": str(args.frozen_model),
        "frozen_model_sha256": file_sha256(args.frozen_model),
        "source_run": str(args.source_run),
        "source_regions_sha256": source_run_hash(args.source_run),
        "multiscale_analysis": str(args.multiscale_analysis),
        "multiscale_analysis_sha256": file_sha256(args.multiscale_analysis),
        "field_roi_analysis": str(args.field_roi_analysis),
        "field_roi_analysis_sha256": file_sha256(args.field_roi_analysis),
        "document_count": len(sources),
        "page_count": sum(len(source["evaluation_pages"]) for source in sources),
        "reference_interval_count": sum(len(source["intervals"]) for source in sources),
        "reference_boundary_count": reference_count,
        "metrics_by_tolerance_m": metrics_by_tolerance,
        "selective_operating_point": {
            "threshold": selective_threshold,
            "accepted_boundary_count": accepted,
            "coverage_against_reference": accepted / reference_count,
            "boundary": selective_boundary,
            "interval": selective_interval,
        },
        "provenance": {
            "complete_boundary_count": provenance_complete,
            "total_boundary_count": provenance_count,
            "complete_rate": provenance_complete / provenance_count if provenance_count else 0.0,
        },
        "predictions": diagnostic_rows,
        "reference_blinding": "all predictions fixed before external interval references were accessed for scoring",
        "post_external_policy": "no tuning; any method change demotes the set to validation" if args.evaluation_role == "external" else "validation evidence may support subsequent development",
        "wall_time_seconds": time.perf_counter() - started,
        "latency_seconds_per_page": (time.perf_counter() - started) / sum(len(source["evaluation_pages"]) for source in sources),
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("document_count", "page_count", "metrics_by_tolerance_m", "selective_operating_point", "provenance", "wall_time_seconds", "latency_seconds_per_page", "peak_process_rss_kib")}, indent=2))


if __name__ == "__main__":
    main()
