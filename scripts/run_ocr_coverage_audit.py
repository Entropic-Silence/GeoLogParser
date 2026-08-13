#!/usr/bin/env python3
"""Run privacy-minimized B1 OCR+Regex coverage on a rendered review pack."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path

from geologparser.constraints import load_engine_config
from geologparser.ocr import RapidOCROnnxAdapter, TesseractOCRAdapter
from geologparser.ocr_coverage_audit import run_ocr_coverage_audit
from geologparser.result_index import file_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = Path("/data/GeoLogParser/artifacts/source_review/international_candidates_v001")
DEFAULT_CONSTRAINTS = ROOT / "configs/constraints/default_v001.yaml"
RAPIDOCR_MODEL_DIR = Path("/data/GeoLogParser/models/rapidocr")
RAPIDOCR_MODEL_HASHES = {
    "ch_PP-OCRv4_det_infer.onnx": "d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9",
    "ch_PP-OCRv4_rec_infer.onnx": "48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b",
    "ch_ppocr_mobile_v2.0_cls_infer.onnx": "e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c",
}


def verify_rapidocr_models() -> None:
    for filename, expected in RAPIDOCR_MODEL_HASHES.items():
        path = RAPIDOCR_MODEL_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"RapidOCR model is missing: {path}")
        actual = file_sha256(path)
        if actual != expected:
            raise ValueError(f"RapidOCR model hash mismatch: {filename}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--review-pack-root", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--ocr-backend", choices=("tesseract", "rapidocr"), required=True)
    parser.add_argument("--dataset-id")
    parser.add_argument("--content-class")
    parser.add_argument("--tesseract-language", default="eng")
    parser.add_argument("--tesseract-psm", type=int, default=6)
    parser.add_argument("--rapidocr-threads", type=int, default=4)
    parser.add_argument("--constraint-config", type=Path, default=DEFAULT_CONSTRAINTS)
    arguments = parser.parse_args()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    if arguments.ocr_backend == "tesseract":
        revision = subprocess.run(
            ["tesseract", "--version"], text=True, capture_output=True, check=True,
        ).stdout.splitlines()[0]
        adapter = TesseractOCRAdapter(
            language=arguments.tesseract_language, psm=arguments.tesseract_psm,
        )
        model = "B1_tesseract_ocr_regex_privacy_minimized"
        software = {"python": platform.python_version(), "tesseract": revision}
        backend_config = {
            "language": arguments.tesseract_language, "psm": arguments.tesseract_psm,
        }
    else:
        verify_rapidocr_models()
        revision = (
            f"rapidocr_onnxruntime {version('rapidocr_onnxruntime')} / "
            f"onnxruntime {version('onnxruntime')}"
        )
        adapter = RapidOCROnnxAdapter(
            model_dir=RAPIDOCR_MODEL_DIR,
            intra_op_num_threads=arguments.rapidocr_threads,
        )
        model = "B1_rapidocr_ppocrv4_regex_privacy_minimized"
        software = {
            "python": platform.python_version(),
            "rapidocr_onnxruntime": version("rapidocr_onnxruntime"),
            "onnxruntime": version("onnxruntime"),
        }
        backend_config = {
            "threads": arguments.rapidocr_threads,
            "execution_provider": "CPUExecutionProvider",
            "model_dir": str(RAPIDOCR_MODEL_DIR),
            "model_sha256": RAPIDOCR_MODEL_HASHES,
        }
    metadata = {
        "experiment_id": arguments.experiment_id,
        "git_commit": commit,
        "date": "2026-08-13",
        "dataset_version": "international_source_review_pack_v001",
        "split_version": "audit_selection_no_training_no_ground_truth",
        "model": model,
        "model_revision": revision,
        "prompt_version": "not_applicable",
        "seed": None,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": software,
        "config": backend_config | {
            "review_pack_root": str(arguments.review_pack_root.resolve()),
            "review_pack_manifest_sha256": file_sha256(
                arguments.review_pack_root / "review_pack_manifest.jsonl"
            ),
            "dataset_id_filter": arguments.dataset_id,
            "content_class_filter": arguments.content_class,
            "source_content_review_status": "unreviewed",
            "record_output_policy": "hash_and_presence_only",
            "constraint_config_path": str(arguments.constraint_config.resolve()),
            "constraint_config_sha256": file_sha256(arguments.constraint_config),
        },
    }
    run, metrics = run_ocr_coverage_audit(
        review_pack_root=arguments.review_pack_root,
        results_root=arguments.results_root,
        run_metadata=metadata,
        adapter=adapter,
        constraint_engine=load_engine_config(arguments.constraint_config),
        dataset_id=arguments.dataset_id,
        content_class=arguments.content_class,
    )
    print(json.dumps({"result_path": str(run), "metrics": metrics}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
