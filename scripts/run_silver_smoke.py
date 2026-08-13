#!/usr/bin/env python3
"""Run an isolated A/B OCR Silver smoke on frozen source images."""

from __future__ import annotations

import json
from pathlib import Path

from geologparser.pipeline import run_minimal_baseline
from geologparser.silver import build_silver_dataset


DATA_ROOT = Path("/data/GeoLogParser/datasets/synthetic_borehole_logs_v001")


def extractor(psm: int):
    def run(source):
        _, record = run_minimal_baseline(Path(source["image_path"]), ocr_language="eng", render_dpi=180)
        record["document"]["document_id"] = source["item_id"]
        return {"extractor_id": f"tesseract_psm_{psm}", "record": record}
    return run


def main() -> None:
    manifest = DATA_ROOT / "manifest.jsonl"
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line][:8]
    sources = [{"item_id": row["record_id"], "image_path": row["image_path"]} for row in rows]
    output = Path("/data/GeoLogParser/artifacts/silver/synthetic_ocr_ab_v001")
    summary = build_silver_dataset(sources, output, extractor(6), extractor(11), confidence_threshold=0.95)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
