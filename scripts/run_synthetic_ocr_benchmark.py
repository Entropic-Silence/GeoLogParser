#!/usr/bin/env python3
"""Run Tesseract+regex on frozen synthetic logs as controlled evidence."""

from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import subprocess
import time

from geologparser.evaluation import evaluate_synthetic_controlled
from geologparser.experiment import create_run_directory
from geologparser.pipeline import run_minimal_baseline


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    manifest_path = Path("/data/GeoLogParser/datasets/synthetic_borehole_logs_v001/manifest.jsonl")
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line]
    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip() or "UNCOMMITTED"
    version = subprocess.run(["tesseract", "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0]
    metadata = {
        "experiment_id": "P1_B1_SYNTHETIC_CONTROLLED_002", "git_commit": git_commit,
        "date": date.today().isoformat(), "dataset_version": "synthetic_borehole_logs_v001",
        "split_version": "all_synthetic_controlled_no_training", "model": "tesseract_eng_regex",
        "model_revision": version, "prompt_version": "not_applicable", "seed": 20260813,
        "hardware": {"device": "cpu", "gpu_used": False},
        "software": {"pipeline": "geologparser_0.0.1", "tesseract": version},
        "config": {"manifest_sha256": "9a28a97bc69a9950b755acf203d99003f32eb439caa24952160f40f041b50acd", "ocr_language": "eng", "psm": 6},
    }
    run = create_run_directory(ROOT / "results", metadata)
    predictions, references, persisted = [], [], []
    start = time.perf_counter()
    for row in rows:
        reference = json.loads(Path(row["label_path"]).read_text(encoding="utf-8"))
        _, prediction = run_minimal_baseline(Path(row["image_path"]), ocr_language="eng")
        prediction["document"]["document_id"] = reference["document"]["document_id"]
        references.append(reference)
        predictions.append(prediction)
        persisted.append({"item_id": row["record_id"], "record": prediction})
    elapsed = time.perf_counter() - start
    metrics = evaluate_synthetic_controlled(references, predictions)
    metrics.update({"elapsed_seconds": elapsed, "latency_seconds_per_page": elapsed / len(rows)})
    (run / "predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in persisted), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    errors = []
    for reference, prediction in zip(references, predictions):
        expected = reference["borehole"]["borehole_id"]["value"]
        observed = prediction["borehole"]["borehole_id"]["value"]
        if expected != observed:
            errors.append({"item_id": reference["document"]["document_id"], "field": "borehole.borehole_id", "reference": expected, "prediction": observed, "error_type": "OCR_character_error"})
    (run / "errors.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in errors), encoding="utf-8")
    (run / "run.log").write_text(f"status=completed\nscope=synthetic_controlled_not_real_gold\npages={len(rows)}\nelapsed_seconds={elapsed}\n", encoding="utf-8")
    print(run)


if __name__ == "__main__":
    main()
