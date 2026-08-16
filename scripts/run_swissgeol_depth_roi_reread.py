#!/usr/bin/env python3
"""High-resolution depth-column rereading driven by field-aware OCR evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geologparser.ocr import RapidOCROnnxAdapter
from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


NUMBER = re.compile(r"^\s*([0-9]{1,5}(?:[.,][0-9]{1,3})?)\s*(?:m)?\s*$", re.I)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_number(text: str) -> float | None:
    match = NUMBER.fullmatch(text.strip().replace(",", ".").replace("O", "0").replace("o", "0"))
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value if 0.0 <= value <= 5000.0 else None


def render_pdf(pdf: Path, output: Path, dpi: int) -> list[Path]:
    prefix = output / "page"
    completed = subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)], text=True, capture_output=True, check=False)
    pages = sorted(output.glob("page-*.png"), key=lambda path: int(path.stem.rsplit("-", 1)[1]))
    if completed.returncode != 0 or not pages:
        raise RuntimeError(f"pdftoppm failed for {pdf}: {completed.stderr.strip()}")
    return pages


def references(row: dict) -> list[float]:
    intervals = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))["stratigraphy"]["intervals"]
    return sorted({float(value) for interval in intervals for value in (interval["top_depth_m"], interval["bottom_depth_m"])})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--field-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--half-width", type=float, default=0.025)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest = load_jsonl(args.manifest)
    initial = json.loads(args.field_report.read_text(encoding="utf-8"))
    initial_predictions = initial["predictions"]
    initial_diagnostics = {row["record_id"]: row for row in initial["diagnostics"]}
    adapter = RapidOCROnnxAdapter(intra_op_num_threads=args.threads)
    predictions: dict[str, list[float]] = {}
    diagnostics: list[dict] = []
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="geologparser-depth-reread-") as temporary:
        root = Path(temporary)
        for index, row in enumerate(manifest, 1):
            record_id = row["record_id"]
            record_root = root / record_id
            record_root.mkdir()
            rendered = render_pdf(Path(row["pdf_path"]), record_root, args.dpi)
            selected = initial_diagnostics[record_id]["page_reports"]
            values: list[dict] = []
            page_reports = []
            for page_number, page in enumerate(rendered, 1):
                page_info = next((item for item in selected if item["page"] == page_number), None)
                selected_info = page_info.get("selected") if page_info else None
                if not selected_info or "x_norm" not in selected_info:
                    page_reports.append({"page": page_number, "status": "no_initial_column"})
                    continue
                image = Image.open(page)
                width, height = image.size
                x_norm = float(selected_info["x_norm"])
                left = max(0, int((x_norm - args.half_width) * width))
                right = min(width, int((x_norm + args.half_width) * width))
                crop_path = record_root / f"crop-{page_number}.png"
                image.crop((left, 0, right, height)).save(crop_path)
                regions = adapter.extract(crop_path)
                candidates = []
                for region in regions:
                    value = parse_number(region.text)
                    if value is None:
                        continue
                    y = (region.bbox[1] + region.bbox[3]) / 2.0
                    candidates.append({"value": value, "y": y, "page": page_number, "source_text": region.text, "bbox": [left + region.bbox[0], region.bbox[1], left + region.bbox[2], region.bbox[3]], "ocr_confidence": float(region.confidence or 0.0)})
                candidates.sort(key=lambda item: item["y"])
                deduped = []
                for item in candidates:
                    if deduped and abs(item["y"] - deduped[-1]["y"]) <= 10:
                        if item["ocr_confidence"] > deduped[-1]["ocr_confidence"]:
                            deduped[-1] = item
                    else:
                        deduped.append(item)
                values.extend(deduped)
                page_reports.append({"page": page_number, "x_norm": x_norm, "crop_bbox": [left, 0, right, height], "ocr_region_count": len(regions), "selected_count": len(deduped)})
            values.sort(key=lambda item: (item["page"], item["y"]))
            deduped = []
            for item in values:
                if deduped and abs(item["value"] - deduped[-1]["value"]) <= 0.05:
                    continue
                deduped.append(item)
            if deduped and deduped[0]["value"] > 0.05:
                deduped.insert(0, {"value": 0.0, "page": deduped[0]["page"], "source_text": "implicit_origin", "bbox": [], "ocr_confidence": None})
            predictions[record_id] = [float(item["value"]) for item in deduped]
            diagnostics.append({"record_id": record_id, "page_reports": page_reports, "selected_boundary_count": len(deduped), "boundaries": deduped})
            print(f"[{index}/{len(manifest)}] {record_id} boundaries={len(deduped)}", flush=True)
    gold = {row["record_id"]: references(row) for row in manifest}
    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_depth_roi_reread_transfer_exploration",
        "method_version": "swissgeol_field_aware_depth_roi_reread_v001",
        "manifest": str(args.manifest),
        "field_report": str(args.field_report),
        "document_count": len(manifest),
        "page_count": sum(int(row["page_count"]) for row in manifest),
        "reference_ground_truth_tier": "AUTHORITATIVE_STRUCTURED_SOURCE",
        "page_database_interval_agreement_verified": False,
        "prediction_reference_conditioning": "none",
        "dpi": args.dpi,
        "half_width_normalized": args.half_width,
        "predictions": predictions,
        "diagnostics": diagnostics,
        "baseline_field_aware": {"boundary": boundary_metrics(initial_predictions, gold, 0.05), "interval": interval_metrics(initial_predictions, gold, 0.05)},
        "reread": {"boundary": boundary_metrics(predictions, gold, 0.05), "interval": interval_metrics(predictions, gold, 0.05)},
        "wall_time_seconds": time.perf_counter() - started,
        "limitations": [
            "Exploratory transfer evidence; page/database agreement is unverified.",
            "ROI center is inherited from the exploratory field-aware detector and was not tuned with transfer references.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"baseline": report["baseline_field_aware"], "reread": report["reread"], "wall_time_seconds": report["wall_time_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
