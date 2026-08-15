#!/usr/bin/env python3
"""Development-only multiscale long-page rereading visibility experiment."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import tempfile

import cv2
from PIL import Image

from geologparser.layout import infer_log_panel_layout, long_page_tiles
from geologparser.ocr import TextRegion
from geologparser.result_index import file_sha256


NUMBER = re.compile(r"^\s*([0-9]{1,4}(?:[.,][0-9]{1,3})?)\s*m?\s*$", re.I)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def number(text: str) -> float | None:
    match = NUMBER.fullmatch(text.replace("O", "0").replace("o", "0"))
    return float(match.group(1).replace(",", ".")) if match else None


def tesseract_tsv(image: Path, psm: int) -> list[dict]:
    completed = subprocess.run(
        ["tesseract", str(image), "stdout", "-l", "eng", "--psm", str(psm), "tsv"],
        capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0:
        return []
    lines = completed.stdout.splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    output = []
    for raw in lines[1:]:
        values = raw.split("\t")
        if len(values) != len(header):
            continue
        row = dict(zip(header, values))
        value = number(row.get("text", ""))
        if value is None:
            continue
        try:
            output.append({
                "value": value, "text": row["text"],
                "confidence": max(0.0, float(row["conf"]) / 100),
                "bbox": [float(row["left"]), float(row["top"]),
                         float(row["left"]) + float(row["width"]),
                         float(row["top"]) + float(row["height"])],
            })
        except ValueError:
            continue
    return output


def reread_tile(task: dict) -> list[dict]:
    image = cv2.imread(task["source"], cv2.IMREAD_GRAYSCALE)
    x1, y1, x2, y2 = task["bbox"]
    crop = image[y1:y2, x1:x2]
    resized = cv2.resize(crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    variants = {"gray": resized}
    variants["otsu"] = cv2.threshold(
        resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )[1]
    output = []
    with tempfile.TemporaryDirectory(prefix="geologparser-bgs-tile-") as temporary:
        root = Path(temporary)
        for variant, pixels in variants.items():
            image_path = root / f"{variant}.png"
            cv2.imwrite(str(image_path), pixels)
            for psm in (6, 11):
                for row in tesseract_tsv(image_path, psm):
                    bx1, by1, bx2, by2 = row["bbox"]
                    row["bbox"] = [
                        x1 + bx1 / 2, y1 + by1 / 2,
                        x1 + bx2 / 2, y1 + by2 / 2,
                    ]
                    row.update({
                        "page": task["page"], "tile_id": task["tile_id"],
                        "variant": variant, "psm": psm,
                    })
                    output.append(row)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-workers", type=int, default=8)
    args = parser.parse_args()
    documents = []
    tasks = []
    page_context: dict[tuple[str, int], dict] = {}
    sources = load_jsonl(args.manifest)
    for source in sources:
        for page in source["evaluation_pages"]:
            image_path = args.source_run / f"{source['record_id']}_page-{page}.png"
            region_path = args.source_run / f"{source['record_id']}_page-{page}_regions.jsonl"
            rows = load_jsonl(region_path)
            with Image.open(image_path) as image:
                width, height = image.size
            regions = [TextRegion(
                page=int(page), bbox=tuple(row["bbox"]), text=row["text"],
                confidence=float(row.get("confidence") or 0), method="frozen_full_page",
            ) for row in rows]
            layout = infer_log_panel_layout(regions, width, height)
            tiles = long_page_tiles(width, height, layout) if layout else []
            key = (source["record_id"], int(page))
            baseline = [
                {
                    "value": value, "text": row["text"], "bbox": row["bbox"],
                    "confidence": float(row.get("confidence") or 0.0),
                    "variant": None, "psm": None,
                }
                for row in rows if (value := number(row["text"])) is not None
            ]
            page_context[key] = {
                "baseline": baseline, "layout_detected": layout is not None,
                "tile_count": len(tiles), "reread": [],
            }
            for tile in tiles:
                tasks.append({
                    "record_id": source["record_id"], "page": int(page),
                    "source": str(image_path), "tile_id": tile.tile_id,
                    "bbox": tile.bbox,
                })

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        for task, rows in zip(tasks, executor.map(reread_tile, tasks)):
            page_context[(task["record_id"], task["page"])]["reread"].extend(rows)

    for source in sources:
        references = sorted(
            {float(row["top_depth_m"]) for row in source["intervals"]}
            | {float(row["bottom_depth_m"]) for row in source["intervals"]}
        )
        baseline_values = {
            row["value"] for page in source["evaluation_pages"]
            for row in page_context[(source["record_id"], int(page))]["baseline"]
        }
        reread_rows = [
            row for page in source["evaluation_pages"]
            for row in page_context[(source["record_id"], int(page))]["reread"]
        ]
        reread_values = {row["value"] for row in reread_rows}
        baseline_visible = [value for value in references if value in baseline_values]
        reread_visible = [value for value in references if value in reread_values]
        combined_visible = [value for value in references if value in baseline_values | reread_values]
        documents.append({
            "record_id": source["record_id"], "reference_boundary_count": len(references),
            "baseline_visible": baseline_visible, "reread_visible": reread_visible,
            "combined_visible": combined_visible,
            "reread_numeric_candidate_count": len(reread_rows),
            "page_layout": [page_context[(source["record_id"], int(page))] | {"page": int(page)}
                            for page in source["evaluation_pages"]],
        })

    total = sum(row["reference_boundary_count"] for row in documents)
    baseline = sum(len(row["baseline_visible"]) for row in documents)
    reread = sum(len(row["reread_visible"]) for row in documents)
    combined = sum(len(row["combined_visible"]) for row in documents)
    report = {
        "analysis_scope": "development-only multiscale tiled OCR boundary-visibility experiment",
        "manifest_path": str(args.manifest), "manifest_sha256": file_sha256(args.manifest),
        "source_run_path": str(args.source_run), "document_count": len(documents),
        "page_count": sum(len(row["page_layout"]) for row in documents),
        "tile_count": len(tasks), "reference_boundary_count": total,
        "full_page_visibility": {"numerator": baseline, "denominator": total, "value": baseline / total},
        "tiled_reread_visibility": {"numerator": reread, "denominator": total, "value": reread / total},
        "combined_visibility": {"numerator": combined, "denominator": total, "value": combined / total},
        "combined_absolute_gain": combined - baseline,
        "combined_relative_recall_gain": (combined - baseline) / baseline if baseline else None,
        "reread_config": {
            "semantic_panel_inference": "long_page_layout_v001", "tile_height_px": 1800,
            "overlap_px": 180, "upscale": 2.0, "variants": ["gray", "otsu"], "psm": [6, 11],
        },
        "reference_blinding": "tiles and OCR frozen before reference visibility scoring",
        "documents": documents,
        "limitations": [
            "Visibility is necessary but not sufficient for correct column assignment or interval recovery.",
            "BGS v001 is development evidence and is excluded from the subsequent v002 external test.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
