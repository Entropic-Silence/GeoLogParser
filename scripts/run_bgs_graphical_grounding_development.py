#!/usr/bin/env python3
"""Evaluate reference-blind raster contact grounding on BGS v001 development."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import time

import cv2

from geologparser.layout import ground_graphical_boundaries, infer_log_panel_layout
from geologparser.ocr import TextRegion
from geologparser.result_index import file_sha256
from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def deduplicate(values: list[float], tolerance: float = 0.025) -> list[float]:
    output = []
    for value in sorted(values):
        if not output or value - output[-1] > tolerance:
            output.append(value)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "datasets/manifests/bgs_offshore_gold_v001.jsonl")
    parser.add_argument("--source-run", type=Path, default=ROOT / "results/2026-08-15/P1_BGS_OFFSHORE_V001_TESSERACT_CROSS_SOURCE_FORMAL_001")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper2/analysis/bgs_graphical_grounding_development_v001.json")
    args = parser.parse_args()
    started = time.perf_counter()
    sources = load_jsonl(args.manifest)
    predictions: dict[str, list[float]] = {}
    candidate_predictions: dict[str, list[float]] = {}
    documents = []
    for source_row in sources:
        generation_source = {
            "record_id": source_row["record_id"],
            "evaluation_pages": list(source_row["evaluation_pages"]),
        }
        selected_depths: list[float] = []
        candidate_depths: list[float] = []
        pages = []
        for page in generation_source["evaluation_pages"]:
            image_path = args.source_run / f"{generation_source['record_id']}_page-{page}.png"
            region_path = args.source_run / f"{generation_source['record_id']}_page-{page}_regions.jsonl"
            gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            rows = load_jsonl(region_path)
            if gray is None:
                pages.append({"page": page, "status": "missing_image", "axis": None, "events": []})
                continue
            height, width = gray.shape
            regions = [TextRegion(
                page=int(page), bbox=tuple(row["bbox"]), text=str(row["text"]),
                confidence=float(row.get("confidence") or 0.0), method="frozen_full_page",
            ) for row in rows]
            layout = infer_log_panel_layout(regions, width, height)
            if layout is None:
                pages.append({"page": page, "status": "layout_abstained", "axis": None, "events": []})
                continue
            axis, events = ground_graphical_boundaries(rows, gray, layout=layout)
            if axis is None or not events:
                pages.append({
                    "page": page, "status": "axis_or_graphic_abstained",
                    "axis": axis.to_dict() if axis else None, "events": [],
                })
                continue
            page_candidates = []
            page_selected = []
            for event in events:
                raw = float(event.depth_m)
                hypotheses = {raw, round(raw * 20.0) / 20.0, round(raw * 10.0) / 10.0}
                page_candidates.extend(value for value in hypotheses if 0.0 <= value <= 5000.0)
                if event.line_support >= 0.26 and event.confidence >= 0.20:
                    page_selected.append(round(raw * 20.0) / 20.0)
            candidate_depths.extend(page_candidates)
            selected_depths.extend(page_selected)
            pages.append({
                "page": page, "status": "grounded", "axis": axis.to_dict(),
                "events": [event.to_dict() for event in events],
                "candidate_depths_m": deduplicate(page_candidates),
                "selected_depths_m": deduplicate(page_selected),
            })
        record_id = generation_source["record_id"]
        candidate_predictions[record_id] = deduplicate(candidate_depths)
        predictions[record_id] = deduplicate(selected_depths)
        documents.append({
            "record_id": record_id, "pages": pages,
            "candidate_boundaries_m": candidate_predictions[record_id],
            "selected_boundaries_m": predictions[record_id],
        })

    # References are first accessed after all image-derived predictions exist.
    references = {
        row["record_id"]: sorted({
            float(interval[key])
            for interval in row["intervals"]
            for key in ("top_depth_m", "bottom_depth_m")
        })
        for row in sources
    }
    metrics = {}
    for tolerance in (0.05, 0.10):
        metrics[f"{tolerance:.2f}"] = {
            "candidate_boundary": boundary_metrics(candidate_predictions, references, tolerance),
            "selected_boundary": boundary_metrics(predictions, references, tolerance),
            "selected_interval": interval_metrics(predictions, references, tolerance),
        }
    grounded_pages = sum(page["status"] == "grounded" for document in documents for page in document["pages"])
    report = {
        "experiment_id": "P2_BGS_GRAPHICAL_GROUNDING_DEVELOPMENT_V001",
        "evaluation_role": "development_only",
        "method": "reference-blind numeric depth-axis reconstruction plus horizontal contact grounding",
        "manifest": str(args.manifest), "manifest_sha256": file_sha256(args.manifest),
        "source_run": str(args.source_run),
        "source_predictions_sha256": file_sha256(args.source_run / "predictions.jsonl"),
        "document_count": len(sources),
        "page_count": sum(len(row["evaluation_pages"]) for row in sources),
        "reference_boundary_count": sum(map(len, references.values())),
        "grounded_page_count": grounded_pages,
        "grounded_page_coverage": grounded_pages / sum(len(row["evaluation_pages"]) for row in sources),
        "metrics_by_tolerance_m": metrics,
        "predictions": documents,
        "reference_blinding": "layout, axis fitting, line detection, confidence and rounding fixed before official interval arrays were used for scoring",
        "frozen_external_policy": "BGS v002 is consumed validation; BGS v003 remains unopened and was not used",
        "wall_time_seconds": time.perf_counter() - started,
        "latency_seconds_per_page": (time.perf_counter() - started) / sum(len(row["evaluation_pages"]) for row in sources),
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "limitations": [
            "This is a development diagnostic, not untouched external confirmation.",
            "Line grounding alone does not determine lithology or description semantics.",
            "Candidate coverage includes deterministic 0.05 m and 0.10 m geometry hypotheses and must not be reported as selected precision.",
        ],
    }
    if args.output.exists():
        raise FileExistsError(f"immutable experiment output already exists: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "grounded_page_coverage": report["grounded_page_coverage"],
        "metrics_by_tolerance_m": metrics,
        "latency_seconds_per_page": report["latency_seconds_per_page"],
    }, indent=2))


if __name__ == "__main__":
    main()
