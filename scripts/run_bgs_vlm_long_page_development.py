#!/usr/bin/env python3
"""Reference-blind Qwen3-VL rereading of BGS v001 long-page panel tiles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import tempfile
import time

from PIL import Image

from geologparser.layout import infer_log_panel_layout, long_page_tiles
from geologparser.ocr import TextRegion
from geologparser.vlm import Qwen3VLTransformersAdapter, parse_json_object


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = Path("/data/GeoLogParser/models/huggingface/Qwen3-VL-4B-Instruct")
MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_boundaries(text: str) -> list[dict]:
    try:
        payload = parse_json_object(text)
    except Exception:
        return []
    if not isinstance(payload, dict) or not isinstance(payload.get("boundaries"), list):
        return []
    output = []
    for item in payload["boundaries"]:
        if not isinstance(item, dict):
            continue
        try:
            value = float(item["depth_m"])
            bbox = [float(x) for x in item.get("relative_bbox", [])]
        except (KeyError, TypeError, ValueError):
            continue
        if not (0 <= value <= 5000) or len(bbox) != 4:
            continue
        output.append({
            "value_m": value,
            "relative_bbox": bbox,
            "evidence": str(item.get("evidence") or ""),
        })
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, default=ROOT / "prompts/bgs_long_page_boundary_v001.md")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=MODEL_PATH)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--min-pixels", type=int, default=128 * 28 * 28)
    parser.add_argument("--max-pixels", type=int, default=768 * 28 * 28)
    parser.add_argument("--target-height", type=int, default=2200)
    parser.add_argument("--overlap", type=int, default=260)
    args = parser.parse_args()
    prompt = args.prompt.read_text(encoding="utf-8")
    sources = load_jsonl(args.manifest)
    adapter = Qwen3VLTransformersAdapter(
        args.model_path, model_id=MODEL_ID, model_revision=MODEL_REVISION,
        max_new_tokens=args.max_new_tokens, min_pixels=args.min_pixels, max_pixels=args.max_pixels,
    )
    documents = []
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="geologparser_bgs_vlm_", dir="/data/GeoLogParser") as temp_dir:
        temp_root = Path(temp_dir)
        for source in sources:
            page_results = []
            for page in source["evaluation_pages"]:
                image_path = args.source_run / f"{source['record_id']}_page-{page}.png"
                region_path = args.source_run / f"{source['record_id']}_page-{page}_regions.jsonl"
                regions = [
                    TextRegion(int(page), tuple(row["bbox"]), row["text"], float(row.get("confidence") or 0), "frozen_full_page")
                    for row in load_jsonl(region_path)
                ]
                with Image.open(image_path) as image:
                    width, height = image.size
                    layout = infer_log_panel_layout(regions, width, height)
                    if layout is None:
                        page_results.append({"page": page, "layout_detected": False, "tiles": []})
                        continue
                    tiles = long_page_tiles(width, height, layout, target_height_px=args.target_height, overlap_px=args.overlap)
                    tile_results = []
                    for tile in tiles:
                        crop = image.crop(tile.bbox)
                        crop_path = temp_root / f"{source['record_id']}_{page}_{tile.tile_id}.png"
                        crop.save(crop_path)
                        try:
                            generation = adapter.generate([crop_path], prompt, prompt_version="bgs_long_page_boundary_v001")
                            parsed = parse_boundaries(generation.text)
                            tile_results.append({
                                "tile_id": tile.tile_id, "tile_bbox": list(tile.bbox),
                                "raw_text": generation.text, "parsed_boundaries": parsed,
                                "parse_status": "valid" if parsed or generation.text.strip().startswith("{") else "invalid",
                                "latency_seconds": generation.latency_seconds,
                                "peak_gpu_memory_bytes": generation.peak_gpu_memory_bytes,
                                "output_tokens": generation.output_tokens,
                                "generation_config": generation.generation_config,
                            })
                        except Exception as exc:
                            tile_results.append({
                                "tile_id": tile.tile_id, "tile_bbox": list(tile.bbox),
                                "raw_text": "", "parsed_boundaries": [],
                                "parse_status": "error", "error_type": type(exc).__name__, "error": str(exc),
                            })
                    page_results.append({
                        "page": page, "layout_detected": True,
                        "layout": {"x_min": layout.x_min, "x_max": layout.x_max, "y_min": layout.y_min, "y_max": layout.y_max},
                        "tiles": tile_results,
                    })
            documents.append({"record_id": source["record_id"], "pages": page_results})
    output = {
        "analysis_scope": "BGS v001 development-only reference-blind VLM long-page rereading; no official intervals consumed",
        "manifest_path": str(args.manifest), "source_run": str(args.source_run),
        "model_id": MODEL_ID, "model_revision": MODEL_REVISION,
        "prompt_path": str(args.prompt), "prompt_version": "bgs_long_page_boundary_v001",
        "tile_config": {"target_height": args.target_height, "overlap": args.overlap},
        "document_count": len(documents),
        "page_count": sum(len(d["pages"]) for d in documents),
        "tile_count": sum(len(p.get("tiles", [])) for d in documents for p in d["pages"]),
        "valid_tile_count": sum(1 for d in documents for p in d["pages"] for t in p.get("tiles", []) if t["parse_status"] == "valid"),
        "wall_time_seconds": time.perf_counter() - started,
        "documents": documents,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
