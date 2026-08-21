#!/usr/bin/env python3
"""Run a raster-only interval benchmark on the USGS-142 source log.

Reference intervals are taken from the explicit generalized-lithology legend in
the official PDF. Prediction uses only a rendered page-2 ROI and Tesseract OCR;
native PDF text and reference values are never used during parsing.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import platform
import re
from geologparser.runtime_resources import peak_process_rss_kib
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest

ROOT = Path(__file__).resolve().parents[1]
FT_TO_M = 0.3048
INTERVAL_RE = re.compile(
    r"(?P<top>\d+(?:\.\d+)?)\s+to\s+(?P<bottom>\d+(?:\.\d+)?)\s*(?:ft)?\s*[-–—]\s*(?P<lith>Basalt|Sediment)",
    re.IGNORECASE,
)
BOTTOM_RE = re.compile(
    r"(?P<top>\d+(?:\.\d+)?)\s+to\s+bottom\s*[-–—]\s*(?P<lith>Basalt|Sediment)",
    re.IGNORECASE,
)


def render_page(pdf: Path, output_root: Path, dpi: int) -> Path:
    executable = shutil.which("pdftoppm")
    if executable is None:
        raise RuntimeError("pdftoppm is required")
    completed = subprocess.run(
        [executable, "-png", "-r", str(dpi), "-f", "2", "-l", "2", str(pdf), str(output_root / "page")],
        text=True, capture_output=True, check=False,
    )
    pages = sorted(output_root.glob("page-*.png"))
    if completed.returncode != 0 or len(pages) != 1:
        raise RuntimeError(f"pdftoppm failed or page count was not one: {completed.stderr.strip()}")
    return pages[0]


def ocr_roi(image: Path, roi_path: Path, psm: int) -> str:
    from PIL import Image

    page = Image.open(image)
    width, height = page.size
    box = (int(width * 0.65), int(height * 0.25), int(width * 0.995), int(height * 0.92))
    roi = page.crop(box)
    roi.save(roi_path)
    completed = subprocess.run(
        ["tesseract", str(roi_path), "stdout", "-l", "eng", "--psm", str(psm)],
        text=True, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"tesseract failed: {completed.stderr.strip()}")
    return completed.stdout


def parse_intervals(text: str, final_depth_ft: float) -> list[dict]:
    parsed = []
    for match in INTERVAL_RE.finditer(text):
        top, bottom = float(match.group("top")), float(match.group("bottom"))
        if bottom <= top:
            continue
        parsed.append((top, bottom, match.group("lith").lower()))
    for match in BOTTOM_RE.finditer(text):
        top = float(match.group("top"))
        if final_depth_ft <= top:
            continue
        parsed.append((top, final_depth_ft, match.group("lith").lower()))
    unique = []
    seen = set()
    for top, bottom, lith in sorted(parsed):
        key = (top, bottom, lith)
        if key not in seen:
            unique.append({
                "top_depth_m": top * FT_TO_M,
                "bottom_depth_m": bottom * FT_TO_M,
                "thickness_m": (bottom - top) * FT_TO_M,
                "lithology_raw": lith.title(),
                "lithology_normalized": lith,
                "source_unit": "ft_bls",
            })
            seen.add(key)
    return unique


def load_reference(manifest: Path) -> tuple[dict, list[dict]]:
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1:
        raise ValueError("USGS-142 benchmark requires exactly one manifest row")
    row = rows[0]
    intervals = []
    for item in row["intervals"]:
        top, bottom = float(item["top_depth_ft"]), float(item["bottom_depth_ft"])
        intervals.append({
            "top_depth_m": top * FT_TO_M,
            "bottom_depth_m": bottom * FT_TO_M,
            "thickness_m": (bottom - top) * FT_TO_M,
            "lithology_raw": item["lithology_raw"],
            "lithology_normalized": item["lithology_normalized"],
        })
    return row, intervals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "datasets/manifests/usgs142_interval_gold_v001.jsonl")
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--dpi", type=int, default=400)
    parser.add_argument("--psm", type=int, default=11)
    args = parser.parse_args()
    row, references = load_reference(args.manifest)
    pdf = Path(row["pdf_path"])
    if file_sha256(pdf) != row["pdf_sha256"]:
        raise ValueError("source PDF hash mismatch")
    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    tesseract_version = subprocess.run(["tesseract", "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0]
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": "openei_usgs142_interval_gold_v001",
        "split_version": "cross_source_single_document_holdout_v001",
        "model": "tesseract_roi_generalized_lithology_parser",
        "model_revision": tesseract_version,
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version(), "tesseract": tesseract_version},
        "config": {
            "ground_truth_sha256": file_sha256(args.manifest),
            "prediction_reference_conditioning": "none",
            "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
            "render_dpi": args.dpi,
            "page": 2,
            "roi_normalized": [0.65, 0.25, 0.995, 0.92],
            "psm": args.psm,
            "unit_conversion": "feet_bls_to_meters_multiply_0.3048",
            "evaluated_fields": ["interval.top_depth_m", "interval.bottom_depth_m", "interval.thickness_m", "interval.lithology_normalized"],
            "reference_scope": "explicit generalized lithology legend in official PDF",
            "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        },
        "started_utc": started.isoformat(),
    })
    wall_started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="geologparser-usgs142-") as temporary:
        rendered = render_page(pdf, Path(temporary), args.dpi)
        roi_path = run / "roi_page2.png"
        text = ocr_roi(rendered, roi_path, args.psm)
    text_path = run / "ocr_roi.txt"
    text_path.write_text(text, encoding="utf-8")
    predictions = parse_intervals(text, float(row["final_depth_ft"]))
    matches, missing, extra = match_intervals_by_boundaries(references, predictions, tolerance_m=0.05)
    metrics_by_name = boundary_matched_interval_metrics([references], [predictions], tolerance_m=0.05)
    metrics = {
        "scope": "authoritative-interval benchmark evaluation",
        "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "prediction_reference_conditioning": "none",
        "human_reviewed": False,
        "document_count": 1,
        "page_count": 2,
        "reference_interval_count": len(references),
        "predicted_interval_count": len(predictions),
        "documents_with_predictions": 1 if predictions else 0,
        "document_full_exact": {"value": 1.0 if len(matches) == len(references) == len(predictions) else 0.0, "numerator": int(len(matches) == len(references) == len(predictions)), "denominator": 1},
        "interval_metrics": {name: result.to_dict() for name, result in metrics_by_name.items()},
        "evaluated_fields": ["interval.top_depth_m", "interval.bottom_depth_m", "interval.thickness_m", "interval.lithology_normalized"],
        "excluded_reference_fields": ["coordinates", "description", "source_bbox"],
        "source_domain": "USGS Idaho / Eastern Snake River Plain",
        "selection_limitation": "single official PDF with explicit generalized-lithology legend; not a representative sample",
        "wall_time_seconds": time.perf_counter() - wall_started,
        "latency_seconds_per_document_wall": time.perf_counter() - wall_started,
        "peak_process_rss_kib": peak_process_rss_kib(),
    }
    prediction_row = {
        "record_id": row["record_id"], "pdf_path": row["pdf_path"], "pdf_sha256": row["pdf_sha256"],
        "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT", "human_reviewed": False,
        "reference_intervals": references, "predicted_intervals": predictions,
        "matched_interval_count": len(matches), "unmatched_reference_indices": missing,
        "unmatched_prediction_indices": extra, "document_full_exact": metrics["document_full_exact"],
        "ocr_text_path": str(text_path.relative_to(run)), "ocr_text_sha256": file_sha256(text_path),
    }
    (run / "predictions.jsonl").write_text(json.dumps(prediction_row, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    errors = [{"error_type": "missing_interval", "index": idx} for idx in missing] + [{"error_type": "spurious_interval", "index": idx} for idx in extra]
    (run / "errors.jsonl").write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in errors), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(f"started_utc={started.isoformat()}\ndocuments=1\nreference_intervals={len(references)}\npredicted_intervals={len(predictions)}\nstatus=completed\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
