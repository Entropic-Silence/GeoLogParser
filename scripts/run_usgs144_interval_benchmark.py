#!/usr/bin/env python3
"""Raster-only benchmark for the explicit lithology intervals in USGS-144.

The reference is transcribed from interval descriptions printed in the official
PDF. Prediction is made from rendered page images and Tesseract OCR only; the
native PDF text is never read by the parser.
"""
from __future__ import annotations

import argparse, json, platform, re, resource, shutil, subprocess, tempfile, time
from datetime import date, datetime, timezone
from pathlib import Path

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest

ROOT = Path(__file__).resolve().parents[1]
FT_TO_M = 0.3048
INTERVAL_RE = re.compile(
    r"(?P<top>\d+(?:\.\d+)?)\s*(?:to|[-–—])\s*(?P<bottom>\d+(?:\.\d+)?)\s*ft\.?\s*[-–—]\s*(?P<lith>Surficial sediment|Basalt|Sediment(?: layers?)?|Sand[^.\n]*)",
    re.IGNORECASE,
)

def render_pages(pdf: Path, root: Path, dpi: int) -> list[Path]:
    exe = shutil.which("pdftoppm")
    if not exe:
        raise RuntimeError("pdftoppm is required")
    cp = subprocess.run([exe, "-png", "-r", str(dpi), "-f", "1", "-l", "3", str(pdf), str(root / "page")], capture_output=True, text=True)
    pages = sorted(root.glob("page-*.png"))
    if cp.returncode or len(pages) != 3:
        raise RuntimeError(f"pdftoppm failed: {cp.stderr.strip()}")
    return pages

def ocr_pages(pages: list[Path], output_dir: Path, psm: int) -> str:
    chunks = []
    for page in pages:
        cp = subprocess.run(["tesseract", str(page), "stdout", "-l", "eng", "--psm", str(psm)], capture_output=True, text=True)
        if cp.returncode:
            raise RuntimeError(cp.stderr.strip())
        chunks.append(f"\n--- {page.name} ---\n{cp.stdout}")
    text = "".join(chunks)
    (output_dir / "ocr_pages.txt").write_text(text, encoding="utf-8")
    return text

def normalize_lithology(raw: str) -> str:
    value = raw.lower().strip()
    if value.startswith("surficial"):
        return "surficial sediment"
    if value.startswith("sediment"):
        return "sediment"
    if value.startswith("sand"):
        return "sand"
    return value

def parse_intervals(text: str) -> list[dict]:
    rows = []
    seen = set()
    for m in INTERVAL_RE.finditer(text):
        top, bottom = float(m.group("top")), float(m.group("bottom"))
        if bottom <= top:
            continue
        lith_raw = re.sub(r"\s+", " ", m.group("lith")).strip(" ,")
        key = (top, bottom, normalize_lithology(lith_raw))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"top_depth_m": top * FT_TO_M, "bottom_depth_m": bottom * FT_TO_M, "thickness_m": (bottom - top) * FT_TO_M, "lithology_raw": lith_raw, "lithology_normalized": normalize_lithology(lith_raw), "source_unit": "ft_bls"})
    return sorted(rows, key=lambda row: (row["top_depth_m"], row["bottom_depth_m"]))

def load_reference(path: Path) -> tuple[dict, list[dict]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1:
        raise ValueError("USGS-144 benchmark requires exactly one manifest row")
    row = rows[0]
    refs = []
    for item in row["intervals"]:
        top, bottom = float(item["top_depth_ft"]), float(item["bottom_depth_ft"])
        refs.append({"top_depth_m": top * FT_TO_M, "bottom_depth_m": bottom * FT_TO_M, "thickness_m": (bottom - top) * FT_TO_M, "lithology_raw": item["lithology_raw"], "lithology_normalized": item["lithology_normalized"]})
    return row, refs

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--manifest", type=Path, default=ROOT / "datasets/manifests/usgs144_interval_gold_v001.jsonl")
    ap.add_argument("--results-root", type=Path, default=ROOT / "results")
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--psm", type=int, default=11)
    args = ap.parse_args()
    row, refs = load_reference(args.manifest)
    pdf = Path(row["pdf_path"])
    if file_sha256(pdf) != row["pdf_sha256"]:
        raise ValueError("source PDF hash mismatch")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tess = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {"experiment_id": args.experiment_id, "git_commit": commit, "date": date.today().isoformat(), "dataset_version": "usgs144_interval_gold_v001", "split_version": "single_document_explicit_interval_holdout_v001", "model": "tesseract_raster_page_interval_parser", "model_revision": tess, "prompt_version": "not_applicable", "seed": 0, "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False}, "software": {"python": platform.python_version(), "tesseract": tess}, "config": {"ground_truth_sha256": file_sha256(args.manifest), "prediction_reference_conditioning": "none", "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT", "render_dpi": args.dpi, "pages": [1, 2, 3], "psm": args.psm, "unit_conversion": "feet_bls_to_meters_multiply_0.3048", "evaluated_fields": ["interval.top_depth_m", "interval.bottom_depth_m", "interval.thickness_m", "interval.lithology_normalized"], "reference_scope": "explicit interval descriptions in official PDF", "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW"}, "started_utc": started.isoformat()})
    wall = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="geologparser-usgs144-") as temp:
        pages = render_pages(pdf, Path(temp), args.dpi)
        text = ocr_pages(pages, run, args.psm)
    preds = parse_intervals(text)
    matches, missing, extra = match_intervals_by_boundaries(refs, preds, tolerance_m=0.05)
    by_name = boundary_matched_interval_metrics([refs], [preds], tolerance_m=0.05)
    metrics = {"scope": "authoritative-interval benchmark evaluation", "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT", "prediction_reference_conditioning": "none", "human_reviewed": False, "document_count": 1, "page_count": 3, "reference_interval_count": len(refs), "predicted_interval_count": len(preds), "documents_with_predictions": int(bool(preds)), "document_full_exact": {"value": float(len(matches) == len(refs) == len(preds)), "numerator": int(len(matches) == len(refs) == len(preds)), "denominator": 1}, "interval_metrics": {name: result.to_dict() for name, result in by_name.items()}, "evaluated_fields": ["interval.top_depth_m", "interval.bottom_depth_m", "interval.thickness_m", "interval.lithology_normalized"], "excluded_reference_fields": ["coordinates", "description", "source_bbox"], "source_domain": "USGS Idaho / INL USGS-144", "selection_limitation": "single official PDF; explicit descriptions include a 635-639 ft entry while the header reports 638 ft total depth", "wall_time_seconds": time.perf_counter() - wall, "latency_seconds_per_document_wall": time.perf_counter() - wall, "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    pred_row = {"record_id": row["record_id"], "pdf_path": row["pdf_path"], "pdf_sha256": row["pdf_sha256"], "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT", "human_reviewed": False, "reference_intervals": refs, "predicted_intervals": preds, "matched_interval_count": len(matches), "unmatched_reference_indices": missing, "unmatched_prediction_indices": extra, "document_full_exact": metrics["document_full_exact"], "ocr_text_path": "ocr_pages.txt", "ocr_text_sha256": file_sha256(run / "ocr_pages.txt")}
    (run / "predictions.jsonl").write_text(json.dumps(pred_row, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in ([{"error_type": "missing_interval", "index": i} for i in missing] + [{"error_type": "spurious_interval", "index": i} for i in extra])), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(f"started_utc={started.isoformat()}\ndocuments=1\nreference_intervals={len(refs)}\npredicted_intervals={len(preds)}\nstatus=completed\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)

if __name__ == "__main__":
    main()
