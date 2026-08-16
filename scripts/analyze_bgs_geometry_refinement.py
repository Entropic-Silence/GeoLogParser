#!/usr/bin/env python3
"""Source-disjoint continuous-depth geometry refinement for BGS v022.

The v022 decoder deliberately snaps graphical events to a conservative depth
grid.  This analysis restores calibrated continuous depth only when the page
scale residual is sufficiently small.  Integer-looking events remain snapped;
other events retain one or two calibrated decimal places.  Every refinement
parameter is selected on the other source folds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import time

from scripts.analyze_bgs_column_gate import gated_candidates
from scripts.run_bgs_layout_method_development import (
    boundary_metrics,
    interval_metrics,
    monotonic_sequence,
)


INTEGER_RADII = (0.0, 0.05, 0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30, 0.40, 0.50)
DECIMAL_PLACES = (1, 2)
MAX_SCALE_RMSE = (0.03, 0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 1.0)
RISK_THRESHOLDS = (0.10, 0.20, 0.30, 0.32, 0.35, 0.40, 0.50, 0.60, 0.62, 0.64, 0.65, 0.66, 0.68, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99)


def references(source: dict) -> list[float]:
    return sorted(
        {float(interval[key]) for interval in source["intervals"] for key in ("top_depth_m", "bottom_depth_m")}
    )


def candidate_sequences(source_analysis: dict, column_analysis: dict, threshold: float) -> dict[str, list]:
    predictions = {row["record_id"]: row for row in source_analysis["predictions"]}
    column_rows = {row["record_id"]: row for row in column_analysis["predictions"]}
    fold_models = {int(row["fold"]): row for row in column_analysis["fold_models"]}
    output = {}
    for record_id, prediction in predictions.items():
        stored = column_rows[record_id]
        fold_model = fold_models[int(stored["fold"])]
        columns = [SimpleNamespace(key=tuple(row["key"])) for row in stored["columns"]]
        scores = [float(row["probability"]) for row in stored["columns"]]
        candidates, probabilities = gated_candidates(
            prediction,
            columns,
            scores,
            int(fold_model["top_k"]),
            float(column_analysis.get("column_score_power", 0.0)),
        )
        output[record_id] = monotonic_sequence(candidates, probabilities, threshold)
    return output


def refine_sequence(sequence: list, parameters: tuple[float, int, float]) -> tuple[list[float], list[dict]]:
    integer_radius, decimal_places, maximum_scale_rmse = parameters
    values: list[float] = []
    evidence: list[dict] = []
    for candidate, probability in sequence:
        snapped_value = float(candidate.value_m)
        refined_value = snapped_value
        raw_depth = None
        used_continuous_geometry = False
        if candidate.candidate_source == "graphic_scale_transition" and candidate.provenance:
            raw_depth = candidate.provenance[0].get("raw_depth_m")
            scale_rmse = float(candidate.features.get("page_scale_rmse", 1.0))
            if raw_depth is not None and scale_rmse <= maximum_scale_rmse:
                raw_depth = float(raw_depth)
                nearest_integer = round(raw_depth)
                if abs(raw_depth - nearest_integer) <= integer_radius:
                    refined_value = float(nearest_integer)
                else:
                    refined_value = round(raw_depth, decimal_places)
                used_continuous_geometry = True
        if any(abs(refined_value - existing) <= 0.001 for existing in values):
            continue
        values.append(refined_value)
        evidence.append(
            {
                "value_m": refined_value,
                "snapped_value_m": snapped_value,
                "raw_calibrated_depth_m": raw_depth,
                "used_continuous_geometry": used_continuous_geometry,
                "probability": float(probability),
                "candidate_source": candidate.candidate_source,
                "page": int(candidate.page),
                "bbox": [float(value) for value in candidate.bbox],
                "provenance": list(candidate.provenance),
            }
        )
    ordering = sorted(range(len(values)), key=values.__getitem__)
    return [values[index] for index in ordering], [evidence[index] for index in ordering]


def apply_parameters(sequences: dict[str, list], parameters: tuple[float, int, float], record_ids: list[str]) -> tuple[dict, dict]:
    predictions = {}
    evidence = {}
    for record_id in record_ids:
        predictions[record_id], evidence[record_id] = refine_sequence(sequences[record_id], parameters)
    return predictions, evidence


def tune_parameters(sequences: dict, references_by_id: dict, record_ids: list[str]) -> tuple[tuple, dict]:
    best = None
    selected = None
    for integer_radius in INTEGER_RADII:
        for decimal_places in DECIMAL_PLACES:
            for maximum_scale_rmse in MAX_SCALE_RMSE:
                parameters = (integer_radius, decimal_places, maximum_scale_rmse)
                predictions, _ = apply_parameters(sequences, parameters, record_ids)
                references = {record_id: references_by_id[record_id] for record_id in record_ids}
                interval = interval_metrics(predictions, references, 0.05)
                boundary = boundary_metrics(predictions, references, 0.05)
                key = (
                    interval["f1"],
                    boundary["f1"],
                    boundary["precision"],
                    -integer_radius,
                    -decimal_places,
                    -maximum_scale_rmse,
                )
                if best is None or key > best:
                    best = key
                    selected = (parameters, {"interval_at_0_05m": interval, "boundary_at_0_05m": boundary})
    if selected is None:
        raise RuntimeError("no geometry-refinement parameters were evaluated")
    return selected


def parameter_dict(parameters: tuple[float, int, float]) -> dict:
    return {
        "integer_snap_radius_m": parameters[0],
        "continuous_depth_decimal_places": parameters[1],
        "maximum_page_scale_rmse": parameters[2],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-analysis", type=Path, required=True)
    parser.add_argument("--column-analysis", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()

    source_analysis = json.loads(args.source_analysis.read_text())
    column_analysis = json.loads(args.column_analysis.read_text())
    sources = {row["record_id"]: row for row in map(json.loads, args.manifest.open())}
    references_by_id = {record_id: references(row) for record_id, row in sources.items()}
    folds = {row["record_id"]: int(row["fold"]) for row in column_analysis["predictions"]}
    sequence_thresholds = {float(row["sequence_threshold"]) for row in column_analysis["fold_models"]}
    if len(sequence_thresholds) != 1:
        raise ValueError("geometry refinement requires one frozen full-sequence threshold")
    full_sequence_threshold = sequence_thresholds.pop()
    sequences = candidate_sequences(source_analysis, column_analysis, full_sequence_threshold)

    predictions = {}
    evidence = {}
    fold_models = []
    for fold in sorted(set(folds.values())):
        train_ids = [record_id for record_id in sequences if folds[record_id] != fold]
        test_ids = [record_id for record_id in sequences if folds[record_id] == fold]
        parameters, training_metrics = tune_parameters(sequences, references_by_id, train_ids)
        test_predictions, test_evidence = apply_parameters(sequences, parameters, test_ids)
        predictions.update(test_predictions)
        evidence.update(test_evidence)
        fold_models.append(
            {
                "fold": fold,
                "train_documents": len(train_ids),
                "test_documents": len(test_ids),
                "parameters": parameter_dict(parameters),
                "training_metrics": training_metrics,
            }
        )

    metrics_by_tolerance = {}
    for tolerance in (0.01, 0.05, 0.10):
        metrics_by_tolerance[f"{tolerance:.2f}"] = {
            "boundary": boundary_metrics(predictions, references_by_id, tolerance),
            "interval": interval_metrics(predictions, references_by_id, tolerance),
        }

    risk_curve = []
    fold_parameters = {
        int(row["fold"]): (
            float(row["parameters"]["integer_snap_radius_m"]),
            int(row["parameters"]["continuous_depth_decimal_places"]),
            float(row["parameters"]["maximum_page_scale_rmse"]),
        )
        for row in fold_models
    }
    for threshold in RISK_THRESHOLDS:
        threshold_sequences = candidate_sequences(source_analysis, column_analysis, threshold)
        threshold_predictions = {}
        for record_id in threshold_sequences:
            values, _ = refine_sequence(threshold_sequences[record_id], fold_parameters[folds[record_id]])
            threshold_predictions[record_id] = values
        boundary = boundary_metrics(threshold_predictions, references_by_id, 0.05)
        interval = interval_metrics(threshold_predictions, references_by_id, 0.05)
        accepted = sum(map(len, threshold_predictions.values()))
        risk_curve.append(
            {
                "threshold": threshold,
                "accepted_boundary_count": accepted,
                "coverage_against_reference": accepted / sum(map(len, references_by_id.values())),
                "boundary": boundary,
                "interval": interval,
            }
        )
    reliable = [row for row in risk_curve if row["accepted_boundary_count"] and row["boundary"]["precision"] >= 0.90]
    selective = max(reliable, key=lambda row: (row["accepted_boundary_count"], row["boundary"]["precision"])) if reliable else None

    all_ids = list(sequences)
    final_parameters, final_training_metrics = tune_parameters(sequences, references_by_id, all_ids)
    evidence_count = sum(map(len, evidence.values()))
    provenance_complete = sum(
        1
        for rows in evidence.values()
        for row in rows
        if row["page"] >= 0 and len(row["bbox"]) == 4
    )
    report = {
        "analysis_scope": "BGS v001 source-disjoint continuous-depth geometry refinement over v022",
        "source_analysis": str(args.source_analysis),
        "source_analysis_sha256": hashlib.sha256(args.source_analysis.read_bytes()).hexdigest(),
        "column_analysis": str(args.column_analysis),
        "column_analysis_sha256": hashlib.sha256(args.column_analysis.read_bytes()).hexdigest(),
        "manifest": str(args.manifest),
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "document_count": len(predictions),
        "reference_boundary_count": sum(map(len, references_by_id.values())),
        "predicted_boundary_count": evidence_count,
        "metrics_by_tolerance_m": metrics_by_tolerance,
        "coverage_risk_curve": risk_curve,
        "selective_operating_point": selective,
        "fold_models": fold_models,
        "final_model": {
            "trained_on": "all BGS v001 development source groups",
            "parameters": parameter_dict(final_parameters),
            "training_metrics": final_training_metrics,
        },
        "provenance": {
            "complete_boundary_count": provenance_complete,
            "total_boundary_count": evidence_count,
            "complete_rate": provenance_complete / evidence_count if evidence_count else 0.0,
        },
        "predictions": [
            {
                "record_id": record_id,
                "fold": folds[record_id],
                "parameters": parameter_dict(fold_parameters[folds[record_id]]),
                "predicted_boundaries_m": predictions[record_id],
                "evidence": evidence[record_id],
            }
            for record_id in sorted(predictions)
        ],
        "reference_blinding": "outer source-fold labels are used only for scoring; geometry parameters use other source folds",
        "wall_time_seconds": time.perf_counter() - started,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "metrics_at_0_05m": metrics_by_tolerance["0.05"],
                "metrics_at_0_10m": metrics_by_tolerance["0.10"],
                "selective_operating_point": selective,
                "final_model": report["final_model"],
                "provenance": report["provenance"],
                "wall_time_seconds": report["wall_time_seconds"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
