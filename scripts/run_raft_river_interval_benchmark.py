#!/usr/bin/env python3
"""Raster-only interval benchmark for two Raft River IDWR driller reports."""
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

from PIL import Image

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.ocr import RapidOCROnnxAdapter
from geologparser.ocr.rapidocr import DEFAULT_MODEL_DIR, MODEL_FILENAMES
from geologparser.result_index import file_sha256, write_artifact_manifest

ROOT = Path(__file__).resolve().parents[1]
FT_TO_M = 0.3048
NUMERIC_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*$")


def normalize_lithology(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def reference_intervals(row: dict) -> list[dict]:
    return [
        {
            "top_depth_m": float(item["top_depth_ft"]) * FT_TO_M,
            "bottom_depth_m": float(item["bottom_depth_ft"]) * FT_TO_M,
            "thickness_m": (float(item["bottom_depth_ft"]) - float(item["top_depth_ft"])) * FT_TO_M,
            "lithology_raw": item["lithology_raw"],
            "lithology_normalized": item["lithology_normalized"],
        }
        for item in row["intervals"]
    ]


def render_and_crop(pdf: Path, pages: list[int], root: Path, dpi: int) -> list[tuple[int, Path]]:
    if shutil.which("pdftoppm") is None:
        raise RuntimeError("pdftoppm is required")
    output: list[tuple[int, Path]] = []
    for page_number in pages:
        prefix = root / f"page-{page_number}"
        completed = subprocess.run(
            ["pdftoppm", "-png", "-r", str(dpi), "-f", str(page_number), "-l", str(page_number), "-singlefile", str(pdf), str(prefix)],
            capture_output=True, text=True, check=False,
        )
        rendered = prefix.with_suffix(".png")
        if completed.returncode or not rendered.is_file():
            raise RuntimeError(f"pdftoppm failed: {completed.stderr.strip()}")
        with Image.open(rendered) as image:
            width, height = image.size
            roi = image.crop((int(width * 0.50), int(height * 0.20), int(width * 0.99), int(height * 0.83)))
            roi_path = root / f"page-{page_number}-table.png"
            roi.save(roi_path)
        output.append((page_number, roi_path))
    return output


def as_interval(top: float, bottom: float, lithology: str, page: int, evidence: dict) -> dict | None:
    if not (0 <= top < bottom <= 5000):
        return None
    lithology = re.sub(r"\s+", " ", lithology).strip(" |[]_.,;:-")
    lithology = re.sub(r"(?:\s+[XY])+$", "", lithology).strip()
    if not lithology or not re.search(r"[A-Za-z]", lithology):
        return None
    return {
        "top_depth_m": top * FT_TO_M,
        "bottom_depth_m": bottom * FT_TO_M,
        "thickness_m": (bottom - top) * FT_TO_M,
        "lithology_raw": lithology,
        "lithology_normalized": normalize_lithology(lithology),
        "source_page": page,
        "source_unit": "ft_bls",
        "evidence": evidence,
    }


def parse_tesseract(text: str, page: int) -> list[dict]:
    rows: list[dict] = []
    for raw_line in text.splitlines():
        cleaned = re.sub(r"[|\[\]{}_/\\]+", " ", raw_line)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        tokens = cleaned.split()
        number_positions = [index for index, token in enumerate(tokens) if NUMERIC_RE.fullmatch(token)]
        if len(number_positions) < 2:
            continue
        start = 1 if len(number_positions) >= 3 and float(tokens[number_positions[0]]) in {6.0, 8.0, 10.0} else 0
        if len(number_positions) < start + 2:
            continue
        top_index, bottom_index = number_positions[start:start + 2]
        if bottom_index + 1 >= len(tokens):
            continue
        interval = as_interval(
            float(tokens[top_index]), float(tokens[bottom_index]),
            " ".join(tokens[bottom_index + 1:]), page,
            {"backend": "tesseract", "source_text": raw_line},
        )
        if interval is not None:
            rows.append(interval)
    return rows


def parse_rapidocr(regions: list, page: int) -> list[dict]:
    numeric = []
    lithology = []
    for region in regions:
        if region.bbox is None:
            continue
        x1, y1, x2, y2 = region.bbox
        center_y = (y1 + y2) / 2
        number_match = NUMERIC_RE.fullmatch(region.text)
        if number_match and 130 <= x1 < 365:
            numeric.append((x1, center_y, float(number_match.group(1)), region))
        elif 340 <= x1 < 1000 and re.search(r"[A-Za-z]", region.text):
            lithology.append((center_y, region))
    rows: list[dict] = []
    top_candidates = [item for item in numeric if item[0] < 260]
    bottom_candidates = [item for item in numeric if item[0] >= 250]
    for _x, center_y, top, top_region in top_candidates:
        bottom_hits = [item for item in bottom_candidates if abs(item[1] - center_y) <= 18]
        lith_hits = [item for item in lithology if abs(item[0] - center_y) <= 20]
        if not bottom_hits or not lith_hits:
            continue
        bottom_item = min(bottom_hits, key=lambda item: abs(item[1] - center_y))
        lith_item = min(lith_hits, key=lambda item: abs(item[0] - center_y))
        interval = as_interval(
            top, bottom_item[2], lith_item[1].text, page,
            {
                "backend": "rapidocr_onnxruntime",
                "top_bbox": list(top_region.bbox),
                "bottom_bbox": list(bottom_item[3].bbox),
                "lithology_bbox": list(lith_item[1].bbox),
                "confidence": min(top_region.confidence or 0.0, bottom_item[3].confidence or 0.0, lith_item[1].confidence or 0.0),
            },
        )
        if interval is not None:
            rows.append(interval)
    return rows


def deduplicate(rows: list[dict]) -> list[dict]:
    output, seen = [], set()
    for row in sorted(rows, key=lambda item: (item["source_page"], item["top_depth_m"], item["bottom_depth_m"])):
        key = (round(row["top_depth_m"], 6), round(row["bottom_depth_m"], 6), row["lithology_normalized"])
        if key not in seen:
            output.append(row)
            seen.add(key)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--backend", choices=("tesseract", "rapidocr"), required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "datasets/manifests/usgs_raft_river_interval_gold_v001.jsonl")
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--psm", type=int, default=6)
    args = parser.parse_args()
    manifest = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(manifest) != 2 or any(row["ground_truth_tier"] != "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT" for row in manifest):
        raise ValueError("unexpected Raft River authoritative interval manifest")
    for row in manifest:
        if file_sha256(Path(row["pdf_path"])) != row["pdf_sha256"]:
            raise ValueError(f"source PDF hash mismatch: {row['record_id']}")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tesseract_revision = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    model_hashes = {name: file_sha256(DEFAULT_MODEL_DIR / filename) for name, filename in MODEL_FILENAMES.items()}
    model_revision = tesseract_revision if args.backend == "tesseract" else json.dumps(model_hashes, sort_keys=True)
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id, "git_commit": commit, "date": date.today().isoformat(),
        "dataset_version": "usgs_raft_river_interval_gold_v001",
        "split_version": "source_disjoint_two_document_explicit_interval_holdout_v001",
        "model": f"{args.backend}_raster_table_interval_parser", "model_revision": model_revision,
        "prompt_version": "not_applicable", "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version(), "tesseract": tesseract_revision},
        "config": {
            "ground_truth_sha256": file_sha256(args.manifest), "prediction_reference_conditioning": "none",
            "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT", "render_dpi": args.dpi,
            "table_roi_normalized": [0.50, 0.20, 0.99, 0.83], "tesseract_psm": args.psm,
            "unit_conversion": "feet_bls_to_meters_multiply_0.3048",
            "evaluated_fields": ["interval.top_depth_m", "interval.bottom_depth_m", "interval.thickness_m", "interval.lithology_normalized"],
            "reference_scope": "explicit From-To-Lithology rows in official IDWR driller reports released by USGS",
            "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        }, "started_utc": started.isoformat(),
    })
    wall_started = time.perf_counter()
    adapter = RapidOCROnnxAdapter(intra_op_num_threads=4) if args.backend == "rapidocr" else None
    refs_by_doc, preds_by_doc, prediction_rows, errors = [], [], [], []
    for row in manifest:
        refs = reference_intervals(row)
        with tempfile.TemporaryDirectory(prefix="geologparser-raft-river-") as temporary:
            rois = render_and_crop(Path(row["pdf_path"]), row["pages"], Path(temporary), args.dpi)
            predictions = []
            evidence_rows = []
            for page, roi in rois:
                saved_roi = run / f"{row['record_id']}_page-{page}_table.png"
                shutil.copy2(roi, saved_roi)
                if args.backend == "tesseract":
                    completed = subprocess.run(["tesseract", str(roi), "stdout", "-l", "eng", "--psm", str(args.psm)], capture_output=True, text=True, check=False)
                    if completed.returncode:
                        raise RuntimeError(completed.stderr.strip())
                    text_path = run / f"{row['record_id']}_page-{page}_ocr.txt"
                    text_path.write_text(completed.stdout, encoding="utf-8")
                    evidence_rows.append({"page": page, "ocr_text_path": text_path.name, "ocr_text_sha256": file_sha256(text_path)})
                    predictions.extend(parse_tesseract(completed.stdout, page))
                else:
                    regions = adapter.extract(roi)
                    region_path = run / f"{row['record_id']}_page-{page}_regions.jsonl"
                    region_path.write_text("".join(json.dumps({"bbox": list(item.bbox) if item.bbox else None, "text": item.text, "confidence": item.confidence}, sort_keys=True) + "\n" for item in regions), encoding="utf-8")
                    evidence_rows.append({"page": page, "ocr_regions_path": region_path.name, "ocr_regions_sha256": file_sha256(region_path)})
                    predictions.extend(parse_rapidocr(regions, page))
        predictions = deduplicate(predictions)
        matches, missing, extra = match_intervals_by_boundaries(refs, predictions, tolerance_m=0.05)
        lith_correct = sum(refs[item.reference_index]["lithology_normalized"] == predictions[item.prediction_index]["lithology_normalized"] for item in matches)
        full_exact = len(matches) == len(refs) == len(predictions) and lith_correct == len(matches)
        refs_by_doc.append(refs)
        preds_by_doc.append(predictions)
        prediction_rows.append({
            "record_id": row["record_id"], "pdf_path": row["pdf_path"], "pdf_sha256": row["pdf_sha256"],
            "ground_truth_tier": row["ground_truth_tier"], "human_reviewed": False,
            "reference_intervals": refs, "predicted_intervals": predictions,
            "matched_interval_count": len(matches), "matched_lithology_exact_count": lith_correct,
            "unmatched_reference_indices": missing, "unmatched_prediction_indices": extra,
            "document_full_exact": full_exact, "evidence": evidence_rows,
        })
        errors.extend({"record_id": row["record_id"], "error_type": "missing_interval", "reference_index": index} for index in missing)
        errors.extend({"record_id": row["record_id"], "error_type": "spurious_interval", "prediction_index": index} for index in extra)
        errors.extend({"record_id": row["record_id"], "error_type": "lithology_semantic_error", "reference_index": item.reference_index, "prediction_index": item.prediction_index} for item in matches if refs[item.reference_index]["lithology_normalized"] != predictions[item.prediction_index]["lithology_normalized"])
    interval_metrics = boundary_matched_interval_metrics(refs_by_doc, preds_by_doc, tolerance_m=0.05)
    total_matches = sum(row["matched_interval_count"] for row in prediction_rows)
    total_lith_correct = sum(row["matched_lithology_exact_count"] for row in prediction_rows)
    metrics = {
        "scope": "authoritative-interval benchmark evaluation", "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "prediction_reference_conditioning": "none", "human_reviewed": False, "document_count": len(manifest),
        "page_count": sum(len(row["pages"]) for row in manifest), "reference_interval_count": sum(len(rows) for rows in refs_by_doc),
        "predicted_interval_count": sum(len(rows) for rows in preds_by_doc), "documents_with_predictions": sum(bool(rows) for rows in preds_by_doc),
        "document_full_exact": {"value": sum(row["document_full_exact"] for row in prediction_rows) / len(prediction_rows), "numerator": sum(row["document_full_exact"] for row in prediction_rows), "denominator": len(prediction_rows)},
        "interval_metrics": {name: result.to_dict() for name, result in interval_metrics.items()},
        "matched_lithology_exact": {"value": total_lith_correct / total_matches if total_matches else None, "numerator": total_lith_correct, "denominator": total_matches},
        "source_domain": "USGS Raft River release / Idaho Department of Water Resources driller reports",
        "selection_limitation": "two of twelve released reports contain explicit interval tables; ten attached lithology sequences are point-depth observations and are excluded from interval scoring",
        "wall_time_seconds": time.perf_counter() - wall_started, "latency_seconds_per_document_wall": (time.perf_counter() - wall_started) / len(manifest),
        "peak_process_rss_kib": peak_process_rss_kib(),
    }
    (run / "predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in prediction_rows), encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in errors), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(f"started_utc={started.isoformat()}\nbackend={args.backend}\ndocuments={len(manifest)}\nreference_intervals={metrics['reference_interval_count']}\npredicted_intervals={metrics['predicted_interval_count']}\nstatus=completed\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
