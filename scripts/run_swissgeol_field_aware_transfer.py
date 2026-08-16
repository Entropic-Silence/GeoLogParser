#!/usr/bin/env python3
"""Field-aware depth-column extraction on Swissgeol transfer pages.

This exploratory branch targets the structural failure observed on long
Swissgeol profiles: the OCR contains depth and thickness/sample numbers in
adjacent columns, while the interval-section parser can reject the whole page.
The predictor uses only rendered pixels and OCR boxes. Official database
references are loaded after prediction for transfer diagnostics and are never
used to select a column.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geologparser.ocr import RapidOCROnnxAdapter
from geologparser.layout import locate_named_log_pages
from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


NUMBER = re.compile(r"^\s*([0-9]{1,5}(?:[.,][0-9]{1,3})?)\s*(?:m)?\s*$", re.I)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_number(text: str) -> float | None:
    cleaned = text.strip().replace(",", ".").replace("O", "0").replace("o", "0")
    match = NUMBER.fullmatch(cleaned)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value if 0.0 <= value <= 5000.0 else None


def render_pdf(pdf: Path, output: Path, dpi: int) -> list[Path]:
    prefix = output / "page"
    completed = subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)],
        text=True,
        capture_output=True,
        check=False,
    )
    pages = sorted(output.glob("page-*.png"), key=lambda path: int(path.stem.rsplit("-", 1)[1]))
    if completed.returncode != 0 or not pages:
        raise RuntimeError(f"pdftoppm failed for {pdf}: {completed.stderr.strip()}")
    return pages


def longest_increasing(values: list[dict]) -> list[dict]:
    if not values:
        return []
    lengths = [1] * len(values)
    previous = [-1] * len(values)
    for index in range(len(values)):
        for prior in range(index):
            if values[prior]["value"] < values[index]["value"] and lengths[prior] + 1 > lengths[index]:
                lengths[index] = lengths[prior] + 1
                previous[index] = prior
    end = max(range(len(values)), key=lambda index: (lengths[index], values[index]["value"]))
    output: list[dict] = []
    while end >= 0:
        output.append(values[end])
        end = previous[end]
    return list(reversed(output))


def numeric_clusters(regions: list, width: int, height: int) -> list[list[dict]]:
    numeric: list[dict] = []
    for region in regions:
        value = parse_number(region.text)
        if value is None:
            continue
        x0, y0, x1, y1 = map(float, region.bbox)
        numeric.append({
            "value": value,
            "x_norm": ((x0 + x1) / 2.0) / width,
            "y_px": (y0 + y1) / 2.0,
            "bbox": [x0, y0, x1, y1],
            "source_text": region.text,
            "ocr_confidence": float(region.confidence or 0.0),
        })
    numeric.sort(key=lambda item: (item["x_norm"], item["y_px"]))
    clusters: list[list[dict]] = []
    for item in numeric:
        if not clusters or item["x_norm"] - clusters[-1][-1]["x_norm"] > 0.02:
            clusters.append([item])
        else:
            clusters[-1].append(item)
    return clusters


def score_cluster(cluster: list[dict]) -> tuple[float, list[dict], dict]:
    ordered = sorted(cluster, key=lambda item: item["y_px"])
    deduplicated: list[dict] = []
    for item in ordered:
        if deduplicated and abs(item["y_px"] - deduplicated[-1]["y_px"]) <= 8.0:
            if item["ocr_confidence"] > deduplicated[-1]["ocr_confidence"]:
                deduplicated[-1] = item
        else:
            deduplicated.append(item)
    sequence = longest_increasing(deduplicated)
    values = [item["value"] for item in sequence]
    count = len(values)
    if count < 2:
        return -math.inf, sequence, {"count": count}
    strict_ratio = sum(right > left for left, right in zip(values, values[1:])) / max(1, count - 1)
    span = max(values) - min(values)
    unique_ratio = len(set(values)) / count
    start_bonus = 2.0 if values[0] <= 1.0 else 0.0
    scale_penalty = 4.0 if count <= 12 and all(abs(value - round(value)) < 1e-6 and value % 100 == 0 for value in values) else 0.0
    score = count + 6.0 * strict_ratio + 3.0 * math.log1p(span / 10.0) + 2.0 * unique_ratio + start_bonus - scale_penalty
    return score, sequence, {
        "count": count,
        "strict_monotonic_ratio": strict_ratio,
        "span_m": span,
        "unique_ratio": unique_ratio,
        "x_norm": sum(item["x_norm"] for item in cluster) / len(cluster),
        "score": score,
    }


def extract_page(regions: list, width: int, height: int) -> tuple[list[dict], dict]:
    candidates = []
    for cluster in numeric_clusters(regions, width, height):
        score, sequence, diagnostics = score_cluster(cluster)
        if sequence:
            candidates.append((score, sequence, diagnostics))
    if not candidates:
        return [], {"candidate_cluster_count": 0, "selected": None}
    score, sequence, diagnostics = max(candidates, key=lambda row: row[0])
    return sequence, {
        "candidate_cluster_count": len(candidates),
        "selected": diagnostics,
        "alternatives": [item[2] for item in sorted(candidates, key=lambda row: row[0], reverse=True)[:5]],
    }


def references(row: dict) -> list[float]:
    reference = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))["stratigraphy"]["intervals"]
    return sorted({float(value) for interval in reference for value in (interval["top_depth_m"], interval["bottom_depth_m"])})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--dpi", type=int, default=120)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = load_jsonl(args.manifest)
    adapter = RapidOCROnnxAdapter(intra_op_num_threads=args.threads)
    predictions: dict[str, list[float]] = {}
    diagnostics: list[dict] = []
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="geologparser-field-aware-") as temporary:
        temporary_root = Path(temporary)
        for index, row in enumerate(rows, 1):
            record_id = row["record_id"]
            reference_record = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))
            target_name = str(reference_record.get("borehole", {}).get("name") or "")
            identity_pages = locate_named_log_pages(Path(row["pdf_path"]), target_name) if target_name else ()
            identity_page_set = set(identity_pages)
            record_root = temporary_root / record_id
            record_root.mkdir()
            page_values: list[dict] = []
            page_reports = []
            pages = render_pdf(Path(row["pdf_path"]), record_root, args.dpi)
            for page_number, page in enumerate(pages, 1):
                if identity_page_set and page_number not in identity_page_set:
                    continue
                image = Image.open(page)
                regions = adapter.extract(page)
                selected, report = extract_page(regions, image.width, image.height)
                for item in selected:
                    page_values.append({"page": page_number, **item})
                page_reports.append({"page": page_number, **report, "ocr_region_count": len(regions)})
            page_values.sort(key=lambda item: (item["page"], item["y_px"]))
            deduped: list[dict] = []
            for item in page_values:
                if deduped and abs(item["value"] - deduped[-1]["value"]) <= 0.05:
                    continue
                deduped.append(item)
            if deduped and deduped[0]["value"] > 0.05:
                deduped.insert(0, {"value": 0.0, "page": deduped[0]["page"], "source_text": "implicit_origin", "bbox": [], "ocr_confidence": None})
            values = [float(item["value"]) for item in deduped]
            predictions[record_id] = values
            diagnostics.append({
                "record_id": record_id,
                "target_name_for_page_alignment": target_name or None,
                "identity_aligned_pages": list(identity_pages),
                "page_reports": page_reports,
                "selected_boundary_count": len(values),
                "boundaries": deduped,
            })
            print(f"[{index}/{len(rows)}] {record_id} pages={len(pages)} boundaries={len(values)}", flush=True)
    gold = {row["record_id"]: references(row) for row in rows}
    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_field_aware_transfer_exploration",
        "method_version": "swissgeol_field_aware_numeric_column_identity_routed_v002",
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "document_count": len(rows),
        "page_count": sum(int(row["page_count"]) for row in rows),
        "reference_ground_truth_tier": "AUTHORITATIVE_STRUCTURED_SOURCE",
        "page_database_interval_agreement_verified": False,
        "prediction_reference_conditioning": "borehole_identity_only_for_multi_page_alignment; interval values never used",
        "dpi": args.dpi,
        "ocr_backend": "RapidOCR ONNX",
        "predictions": predictions,
        "diagnostics": diagnostics,
        "boundary": boundary_metrics(predictions, gold, 0.05),
        "interval": interval_metrics(predictions, gold, 0.05),
        "wall_time_seconds": time.perf_counter() - started,
        "limitations": [
            "Exploratory transfer evidence; official database intervals are not verified as complete page-visible Ground Truth.",
            "Column scores are fixed heuristics and were not tuned on this transfer panel.",
            "Authoritative borehole names are used only to align records to pages in multi-borehole reports.",
            "Lithology and descriptions are not evaluated in this branch.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"boundary": report["boundary"], "interval": report["interval"], "wall_time_seconds": report["wall_time_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
