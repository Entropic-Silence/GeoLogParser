#!/usr/bin/env python3
"""Raster-only interval benchmark for paired BGS offshore borehole scans."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import platform
import re
import resource
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

from geologparser.evaluation import (
    boundary_matched_interval_metrics,
    match_intervals_by_boundaries,
)
from geologparser.experiment import create_run_directory
from geologparser.ocr import RapidOCROnnxAdapter
from geologparser.ocr.rapidocr import DEFAULT_MODEL_DIR, MODEL_FILENAMES
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
NUMBER_RE = re.compile(r"^\s*([0-9]{1,4}(?:[.,][0-9]{1,3})?)\s*m?\s*$", re.I)
LITHOLOGY_TERMS = (
    "sandstone", "limestone", "mudstone", "clay", "sand", "gravel",
    "siltstone", "silt", "mud", "shale", "chalk", "peat", "boulder",
    "rock", "basement", "evaporite",
)


@dataclass(frozen=True)
class Region:
    text: str
    confidence: float
    bbox: tuple[float, float, float, float]

    @property
    def center_x(self) -> float:
        return (self.bbox[0] + self.bbox[2]) / 2

    @property
    def center_y(self) -> float:
        return (self.bbox[1] + self.bbox[3]) / 2


def normal(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_number(text: str) -> float | None:
    match = NUMBER_RE.fullmatch(text.replace("O", "0").replace("o", "0"))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def reference_intervals(row: dict) -> list[dict]:
    return [
        {
            "top_depth_m": float(item["top_depth_m"]),
            "bottom_depth_m": float(item["bottom_depth_m"]),
            "thickness_m": float(item["thickness_m"]),
            "lithology_raw": item.get("lithology_raw") or item.get("description_raw") or "",
            "lithology_normalized": normal(
                item.get("lithology_normalized")
                or item.get("lithology_raw")
                or ""
            ),
        }
        for item in row["intervals"]
    ]


def tesseract_regions(image: Path, psm: int) -> tuple[list[Region], str]:
    completed = subprocess.run(
        ["tesseract", str(image), "stdout", "-l", "eng", "--psm", str(psm), "tsv"],
        capture_output=True, text=True, check=True,
    )
    rows = completed.stdout.splitlines()
    if not rows:
        return [], completed.stdout
    header = rows[0].split("\t")
    regions: list[Region] = []
    for raw in rows[1:]:
        values = raw.split("\t")
        if len(values) != len(header):
            continue
        row = dict(zip(header, values))
        text = row.get("text", "").strip()
        if not text:
            continue
        try:
            left, top = float(row["left"]), float(row["top"])
            width, height = float(row["width"]), float(row["height"])
            confidence = max(0.0, float(row["conf"]) / 100.0)
        except ValueError:
            continue
        regions.append(Region(text, confidence, (left, top, left + width, top + height)))
    return regions, completed.stdout


def rapidocr_regions(adapter: RapidOCROnnxAdapter, image: Path) -> list[Region]:
    return [
        Region(item.text, float(item.confidence or 0.0), tuple(item.bbox))
        for item in adapter.extract(image)
        if item.bbox is not None and item.text.strip()
    ]


def parse_composite_regions(
    regions: list[Region], width: int, height: int, page: int, backend: str,
) -> list[dict]:
    # BGS composite logs place the numeric depth scale immediately left of the
    # description column.  The normalized windows deliberately exclude the
    # header and the left stratigraphy column.
    depth_regions: list[tuple[Region, float]] = []
    for region in regions:
        x = region.center_x / width
        y = region.center_y / height
        value = parse_number(region.text)
        if value is None or not 0 <= value <= 5000:
            continue
        if 0.40 <= x <= 0.62 and y >= 0.43:
            depth_regions.append((region, value))
    depth_regions.sort(key=lambda item: item[0].center_y)
    unique: list[tuple[Region, float]] = []
    for region, value in depth_regions:
        if unique and abs(region.center_y - unique[-1][0].center_y) < max(12, region.bbox[3] - region.bbox[1]):
            if region.confidence > unique[-1][0].confidence:
                unique[-1] = (region, value)
        else:
            unique.append((region, value))
    output: list[dict] = []
    for index in range(len(unique) - 1):
        top_region, top = unique[index]
        bottom_region, bottom = unique[index + 1]
        if not top < bottom:
            continue
        y0, y1 = top_region.center_y, bottom_region.center_y
        description_regions = [
            region for region in regions
            if 0.50 <= region.bbox[0] / width <= 0.86
            and y0 + 4 <= region.center_y <= y1 - 2
            and parse_number(region.text) is None
            and re.search(r"[A-Za-z]", region.text)
        ]
        description_regions.sort(key=lambda item: (item.center_y, item.bbox[0]))
        description = re.sub(
            r"\s+", " ", " ".join(item.text for item in description_regions)
        ).strip(" |_:;.,-")
        if not description or re.fullmatch(r"(?i)(depth|in|metres|metres below sea bed|description)", description):
            description = ""
        canonical = ""
        lowered = description.lower()
        for term in LITHOLOGY_TERMS:
            if term in lowered:
                canonical = term
                break
        evidence_regions = [top_region, bottom_region, *description_regions]
        output.append({
            "top_depth_m": top,
            "bottom_depth_m": bottom,
            "thickness_m": bottom - top,
            "lithology_raw": description,
            "lithology_normalized": canonical or normal(description),
            "source_page": page,
            "source_unit": "m_below_seabed",
            "evidence": {
                "backend": backend,
                "confidence": min(item.confidence for item in evidence_regions),
                "regions": [
                    {"text": item.text, "confidence": item.confidence, "bbox": list(item.bbox)}
                    for item in evidence_regions
                ],
            },
        })
    dedup: list[dict] = []
    seen: set[tuple[float, float]] = set()
    for item in output:
        key = (round(item["top_depth_m"], 5), round(item["bottom_depth_m"], 5))
        if key not in seen:
            dedup.append(item)
            seen.add(key)
    return dedup


def render_page(pdf: Path, page: int, root: Path, dpi: int) -> Path:
    output = root / f"page-{page}"
    completed = subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi), "-f", str(page), "-l", str(page), "-singlefile", str(pdf), str(output)],
        capture_output=True, text=True, check=False,
    )
    rendered = output.with_suffix(".png")
    if completed.returncode or not rendered.is_file():
        raise RuntimeError(completed.stderr.strip() or "pdftoppm failed")
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--backend", choices=("rapidocr", "tesseract"), required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "datasets/manifests/bgs_offshore_gold_v001.jsonl")
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--psm", type=int, default=11)
    args = parser.parse_args()
    manifest = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not manifest or any(row["ground_truth_tier"] != "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT" for row in manifest):
        raise ValueError("unexpected BGS authoritative manifest")
    for row in manifest:
        if file_sha256(Path(row["pdf_path"])) != row["pdf_sha256"]:
            raise ValueError(f"source PDF hash mismatch: {row['record_id']}")

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tesseract_revision = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    model_hashes = {name: file_sha256(DEFAULT_MODEL_DIR / filename) for name, filename in MODEL_FILENAMES.items()}
    model_revision = json.dumps(model_hashes, sort_keys=True) if args.backend == "rapidocr" else tesseract_revision
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id, "git_commit": commit, "date": date.today().isoformat(),
        "dataset_version": "bgs_offshore_paired_v001", "split_version": "bgs_offshore_gold_split_v001_test",
        "model": f"{args.backend}_bgs_composite_interval_parser_v001", "model_revision": model_revision,
        "prompt_version": "not_applicable", "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version(), "tesseract": tesseract_revision},
        "config": {
            "ground_truth_sha256": file_sha256(args.manifest), "prediction_reference_conditioning": "none",
            "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT", "render_dpi": args.dpi,
            "tesseract_psm": args.psm, "evaluation_pages_only": True,
            "evaluated_fields": ["interval.top_depth_m", "interval.bottom_depth_m", "interval.thickness_m", "interval.lithology_normalized"],
            "reference_scope": "BGS official Borehole Geology Data rows explicitly interpreted from graphic logs",
            "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        }, "started_utc": started.isoformat(),
    })
    wall = time.perf_counter()
    adapter = RapidOCROnnxAdapter(intra_op_num_threads=4) if args.backend == "rapidocr" else None
    refs_by_doc, preds_by_doc, prediction_rows, errors = [], [], [], []
    for row in manifest:
        refs = reference_intervals(row)
        predictions: list[dict] = []
        evidence_rows: list[dict] = []
        with tempfile.TemporaryDirectory(prefix="geologparser-bgs-") as temporary:
            temporary_root = Path(temporary)
            for page in row["evaluation_pages"]:
                image = render_page(Path(row["pdf_path"]), int(page), temporary_root, args.dpi)
                with Image.open(image) as opened:
                    width, height = opened.size
                if args.backend == "rapidocr":
                    regions = rapidocr_regions(adapter, image)
                    raw = None
                else:
                    regions, raw = tesseract_regions(image, args.psm)
                predictions.extend(parse_composite_regions(regions, width, height, int(page), args.backend))
                image_copy = run / f"{row['record_id']}_page-{page}.png"
                shutil.copy2(image, image_copy)
                region_path = run / f"{row['record_id']}_page-{page}_regions.jsonl"
                region_path.write_text(
                    "".join(json.dumps({"bbox": list(item.bbox), "text": item.text, "confidence": item.confidence}, sort_keys=True) + "\n" for item in regions),
                    encoding="utf-8",
                )
                evidence = {"page": int(page), "image_path": image_copy.name, "image_sha256": file_sha256(image_copy), "ocr_regions_path": region_path.name, "ocr_regions_sha256": file_sha256(region_path)}
                if raw is not None:
                    tsv_path = run / f"{row['record_id']}_page-{page}.tsv"
                    tsv_path.write_text(raw, encoding="utf-8")
                    evidence.update({"ocr_tsv_path": tsv_path.name, "ocr_tsv_sha256": file_sha256(tsv_path)})
                evidence_rows.append(evidence)
        predictions.sort(key=lambda item: (item["top_depth_m"], item["bottom_depth_m"], item["source_page"]))
        matches, missing, extra = match_intervals_by_boundaries(refs, predictions, tolerance_m=0.05)
        lith_correct = sum(refs[item.reference_index]["lithology_normalized"] == predictions[item.prediction_index]["lithology_normalized"] for item in matches)
        refs_by_doc.append(refs)
        preds_by_doc.append(predictions)
        prediction_rows.append({
            "record_id": row["record_id"], "borehole_id": row["borehole_id"], "pdf_sha256": row["pdf_sha256"],
            "ground_truth_tier": row["ground_truth_tier"], "human_reviewed": False,
            "reference_intervals": refs, "predicted_intervals": predictions,
            "matched_interval_count": len(matches), "matched_lithology_exact_count": lith_correct,
            "unmatched_reference_indices": missing, "unmatched_prediction_indices": extra,
            "evidence": evidence_rows,
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
        "page_count": sum(len(row["evaluation_pages"]) for row in manifest), "reference_interval_count": sum(len(rows) for rows in refs_by_doc),
        "predicted_interval_count": sum(len(rows) for rows in preds_by_doc), "documents_with_predictions": sum(bool(rows) for rows in preds_by_doc),
        "interval_metrics": {name: result.to_dict() for name, result in interval_metrics.items()},
        "matched_lithology_exact": {"value": total_lith_correct / total_matches if total_matches else None, "numerator": total_lith_correct, "denominator": total_matches},
        "source_domain": "British Geological Survey GeoIndex Offshore",
        "selection_limitation": "26 source groups selected from 251 eligible paired graphic-log candidates; 34 composite pages evaluated; scan rights remain pending manual pre-submission verification",
        "wall_time_seconds": time.perf_counter() - wall, "latency_seconds_per_document_wall": (time.perf_counter() - wall) / len(manifest),
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (run / "predictions.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in prediction_rows), encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in errors), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(f"started_utc={started.isoformat()}\nbackend={args.backend}\ndocuments={len(manifest)}\nreference_intervals={metrics['reference_interval_count']}\npredicted_intervals={metrics['predicted_interval_count']}\nstatus=completed\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
