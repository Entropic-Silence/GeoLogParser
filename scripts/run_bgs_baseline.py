"""Run B1 OCR+Regex on the fixed BGS public audit sample."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from pathlib import Path

from geologparser.constraints import default_engine
from geologparser.evaluation import exact_match, numeric_with_missing_mae
from geologparser.experiment import create_run_directory
from geologparser.pipeline import run_minimal_baseline


ROOT = Path(__file__).resolve().parents[1]


def scalar(record: dict, name: str):
    return record["borehole"][name]["value"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--dataset-root", type=Path, default=Path("/data/GeoLogParser/datasets/public/bgs_v001"))
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    arguments = parser.parse_args()
    manifest_path = arguments.dataset_root / "metadata" / "manifest.jsonl"
    manifest = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line]
    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    tesseract_version = subprocess.run(["tesseract", "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0]
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": git_commit,
        "date": "2026-08-12",
        "dataset_version": "bgs_opengeoscience_v001_fixed_ids_4_5_6_10",
        "split_version": "audit_all_no_training",
        "model": "B1_tesseract_ocr_regex",
        "model_revision": tesseract_version,
        "prompt_version": "not_applicable",
        "seed": None,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version(), "tesseract": tesseract_version},
        "config": {"ocr_language": "eng", "psm": 6, "render_dpi": 300, "constraint_tolerance_m": "0.05"},
    })
    references = {name: [] for name in ("borehole_id", "x_coordinate", "y_coordinate", "final_depth_m")}
    predictions = {name: [] for name in references}
    rows = []
    total_start = time.perf_counter()
    with (run / "predictions.jsonl").open("w", encoding="utf-8") as prediction_stream:
        for item in manifest:
            metadata = item["metadata"]
            source = Path(item["local_path"])
            start = time.perf_counter()
            regions, record = run_minimal_baseline(source, ocr_language="eng")
            elapsed = time.perf_counter() - start
            expected = {
                "borehole_id": metadata.get("REFERENCE"),
                "x_coordinate": metadata.get("EASTING"),
                "y_coordinate": metadata.get("NORTHING"),
                "final_depth_m": metadata.get("LENGTH") if (metadata.get("LENGTH") or -1) > 0 else None,
            }
            predicted = {name: scalar(record, name) for name in references}
            for name in references:
                references[name].append(expected[name])
                predictions[name].append(predicted[name])
            constraint_results = default_engine("0.05").evaluate(record)
            row = {
                "source_record_id": item["source_record_id"],
                "source_sha256": item["sha256"],
                "expected": expected,
                "predicted": predicted,
                "interval_count": len(record["intervals"]),
                "text_region_count": len(regions),
                "latency_seconds": elapsed,
                "record": record,
                "constraints": [result.__dict__ | {"violations": [violation.__dict__ for violation in result.violations]} for result in constraint_results],
            }
            rows.append(row)
            prediction_stream.write(json.dumps(row, ensure_ascii=False, default=list) + "\n")
    total_elapsed = time.perf_counter() - total_start
    metrics = {
        "sample_documents": len(rows),
        "sample_pages": 20,
        "benchmark_scope": "small public audit sample; not representative BGS performance",
        "borehole_id_exact_match": exact_match(references["borehole_id"], predictions["borehole_id"], "borehole_id_exact_match").to_dict(),
        "x_coordinate": {key: value.to_dict() for key, value in numeric_with_missing_mae(references["x_coordinate"], predictions["x_coordinate"], "x_coordinate_mae").items()},
        "y_coordinate": {key: value.to_dict() for key, value in numeric_with_missing_mae(references["y_coordinate"], predictions["y_coordinate"], "y_coordinate_mae").items()},
        "final_depth": {key: value.to_dict() for key, value in numeric_with_missing_mae(references["final_depth_m"], predictions["final_depth_m"], "final_depth_mae_m").items()},
        "documents_with_any_interval": sum(row["interval_count"] > 0 for row in rows),
        "total_intervals_emitted": sum(row["interval_count"] for row in rows),
        "latency_total_seconds": total_elapsed,
        "latency_seconds_per_document": total_elapsed / len(rows) if rows else None,
        "latency_seconds_per_page": total_elapsed / 20,
    }
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    errors = []
    for row in rows:
        for name, expected in row["expected"].items():
            observed = row["predicted"][name]
            if expected is not None and observed != expected:
                errors.append({
                    "source_record_id": row["source_record_id"], "field": name,
                    "expected": expected, "observed": observed,
                    "error_type": "missing_field" if observed is None else "OCR_or_extraction_error",
                })
        if row["interval_count"] == 0:
            errors.append({"source_record_id": row["source_record_id"], "field": "intervals", "error_type": "missing_interval", "expected": "TBD_manual_annotation", "observed": 0})
    (run / "errors.jsonl").write_text("".join(json.dumps(error, ensure_ascii=False) + "\n" for error in errors), encoding="utf-8")
    (run / "run.log").write_text(
        f"documents={len(rows)}\npages=20\ntotal_seconds={total_elapsed:.6f}\nstatus=completed\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()

