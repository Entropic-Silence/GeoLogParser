#!/usr/bin/env python3
"""Cross-engine coverage audit on official image-only USGS lithologic logs.

The USGS log sheets are source documents, not a project annotation set.  This
audit therefore reports page/document coverage, lexical evidence and engine
disagreement only; it does not claim interval accuracy or human Ground Truth.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
from geologparser.runtime_resources import peak_process_rss_kib
import subprocess
import tempfile
import time
from datetime import date
from pathlib import Path

from geologparser.experiment import create_run_directory
from geologparser.ocr import RapidOCROnnxAdapter
from geologparser.result_index import file_sha256, write_artifact_manifest

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path("/data/GeoLogParser/models/rapidocr")
MODEL_FILES = (
    "ch_PP-OCRv4_det_infer.onnx",
    "ch_PP-OCRv4_rec_infer.onnx",
    "ch_ppocr_mobile_v2.0_cls_infer.onnx",
)
RANGE_RE = re.compile(r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)(?!\d)")
LITH_RE = re.compile(r"\bLITHOLOGY\s*:\s*([A-Za-z][A-Za-z -]{1,40})", re.I)
HEADER_RE = re.compile(r"\b(?:Official Name|USGS Site ID|Total Core Recovered|County & State)\b", re.I)


def render_page(pdf: Path, page: int, out_dir: Path, dpi: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "page"
    completed = subprocess.run(
        ["pdftoppm", "-png", "-singlefile", "-r", str(dpi), "-f", str(page), "-l", str(page), str(pdf), str(prefix)],
        text=True, capture_output=True, check=False,
    )
    image = out_dir / "page.png"
    if completed.returncode != 0 or not image.exists():
        raise RuntimeError(f"pdftoppm failed for {pdf} page {page}: {completed.stderr.strip()}")
    return image


def lexical_features(text: str) -> dict:
    normalized = " ".join(text.split())
    ranges = [(float(a), float(b)) for a, b in RANGE_RE.findall(normalized) if float(b) > float(a)]
    lithologies = [" ".join(m.split()).strip(" .,:;") for m in LITH_RE.findall(normalized)]
    return {
        "text_chars": len(normalized),
        "has_text": bool(normalized),
        "header_marker": bool(HEADER_RE.search(normalized)),
        "lithology_label": bool(lithologies),
        "lithology_labels": lithologies[:8],
        "depth_range_count": len(ranges),
        "depth_ranges": ranges[:20],
        "numeric_token_count": len(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", normalized)),
    }


def tesseract_text(image: Path, psm: int) -> str:
    completed = subprocess.run(
        ["tesseract", str(image), "stdout", "-l", "eng", "--psm", str(psm)],
        text=True, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--dataset-root", type=Path, default=Path("/data/GeoLogParser/datasets/public/usgs_idaho_lithologic_v001"))
    ap.add_argument("--results-root", type=Path, default=ROOT / "results")
    ap.add_argument("--dpi", type=int, default=180)
    ap.add_argument("--rapidocr-threads", type=int, default=4)
    args = ap.parse_args()
    pdfs = sorted(args.dataset_root.rglob("*.pdf"))
    if not pdfs:
        raise ValueError("no PDF logs found")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    rapid_hashes = {name: file_sha256(MODEL_DIR / name) for name in MODEL_FILES}
    rapid = RapidOCROnnxAdapter(model_dir=MODEL_DIR, intra_op_num_threads=args.rapidocr_threads)
    tesseract_revision = subprocess.run(["tesseract", "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0]
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": "usgs_idaho_lithologic_v001",
        "split_version": "source_document_disjoint_scan_audit_v001",
        "model": "tesseract_psm11_vs_rapidocr_ppocrv4_page_coverage",
        "model_revision": tesseract_revision,
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version(), "tesseract": tesseract_revision},
        "config": {
            "render_dpi": args.dpi,
            "tesseract_psm": 11,
            "rapidocr_threads": args.rapidocr_threads,
            "rapidocr_model_dir": str(MODEL_DIR),
            "rapidocr_model_sha256": rapid_hashes,
            "source_tier": "OFFICIAL_SOURCE_SCAN_COVERAGE_AUDIT",
            "human_reviewed": False,
            "accuracy_metrics": "not computed; no independent interval labels",
            "dataset_manifest_sha256": file_sha256(args.dataset_root / "metadata" / "acquisition.json"),
        },
    })
    started = time.perf_counter()
    rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="geologparser-usgs-idaho-") as temp:
        temp_root = Path(temp)
        for pdf_index, pdf in enumerate(pdfs, 1):
            info = subprocess.run(["pdfinfo", str(pdf)], text=True, capture_output=True, check=True).stdout
            page_match = re.search(r"^Pages:\s+(\d+)", info, re.M)
            pages = int(page_match.group(1)) if page_match else 0
            pdf_rows = []
            for page in range(1, pages + 1):
                page_dir = temp_root / f"p{pdf_index:03d}_{page:04d}"
                image = render_page(pdf, page, page_dir, args.dpi)
                t_text = tesseract_text(image, 11)
                r_regions = rapid.extract(image)
                r_text = "\n".join(region.text for region in r_regions)
                t_features, r_features = lexical_features(t_text), lexical_features(r_text)
                row = {
                    "document_id": pdf.stem,
                    "source_pdf": str(pdf),
                    "source_pdf_sha256": file_sha256(pdf),
                    "page": page,
                    "tesseract": t_features,
                    "rapidocr": r_features,
                    "engine_agreement": {
                        "has_text_equal": t_features["has_text"] == r_features["has_text"],
                        "lithology_label_equal": t_features["lithology_label"] == r_features["lithology_label"],
                        "header_marker_equal": t_features["header_marker"] == r_features["header_marker"],
                    },
                }
                pdf_rows.append(row)
                if page % 20 == 0 or page == pages:
                    print(f"document={pdf.stem} page={page}/{pages}", flush=True)
            rows.extend(pdf_rows)
    by_doc = {}
    for row in rows:
        by_doc.setdefault(row["document_id"], []).append(row)
    document_summary = []
    for doc, items in sorted(by_doc.items()):
        def count(engine: str, key: str) -> int:
            return sum(bool(item[engine][key]) for item in items)
        document_summary.append({
            "document_id": doc,
            "page_count": len(items),
            "tesseract_text_pages": count("tesseract", "has_text"),
            "rapidocr_text_pages": count("rapidocr", "has_text"),
            "tesseract_lithology_pages": count("tesseract", "lithology_label"),
            "rapidocr_lithology_pages": count("rapidocr", "lithology_label"),
            "tesseract_header_pages": count("tesseract", "header_marker"),
            "rapidocr_header_pages": count("rapidocr", "header_marker"),
            "both_lithology_pages": sum(item["tesseract"]["lithology_label"] and item["rapidocr"]["lithology_label"] for item in items),
            "lithology_disagreement_pages": sum(item["tesseract"]["lithology_label"] != item["rapidocr"]["lithology_label"] for item in items),
        })
    total_pages = len(rows)
    summary = {
        "scope": "official USGS Idaho image-only lithologic-log cross-engine coverage audit",
        "ground_truth_tier": "OFFICIAL_SOURCE_SCAN_COVERAGE_AUDIT",
        "human_reviewed": False,
        "accuracy_metrics": None,
        "document_count": len(document_summary),
        "page_count": total_pages,
        "tesseract_text_pages": sum(row["tesseract"]["has_text"] for row in rows),
        "rapidocr_text_pages": sum(row["rapidocr"]["has_text"] for row in rows),
        "tesseract_lithology_pages": sum(row["tesseract"]["lithology_label"] for row in rows),
        "rapidocr_lithology_pages": sum(row["rapidocr"]["lithology_label"] for row in rows),
        "both_lithology_pages": sum(row["tesseract"]["lithology_label"] and row["rapidocr"]["lithology_label"] for row in rows),
        "lithology_disagreement_pages": sum(row["tesseract"]["lithology_label"] != row["rapidocr"]["lithology_label"] for row in rows),
        "tesseract_total_depth_ranges": sum(row["tesseract"]["depth_range_count"] for row in rows),
        "rapidocr_total_depth_ranges": sum(row["rapidocr"]["depth_range_count"] for row in rows),
        "document_summary": document_summary,
        "wall_time_seconds": time.perf_counter() - started,
        "peak_process_rss_kib": peak_process_rss_kib(),
        "publication_use": "cross-source coverage and failure-event evidence only; no interval accuracy claim",
    }
    serialized_rows = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    (run / "page_audit.jsonl").write_text(serialized_rows, encoding="utf-8")
    (run / "predictions.jsonl").write_text(serialized_rows, encoding="utf-8")
    (run / "document_summary.json").write_text(json.dumps(document_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps({"document_id": row["document_id"], "page": row["page"], "error_type": "engine_lithology_label_disagreement"}, sort_keys=True) + "\n" for row in rows if row["tesseract"]["lithology_label"] != row["rapidocr"]["lithology_label"]), encoding="utf-8")
    (run / "run.log").write_text(f"documents={len(document_summary)}\npages={total_pages}\nstatus=completed\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(json.dumps({"result_path": str(run), "summary": summary}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
