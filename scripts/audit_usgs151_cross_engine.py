#!/usr/bin/env python3
"""Cross-engine audit of explicit USGS-151 lithology intervals.

RapidOCR is applied to frozen page rasters and compared with the earlier exact
Tesseract PSM-6/PSM-11 consensus. The output is an independently corroborated
machine transcription tier, not Human Ground Truth.
"""
from __future__ import annotations

import argparse, json, re, time
from pathlib import Path

from geologparser.ocr.rapidocr import DEFAULT_MODEL_DIR, MODEL_FILENAMES, RapidOCROnnxAdapter
from geologparser.result_index import file_sha256

LINE_RE = re.compile(
    r"LITHOLOGY:\s*(?P<lith>[A-Za-z]+)\s*"
    r"(?P<top>\d+(?:\.\d+)?)\s*(?:ft\s*)?[-–—]\s*"
    r"(?P<bottom>\d+(?:\.\d+)?)\s*(?:ft|fi|8)?\b",
    re.IGNORECASE,
)

def parse_region(text: str, *, page: int, confidence: float) -> dict | None:
    match = LINE_RE.search(text)
    if not match:
        return None
    top, bottom = float(match.group("top")), float(match.group("bottom"))
    if not (0 <= top < bottom <= 2000):
        return None
    return {
        "page": page,
        "lithology_raw": match.group("lith").title(),
        "lithology_normalized": match.group("lith").lower(),
        "top_depth_ft": top,
        "bottom_depth_ft": bottom,
        "rapidocr_confidence": float(confidence),
        "source_text": text,
    }

def key(row: dict) -> tuple:
    return (int(row["page"]), row["lithology_normalized"], float(row["top_depth_ft"]), float(row["bottom_depth_ft"]))

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=Path, required=True)
    ap.add_argument("--tesseract-consensus", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()
    pages = sorted(args.pages.glob("page-*.png"))
    if not pages:
        raise ValueError("no page rasters found")
    tesseract_rows = [json.loads(line) for line in args.tesseract_consensus.read_text(encoding="utf-8").splitlines() if line.strip()]
    tesseract_by_key = {key(row): row for row in tesseract_rows}
    adapter = RapidOCROnnxAdapter(intra_op_num_threads=args.threads)
    rapid_rows, region_rows = [], []
    started = time.perf_counter()
    for index, image in enumerate(pages, 1):
        page = int(re.search(r"(\d+)$", image.stem).group(1))
        regions = adapter.extract(image)
        for region in regions:
            region_rows.append({"page": page, "text": region.text, "confidence": region.confidence, "bbox": list(region.bbox)})
            parsed = parse_region(region.text, page=page, confidence=region.confidence or 0.0)
            if parsed is not None:
                rapid_rows.append(parsed)
        if index % 10 == 0 or index == len(pages):
            print(f"processed={index}/{len(pages)} rapid_intervals={len(rapid_rows)}", flush=True)
    rapid_by_key = {key(row): row for row in rapid_rows}
    shared = sorted(set(tesseract_by_key) & set(rapid_by_key))
    consensus = []
    for index, item in enumerate(shared, 1):
        consensus.append({
            "interval_id": f"USGS-151_CE_{index:03d}",
            "page": item[0], "lithology_normalized": item[1],
            "lithology_raw": tesseract_by_key[item]["lithology_raw"],
            "top_depth_ft": item[2], "bottom_depth_ft": item[3],
            "agreement_status": "tesseract_dual_layout_and_rapidocr_exact_agreement",
            "ground_truth_tier": "SOURCE_EXPLICIT_CROSS_ENGINE_CONSENSUS",
            "human_reviewed": False,
            "tesseract_evidence": tesseract_by_key[item],
            "rapidocr_evidence": rapid_by_key[item],
        })
    args.output_root.mkdir(parents=True, exist_ok=True)
    def write_jsonl(name: str, rows: list[dict]) -> None:
        (args.output_root / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    write_jsonl("rapidocr_regions.jsonl", region_rows)
    write_jsonl("rapidocr_intervals.jsonl", rapid_rows)
    write_jsonl("cross_engine_consensus_intervals.jsonl", consensus)
    model_hashes = {name: file_sha256(DEFAULT_MODEL_DIR / filename) for name, filename in MODEL_FILENAMES.items()}
    summary = {
        "scope": "USGS-151 explicit lithology cross-engine consensus audit",
        "ground_truth_tier": "SOURCE_EXPLICIT_CROSS_ENGINE_CONSENSUS",
        "human_reviewed": False,
        "eligible_for_human_gold_claims": False,
        "page_count": len(pages),
        "tesseract_dual_layout_consensus_count": len(tesseract_rows),
        "rapidocr_interval_count": len(rapid_rows),
        "exact_cross_engine_consensus_count": len(consensus),
        "tesseract_only_count": len(set(tesseract_by_key) - set(rapid_by_key)),
        "rapidocr_only_count": len(set(rapid_by_key) - set(tesseract_by_key)),
        "consensus_page_count": len({row["page"] for row in consensus}),
        "rapidocr_model_hashes": model_hashes,
        "page_raster_source": str(args.pages),
        "tesseract_consensus_sha256": file_sha256(args.tesseract_consensus),
        "wall_time_seconds": time.perf_counter() - started,
        "publication_use": "independently corroborated machine transcription candidate; requires source/rights and independent verification before formal Gold use",
    }
    (args.output_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))

if __name__ == "__main__":
    main()
