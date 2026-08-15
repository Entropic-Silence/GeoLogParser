#!/usr/bin/env python3
"""Development-only field-specific rereading of explicit depth columns."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time

import cv2
from PIL import Image

from geologparser.layout import infer_log_panel_layout
from geologparser.ocr import TextRegion
from geologparser.result_index import file_sha256


NUMBER = re.compile(r"^\s*([0-9]{1,4}(?:[.,][0-9]{1,3})?)\s*(?:m|metres?)?\s*$", re.I)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_number(text: str) -> float | None:
    match = NUMBER.fullmatch(text.replace("O", "0").replace("o", "0"))
    return float(match.group(1).replace(",", ".")) if match else None


def tesseract(image: Path, psm: int) -> list[dict]:
    completed = subprocess.run([
        "tesseract", str(image), "stdout", "-l", "eng", "--psm", str(psm),
        "-c", "tessedit_char_whitelist=0123456789.,m",
        "-c", "preserve_interword_spaces=1", "tsv",
    ], capture_output=True, text=True, check=False)
    if completed.returncode:
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
        value = parse_number(row.get("text", ""))
        if value is None:
            continue
        try:
            left, top = float(row["left"]), float(row["top"])
            width, height = float(row["width"]), float(row["height"])
            confidence = max(0.0, float(row["conf"]) / 100)
        except ValueError:
            continue
        output.append({
            "value": value, "text": row["text"], "confidence": confidence,
            "bbox": [left, top, left + width, top + height],
        })
    return output


def reread(task: dict) -> list[dict]:
    gray = cv2.imread(task["image"], cv2.IMREAD_GRAYSCALE)
    x1, y1, x2, y2 = task["bbox"]
    crop = gray[y1:y2, x1:x2]
    enlarged = cv2.resize(crop, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(enlarged)
    inverse = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    horizontal = cv2.morphologyEx(
        inverse, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (100, 1)),
    )
    vertical = cv2.morphologyEx(
        inverse, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 100)),
    )
    cleaned = 255 - cv2.subtract(inverse, cv2.max(horizontal, vertical))
    variants = {
        "gray4x": enlarged,
        "clahe4x": clahe,
        "otsu4x": cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        "line_removed4x": cleaned,
    }
    output = []
    with tempfile.TemporaryDirectory(prefix="geologparser-depth-roi-") as temporary:
        root = Path(temporary)
        for variant, pixels in variants.items():
            image_path = root / f"{variant}.png"
            cv2.imwrite(str(image_path), pixels)
            for psm in (6, 11, 12):
                for row in tesseract(image_path, psm):
                    bx1, by1, bx2, by2 = row["bbox"]
                    row["bbox"] = [
                        x1 + bx1 / 4, y1 + by1 / 4,
                        x1 + bx2 / 4, y1 + by2 / 4,
                    ]
                    row.update({
                        "page": task["page"], "tile_id": task["tile_id"],
                        "variant": variant, "psm": psm,
                        "field_role": task["field_role"],
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
    started = time.perf_counter()
    sources = load_jsonl(args.manifest)
    tasks = []
    contexts = {}
    for source in sources:
        for page in source["evaluation_pages"]:
            image_path = args.source_run / f"{source['record_id']}_page-{page}.png"
            region_path = args.source_run / f"{source['record_id']}_page-{page}_regions.jsonl"
            rows = load_jsonl(region_path)
            with Image.open(image_path) as opened:
                width, height = opened.size
            regions = [
                TextRegion(int(page), tuple(row["bbox"]), row["text"], float(row.get("confidence") or 0), "full_page")
                for row in rows
            ]
            layout = infer_log_panel_layout(regions, width, height)
            key = (source["record_id"], int(page))
            contexts[key] = {"rows": [], "layout_detected": layout is not None, "tile_count": 0, "targets": []}
            if layout is None:
                continue
            anchors = layout.anchors
            numeric_centers = []
            right_limit = (
                anchors["description"].center_x + 0.02 if "description" in anchors
                else anchors["lithology"].center_x + 0.20 if "lithology" in anchors
                else layout.x_max
            )
            for row in rows:
                value = parse_number(str(row.get("text") or ""))
                if value is None:
                    continue
                x = (row["bbox"][0] + row["bbox"][2]) / 2 / width
                y = (row["bbox"][1] + row["bbox"][3]) / 2 / height
                if layout.y_min <= y <= layout.y_max and layout.x_min - 0.12 <= x <= right_limit:
                    numeric_centers.append((x, y, value))
            bins = {}
            for x, y, value in numeric_centers:
                bins.setdefault(round(x / 0.025), []).append((x, y, value))
            boundary_x = None
            if bins:
                _, values = max(
                    bins.items(),
                    key=lambda item: (
                        len({round(value[1], 3) for value in item[1]}),
                        len({round(value[2], 3) for value in item[1]}),
                        sum(value[0] for value in item[1]) / len(item[1]),
                    ),
                )
                boundary_x = sum(value[0] for value in values) / len(values)
            elif "description" in anchors:
                boundary_x = anchors["description"].center_x - 0.04
            scale_x = None
            if "depth" in anchors:
                scale_x = anchors["depth"].center_x
            elif "lithology" in anchors:
                scale_x = max(0.03, anchors["lithology"].center_x - 0.22)
            elif "description" in anchors:
                scale_x = max(0.03, anchors["description"].center_x - 0.20)
            targets = []
            if boundary_x is not None:
                targets.append(("boundary_depth", boundary_x))
            if scale_x is not None and all(abs(scale_x - center) > 0.055 for _, center in targets):
                targets.append(("scale_depth", scale_x))
            contexts[key]["targets"] = [
                {"field_role": role, "center_x_normalized": center} for role, center in targets
            ]
            for field_role, center_x in targets:
                # Narrow crops prevent unrelated sample/metadata numbers from
                # dominating OCR while retaining decimal points and units.
                x1 = max(0, int((center_x - 0.04) * width))
                x2 = min(width, int((center_x + 0.04) * width))
                start = max(0, int(layout.y_min * height))
                end = min(height, int(layout.y_max * height))
                tile_height = 1200
                overlap = 120
                index = 0
                while start < end:
                    tile_end = min(end, start + tile_height)
                    tasks.append({
                        "record_id": source["record_id"], "page": int(page),
                        "image": str(image_path), "bbox": (x1, start, x2, tile_end),
                        "tile_id": f"{field_role}_{index:03d}", "field_role": field_role,
                    })
                    contexts[key]["tile_count"] += 1
                    if tile_end == end:
                        break
                    start += tile_height - overlap
                    index += 1
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        for task, rows in zip(tasks, executor.map(reread, tasks)):
            contexts[(task["record_id"], task["page"])]["rows"].extend(rows)

    documents = []
    for source in sources:
        references = sorted(
            {float(row["top_depth_m"]) for row in source["intervals"]}
            | {float(row["bottom_depth_m"]) for row in source["intervals"]}
        )
        rows = [
            row for page in source["evaluation_pages"]
            for row in contexts[(source["record_id"], int(page))]["rows"]
        ]
        values = {row["value"] for row in rows}
        visible = [value for value in references if value in values]
        documents.append({
            "record_id": source["record_id"], "reference_boundary_count": len(references),
            "visible_boundaries": visible, "candidate_count": len(rows),
            "pages": [
                {"page": int(page), **contexts[(source["record_id"], int(page))]}
                for page in source["evaluation_pages"]
            ],
        })
    total = sum(row["reference_boundary_count"] for row in documents)
    visible = sum(len(row["visible_boundaries"]) for row in documents)
    report = {
        "analysis_scope": "development-only field-specific narrow-ROI depth rereading",
        "manifest_path": str(args.manifest), "manifest_sha256": file_sha256(args.manifest),
        "source_run": str(args.source_run), "document_count": len(documents),
        "page_count": sum(len(row["pages"]) for row in documents), "tile_count": len(tasks),
        "reference_boundary_count": total,
        "field_roi_visibility": {"numerator": visible, "denominator": total, "value": visible / total},
        "candidate_count": sum(row["candidate_count"] for row in documents),
        "wall_time_seconds": time.perf_counter() - started,
        "config": {
            "field_role": "boundary_depth", "x_half_width_normalized": 0.035,
            "tile_height_px": 1200, "overlap_px": 120, "upscale": 4,
            "variants": ["gray4x", "clahe4x", "otsu4x", "line_removed4x"], "psm": [6, 11, 12],
            "character_whitelist": "0123456789.,m",
        },
        "reference_blinding": "semantic field crops and OCR were completed before exact reference visibility scoring",
        "documents": documents,
        "limitations": [
            "Exact numeric visibility is not interval accuracy or correct column assignment.",
            "BGS v001 is a development source and cannot confirm unseen-source generalization.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
