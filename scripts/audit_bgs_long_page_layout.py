#!/usr/bin/env python3
"""Development-only attribution audit for BGS long-page semantic layout."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image

from geologparser.layout import infer_log_panel_layout, long_page_tiles
from geologparser.ocr import TextRegion
from geologparser.result_index import file_sha256


NUMBER = re.compile(r"^\s*([0-9]{1,4}(?:[.,][0-9]{1,3})?)\s*m?\s*$", re.I)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def numeric_regions(rows: list[dict], width: int, height: int) -> list[tuple[float, float, float]]:
    output = []
    for row in rows:
        text = row["text"].replace("O", "0").replace("o", "0")
        match = NUMBER.fullmatch(text)
        if not match:
            continue
        value = float(match.group(1).replace(",", "."))
        x1, y1, x2, y2 = row["bbox"]
        output.append((value, ((x1 + x2) / 2) / width, ((y1 + y2) / 2) / height))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    documents = []
    for source in load_jsonl(args.manifest):
        reference_boundaries = sorted(
            {float(row["top_depth_m"]) for row in source["intervals"]}
            | {float(row["bottom_depth_m"]) for row in source["intervals"]}
        )
        page_rows = []
        visible_any: set[float] = set()
        visible_panel: set[float] = set()
        for page in source["evaluation_pages"]:
            image_path = args.source_run / f"{source['record_id']}_page-{page}.png"
            region_path = args.source_run / f"{source['record_id']}_page-{page}_regions.jsonl"
            if not image_path.is_file() or not region_path.is_file():
                raise FileNotFoundError(f"missing frozen page evidence for {source['record_id']} page {page}")
            rows = load_jsonl(region_path)
            with Image.open(image_path) as image:
                width, height = image.size
            regions = [
                TextRegion(
                    page=int(page), bbox=tuple(row["bbox"]), text=row["text"],
                    confidence=float(row.get("confidence") or 0.0), method="frozen_tesseract",
                )
                for row in rows
            ]
            layout = infer_log_panel_layout(regions, width, height)
            numbers = numeric_regions(rows, width, height)
            for reference in reference_boundaries:
                if any(abs(value - reference) <= 1e-6 for value, _, _ in numbers):
                    visible_any.add(reference)
                if layout and any(
                    abs(value - reference) <= 1e-6
                    and layout.x_min <= x <= layout.x_max
                    and layout.y_min <= y <= layout.y_max
                    for value, x, y in numbers
                ):
                    visible_panel.add(reference)
            tiles = long_page_tiles(width, height, layout) if layout else []
            page_rows.append({
                "page": int(page), "width": width, "height": height,
                "aspect_ratio": height / width,
                "layout_detected": layout is not None,
                "anchor_semantics": sorted(layout.anchors) if layout else [],
                "anchor_row_score": layout.anchor_row_score if layout else None,
                "panel_bbox_normalized": (
                    [layout.x_min, layout.y_min, layout.x_max, layout.y_max] if layout else None
                ),
                "tile_count": len(tiles),
            })
        documents.append({
            "record_id": source["record_id"],
            "source_title": source.get("source_title"),
            "reference_boundary_count": len(reference_boundaries),
            "visible_boundary_count_anywhere": len(visible_any),
            "visible_boundary_count_semantic_panel": len(visible_panel),
            "pages": page_rows,
        })

    boundary_total = sum(row["reference_boundary_count"] for row in documents)
    anywhere = sum(row["visible_boundary_count_anywhere"] for row in documents)
    panel = sum(row["visible_boundary_count_semantic_panel"] for row in documents)
    pages = [page for row in documents for page in row["pages"]]
    report = {
        "analysis_scope": "development-only long-page layout and OCR-to-structure failure attribution",
        "prediction_reference_conditioning": "layout inferred before references; references used only for post-hoc visibility counts",
        "manifest_path": str(args.manifest),
        "manifest_sha256": file_sha256(args.manifest),
        "source_run_path": str(args.source_run),
        "document_count": len(documents),
        "page_count": len(pages),
        "long_page_count_aspect_ratio_ge_2": sum(page["aspect_ratio"] >= 2 for page in pages),
        "semantic_layout_detected_pages": sum(page["layout_detected"] for page in pages),
        "reference_boundary_count": boundary_total,
        "full_page_numeric_visibility": {
            "numerator": anywhere, "denominator": boundary_total,
            "value": anywhere / boundary_total if boundary_total else None,
        },
        "semantic_panel_numeric_visibility": {
            "numerator": panel, "denominator": boundary_total,
            "value": panel / boundary_total if boundary_total else None,
        },
        "mean_tiles_per_detected_page": (
            sum(page["tile_count"] for page in pages if page["layout_detected"])
            / sum(page["layout_detected"] for page in pages)
            if any(page["layout_detected"] for page in pages) else None
        ),
        "documents": documents,
        "limitations": [
            "This audit uses the previously inspected BGS v001 source groups and is development evidence only.",
            "Numeric visibility measures exact OCR token presence, not correct field assignment or interval extraction.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
