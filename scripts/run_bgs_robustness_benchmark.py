#!/usr/bin/env python3
"""Evaluate OCR+regex under controlled degradations of real BGS first pages."""

from __future__ import annotations

import argparse
import json
import platform
from geologparser.runtime_resources import peak_process_rss_kib
import subprocess
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from importlib.metadata import version
from pathlib import Path

from geologparser.evaluation import exact_match, numeric_with_missing_mae
from geologparser.experiment import create_run_directory
from geologparser.extraction import extract_structured
from geologparser.ocr import RapidOCROnnxAdapter, TesseractOCRAdapter
from geologparser.result_index import file_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = Path("/data/GeoLogParser/datasets/public/bgs_metadata_robustness_v001")
RAPIDOCR_MODEL_DIR = Path("/data/GeoLogParser/models/rapidocr")
RAPIDOCR_MODEL_HASHES = {
    "ch_PP-OCRv4_det_infer.onnx": "d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9",
    "ch_PP-OCRv4_rec_infer.onnx": "48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b",
    "ch_ppocr_mobile_v2.0_cls_infer.onnx": "e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c",
}


def scalar(record: dict, name: str):
    return record["borehole"][name]["value"]


def summarize_profile(rows: list[dict]) -> dict:
    fields = ("borehole_id", "x_coordinate", "y_coordinate")
    references = {name: [row["reference"][name] for row in rows] for name in fields}
    predictions = {name: [row["prediction"][name] for row in rows] for name in fields}
    id_metric = exact_match(
        references["borehole_id"], predictions["borehole_id"], "borehole_id_exact_match",
    ).to_dict()
    x_metrics = {
        key: value.to_dict() for key, value in numeric_with_missing_mae(
            references["x_coordinate"], predictions["x_coordinate"], "x_coordinate_mae",
        ).items()
    }
    y_metrics = {
        key: value.to_dict() for key, value in numeric_with_missing_mae(
            references["y_coordinate"], predictions["y_coordinate"], "y_coordinate_mae",
        ).items()
    }
    complete = sum(
        all(row["prediction"][name] == row["reference"][name] for name in fields)
        for row in rows
    )
    numeric_wrong = sum(
        row["prediction"][name] is not None
        and row["prediction"][name] != row["reference"][name]
        for row in rows for name in ("x_coordinate", "y_coordinate")
    )
    omissions = sum(
        row["prediction"][name] is None for row in rows for name in fields
    )
    return {
        "document_count": len(rows),
        "borehole_id_exact_match": id_metric,
        "x_coordinate": x_metrics,
        "y_coordinate": y_metrics,
        "complete_three_field_exact": {
            "value": complete / len(rows) if rows else None,
            "numerator": complete,
            "denominator": len(rows),
        },
        "wrong_nonmissing_numeric_predictions": numeric_wrong,
        "field_omissions": omissions,
        "latency_total_seconds": sum(row["latency_seconds"] for row in rows),
        "latency_mean_seconds_per_image": (
            sum(row["latency_seconds"] for row in rows) / len(rows) if rows else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--ocr-backend", choices=("tesseract", "rapidocr"), required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--rapidocr-threads", type=int, default=2)
    arguments = parser.parse_args()
    if arguments.workers < 1:
        raise ValueError("workers must be positive")

    manifest_path = arguments.dataset_root / "degradation_manifest.jsonl"
    dataset_summary_path = arguments.dataset_root / "summary.json"
    manifest = [
        json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    dataset_summary = json.loads(dataset_summary_path.read_text(encoding="utf-8"))
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    if arguments.ocr_backend == "tesseract":
        backend_revision = subprocess.run(
            ["tesseract", "--version"], text=True, capture_output=True, check=True,
        ).stdout.splitlines()[0]
        model_id = "B1_tesseract_ocr_regex"
        software = {"python": platform.python_version(), "tesseract": backend_revision}
        backend_config = {"ocr_language": "eng", "psm": 6}

        def make_adapter():
            return TesseractOCRAdapter(language="eng", psm=6)
    else:
        backend_revision = (
            f"rapidocr_onnxruntime {version('rapidocr_onnxruntime')} / "
            f"onnxruntime {version('onnxruntime')}"
        )
        model_id = "B1_rapidocr_onnxruntime_ppocrv4_regex"
        software = {
            "python": platform.python_version(),
            "rapidocr_onnxruntime": version("rapidocr_onnxruntime"),
            "onnxruntime": version("onnxruntime"),
        }
        backend_config = {
            "intra_op_num_threads": arguments.rapidocr_threads,
            "inter_op_num_threads": 1,
            "model_dir": str(RAPIDOCR_MODEL_DIR),
            "model_sha256": RAPIDOCR_MODEL_HASHES,
            "execution_provider": "CPUExecutionProvider",
        }

        def make_adapter():
            return RapidOCROnnxAdapter(
                model_dir=RAPIDOCR_MODEL_DIR,
                intra_op_num_threads=arguments.rapidocr_threads,
            )

    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": dataset_summary["dataset_id"],
        "split_version": "same_31_documents_controlled_degradation_profiles_v001",
        "model": model_id,
        "model_revision": backend_revision,
        "prompt_version": "not_applicable",
        "seed": dataset_summary["base_seed"],
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": software,
        "config": backend_config | {
            "workers": arguments.workers,
            "ground_truth_sha256": file_sha256(manifest_path),
            "ground_truth_tier": "AUTHORITATIVE_METADATA",
            "source_manifest_sha256": dataset_summary["source_manifest_sha256"],
            "dataset_summary_sha256": file_sha256(dataset_summary_path),
            "render_dpi": dataset_summary["render_dpi"],
            "evaluated_fields": dataset_summary["evaluated_reference_fields"],
            "excluded_fields": dataset_summary["excluded_reference_fields"],
        },
    })

    local = threading.local()

    def evaluate(row: dict) -> dict:
        adapter = getattr(local, "adapter", None)
        if adapter is None:
            adapter = make_adapter()
            local.adapter = adapter
        image = Path(row["derived_image_path"])
        if file_sha256(image) != row["derived_image_sha256"]:
            raise ValueError(f"derived image hash mismatch: {image}")
        started = time.perf_counter()
        regions = adapter.extract(image)
        record = extract_structured(regions, image)
        elapsed = time.perf_counter() - started
        prediction = {
            name: scalar(record, name)
            for name in ("borehole_id", "x_coordinate", "y_coordinate")
        }
        return {
            "item_id": row["item_id"],
            "source_record_id": row["source_record_id"],
            "profile": row["profile"],
            "derived_image_sha256": row["derived_image_sha256"],
            "reference": row["reference"],
            "prediction": prediction,
            "ocr_region_count": len(regions),
            "latency_seconds": elapsed,
        }

    total_started = time.perf_counter()
    if arguments.workers == 1:
        rows = [evaluate(row) for row in manifest]
    else:
        with ThreadPoolExecutor(max_workers=arguments.workers) as executor:
            rows = list(executor.map(evaluate, manifest))
    wall_seconds = time.perf_counter() - total_started
    with (run / "predictions.jsonl").open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    by_profile: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_profile[row["profile"]].append(row)
    profile_metrics = {
        profile: summarize_profile(by_profile[profile])
        for profile in dataset_summary["profiles"]
    }
    clean = {
        row["source_record_id"]: row for row in by_profile["clean"]
    }
    for profile, values in by_profile.items():
        retained = eligible = 0
        for row in values:
            clean_row = clean[row["source_record_id"]]
            for field in ("borehole_id", "x_coordinate", "y_coordinate"):
                if clean_row["prediction"][field] == clean_row["reference"][field]:
                    eligible += 1
                    retained += row["prediction"][field] == row["reference"][field]
        profile_metrics[profile]["clean_correct_field_retention"] = {
            "value": retained / eligible if eligible else None,
            "numerator": retained,
            "denominator": eligible,
        }
    metrics = {
        "scope": "authoritative-metadata controlled-degradation evaluation",
        "reference_ground_truth_tier": "AUTHORITATIVE_METADATA",
        "document_count": dataset_summary["source_document_count"],
        "derived_image_count": len(rows),
        "profile_count": len(profile_metrics),
        "profiles": profile_metrics,
        "evaluated_reference_fields": ["borehole_id", "x_coordinate", "y_coordinate"],
        "interval_ground_truth_available": False,
        "final_depth_ground_truth_evaluated": False,
        "degradation_origin": "synthetic controlled transformations of real source scans",
        "wall_time_seconds": wall_seconds,
        "latency_seconds_per_image_wall": wall_seconds / len(rows) if rows else None,
        "peak_process_rss_kib": peak_process_rss_kib(),
    }
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    errors = []
    for row in rows:
        for field, expected in row["reference"].items():
            observed = row["prediction"][field]
            if observed != expected:
                errors.append({
                    "item_id": row["item_id"], "source_record_id": row["source_record_id"],
                    "profile": row["profile"], "field": field, "expected": expected,
                    "observed": observed,
                    "error_type": "omission" if observed is None else "OCR_or_extraction_error",
                })
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(error, ensure_ascii=False, sort_keys=True) + "\n" for error in errors),
        encoding="utf-8",
    )
    (run / "run.log").write_text(
        f"images={len(rows)}\nprofiles={len(profile_metrics)}\nwall_seconds={wall_seconds:.6f}\nstatus=completed\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
