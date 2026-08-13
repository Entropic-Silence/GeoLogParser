#!/usr/bin/env python3
"""Run a protocol-only scalar-surface perturbation study on coal-602 data."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import time

import yaml

from geologparser.evaluation import (
    aggregate_repeated_metrics,
    convex_hull_xy,
    idw_predict,
    load_coal_602_roof_depth_surface,
    perturb_surface_scalar,
    regular_queries_within_hull,
    surface_error_metrics,
)
from geologparser.experiment import create_run_directory


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path(
    "/data/GeoLogParser/datasets/public/mendeley_coal_boreholes_602_v001"
)
DEFAULT_AUDIT_ROOT = Path(
    "/data/GeoLogParser/artifacts/structured_data_audits/"
    "mendeley_coal_boreholes_602_v001_audit_v002"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_config(path: Path) -> dict:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = {
        "experiment_id", "dataset_version", "source_role", "split_version", "model",
        "model_revision", "prompt_version", "base_seed", "repetitions", "grid_size",
        "magnitudes_m", "source_field", "coordinate_handling", "query_domain",
        "claims_allowed", "claims_forbidden", "paper_eligibility",
    }
    missing = sorted(required - set(config))
    if missing:
        raise ValueError(f"protocol config lacks fields: {', '.join(missing)}")
    if config["source_role"] != "source_structured_data":
        raise ValueError("coal-602 protocol requires source_structured_data role")
    if config["paper_eligibility"] != "protocol_only":
        raise ValueError("coal-602 source protocol cannot be labelled formal")
    handling = config["coordinate_handling"]
    if handling.get("persist_translation_origin") is not False:
        raise ValueError("protocol must suppress the coordinate translation origin")
    if handling.get("persist_source_identifiers") is not False:
        raise ValueError("protocol must suppress source borehole identifiers")
    if int(config["repetitions"]) < 2:
        raise ValueError("source protocol requires at least two repetitions")
    if not config["magnitudes_m"] or any(float(value) < 0 for value in config["magnitudes_m"]):
        raise ValueError("protocol magnitudes must be non-empty and non-negative")
    return config


def _verify_bound_inputs(dataset_root: Path, audit_root: Path) -> tuple[Path, Path]:
    acquisition_path = dataset_root / "metadata/acquisition.json"
    audit_path = audit_root / "structured_content_audit.json"
    acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("acquisition_sha256") != _sha256(acquisition_path):
        raise ValueError("structured audit is not bound to this acquisition")
    content = audit.get("content_audit", {})
    if content.get("profile") != "coal_boreholes_602_v001":
        raise ValueError("structured audit has the wrong content profile")
    if content.get("source_data_role") != "source_structured_data":
        raise ValueError("structured audit does not declare source_structured_data")
    if content.get("formal_use_status") != "candidate_pending_human_and_spatial_review":
        raise ValueError("unexpected coal-602 formal-use status")
    workbooks = [row for row in acquisition["files"] if row["filename"].endswith(".xlsx")]
    if len(workbooks) != 1:
        raise ValueError("coal-602 acquisition must bind exactly one workbook")
    workbook_path = dataset_root / "raw" / workbooks[0]["filename"]
    if _sha256(workbook_path) != workbooks[0]["sha256"]:
        raise ValueError("coal-602 workbook does not match acquisition evidence")
    return workbook_path, audit_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path,
        default=ROOT / "configs/experiments/P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001.yaml",
    )
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--audit-root", type=Path, default=DEFAULT_AUDIT_ROOT)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--experiment-id")
    arguments = parser.parse_args()

    started = time.perf_counter()
    config = _load_config(arguments.config)
    experiment_id = arguments.experiment_id or config["experiment_id"]
    workbook_path, audit_path = _verify_bound_inputs(arguments.dataset_root, arguments.audit_root)
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": experiment_id,
        "git_commit": git_commit,
        "date": "2026-08-13",
        "dataset_version": config["dataset_version"],
        "split_version": config["split_version"],
        "model": config["model"],
        "model_revision": config["model_revision"],
        "prompt_version": config["prompt_version"],
        "seed": int(config["base_seed"]),
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "protocol_config_path": str(arguments.config.resolve()),
            "protocol_config_sha256": _sha256(arguments.config),
            "source_audit_path": str(audit_path.resolve()),
            "source_audit_sha256": _sha256(audit_path),
            "source_acquisition_sha256": _sha256(arguments.dataset_root / "metadata/acquisition.json"),
            "source_workbook_sha256": _sha256(workbook_path),
            "source_role": config["source_role"],
            "source_field": config["source_field"],
            "coordinate_handling": config["coordinate_handling"],
            "query_domain": config["query_domain"],
            "grid_size": int(config["grid_size"]),
            "magnitudes_m": [float(value) for value in config["magnitudes_m"]],
            "repetitions": int(config["repetitions"]),
            "idw_power": 2.0,
            "claims_allowed": config["claims_allowed"],
            "claims_forbidden": config["claims_forbidden"],
            "scope": "licensed source-field protocol development; not image-derived automated extraction, reference, QC, or geological-model evidence",
        },
    })

    surface = load_coal_602_roof_depth_surface(workbook_path)
    hull = convex_hull_xy(surface.points)
    queries = regular_queries_within_hull(hull, int(config["grid_size"]))
    reference = [idw_predict(surface.points, x, y, power=2.0) for x, y in queries]
    conditions, prediction_rows = [], []
    for magnitude_index, magnitude_value in enumerate(config["magnitudes_m"]):
        magnitude = float(magnitude_value)
        repetitions = []
        for repetition in range(int(config["repetitions"])):
            seed = int(config["base_seed"]) + magnitude_index * 10000 + repetition
            perturbed = perturb_surface_scalar(surface.points, magnitude, seed)
            predicted = [idw_predict(perturbed, x, y, power=2.0) for x, y in queries]
            measured = surface_error_metrics(reference, predicted)
            repetitions.append(measured)
            prediction_rows.append({
                "condition": "independent_signed_source_field_perturbation",
                "magnitude_m": magnitude,
                "seed": seed,
                **measured,
            })
        conditions.append({"magnitude_m": magnitude, **aggregate_repeated_metrics(repetitions)})

    elapsed = time.perf_counter() - started
    metrics = {
        "scope": "licensed structured-source proxy protocol; not extraction accuracy or geological-model evidence",
        "data_status": "licensed_source_structured_data_pending_human_spatial_review",
        "comparison": "source_field_vs_synthetically_perturbed_source_field",
        "source_record_count": surface.source_record_count,
        "source_identifier_values_persisted": False,
        "coordinate_origin_persisted": surface.coordinate_origin_persisted,
        "local_coordinate_extent_m": {
            "u": surface.coordinate_extent_u_m,
            "v": surface.coordinate_extent_v_m,
        },
        "source_scalar_range_m": {
            "minimum": surface.scalar_minimum_m,
            "maximum": surface.scalar_maximum_m,
        },
        "convex_hull_vertex_count": len(hull),
        "query_grid_size": int(config["grid_size"]),
        "query_points_within_convex_hull": len(queries),
        "repetitions_per_condition": int(config["repetitions"]),
        "conditions": conditions,
        "latency_seconds_total": elapsed,
        "accuracy_metrics": None,
        "constraint_qc_effect": None,
        "human_ground_truth_comparison": None,
        "real_geological_model_metrics": None,
    }
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in prediction_rows), encoding="utf-8",
    )
    (run / "run.log").write_text(
        "\n".join([
            "status=completed",
            "scope=licensed_source_field_protocol_only",
            f"source_records={surface.source_record_count}",
            f"query_points={len(queries)}",
            f"repetitions={config['repetitions']}",
            "coordinate_origin_persisted=false",
            "source_identifiers_persisted=false",
            "gpu_used=false",
            f"latency_seconds_total={elapsed:.9f}",
            "",
        ]),
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
