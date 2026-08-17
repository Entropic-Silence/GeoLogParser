#!/usr/bin/env python3
"""Export a pseudonymized, PDF-free input for the Paper II candidate ablation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz

from geologparser.paper2_sequence import start_path_score
from run_california_constraint_sequence import (
    as_predictions,
    hypotheses,
    load_regions,
    select_sequence,
    transition_score,
)


ROOT = Path(__file__).resolve().parents[1]
FREEZES = {
    "v004": {
        "manifest": ROOT / "datasets/manifests/california_wcr_gold_v004.jsonl",
        "raw": ROOT / "results/2026-08-15/P1_CALIFORNIA_WCR_V004_RAPIDOCR_PROSPECTIVE_FORMAL_001",
    },
    "v005": {
        "manifest": ROOT / "datasets/manifests/california_wcr_gold_v005.jsonl",
        "raw": ROOT / "results/2026-08-15/P1_CALIFORNIA_WCR_V005_RAPIDOCR_EXTERNAL_FORMAL_001",
    },
}


def load_jsonl(path: Path) -> dict[str, dict]:
    return {
        row["record_id"]: row
        for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    }


def page_dimensions(pdf_path: Path, page_number: int, dpi: int = 300) -> tuple[int, int]:
    with fitz.open(pdf_path) as document:
        rectangle = document[page_number - 1].rect
        return round(rectangle.width * dpi / 72), round(rectangle.height * dpi / 72)


def interval_key(row: dict) -> tuple[float, float]:
    return round(float(row["top_depth_m"]), 5), round(float(row["bottom_depth_m"]), 5)


def public_intervals(rows: list[dict]) -> list[dict]:
    return [{
        "top_depth_m": round(float(row["top_depth_m"]), 6),
        "bottom_depth_m": round(float(row["bottom_depth_m"]), 6),
        "thickness_m": round(float(row["thickness_m"]), 6),
    } for row in rows]


def export_freeze(freeze: str, paths: dict[str, Path], salt: str) -> list[dict]:
    manifest = load_jsonl(paths["manifest"])
    raw = load_jsonl(paths["raw"] / "predictions.jsonl")
    output = []
    for ordinal, record_id in enumerate(sorted(raw)):
        source = manifest[record_id]
        raw_row = raw[record_id]
        candidates = []
        with fitz.open(source["pdf_path"]) as document:
            for evidence in raw_row["evidence"]:
                page = int(evidence["page"])
                rectangle = document[page - 1].rect
                width, height = round(rectangle.width * 300 / 72), round(rectangle.height * 300 / 72)
                regions = load_regions(paths["raw"] / evidence["ocr_regions_path"])
                candidates.extend(hypotheses(regions, width, height, page))
        candidates = sorted(candidates, key=lambda item: (item["page"], item["y"], item["top"], item["bottom"]))
        selected = select_sequence(candidates)
        selected_keys = {
            (round(float(item["top"]), 3), round(float(item["bottom"]), 3), int(item["page"]), round(float(item["y"]), 3))
            for item in selected
        }
        record_key = "rec_" + hashlib.sha256(f"{salt}:{freeze}:{record_id}".encode()).hexdigest()[:20]
        public_candidates = []
        for index, item in enumerate(candidates):
            candidate_key = "cand_" + hashlib.sha256(f"{record_key}:{index}".encode()).hexdigest()[:20]
            geometry_key = (round(float(item["top"]), 3), round(float(item["bottom"]), 3), int(item["page"]), round(float(item["y"]), 3))
            public_candidates.append({
                "candidate_key": candidate_key,
                "page_order": int(item["page"]),
                "y_norm": round(float(item["y"]), 6),
                "x_top_norm": round(float(item["x_top"]), 6),
                "x_bottom_norm": round(float(item["x_bottom"]), 6),
                "top_ft": round(float(item["top"]), 6),
                "bottom_ft": round(float(item["bottom"]), 6),
                "top_depth_m": round(float(item["top"]) * 0.3048, 6),
                "bottom_depth_m": round(float(item["bottom"]) * 0.3048, 6),
                "ocr_confidence": round(float(item["confidence"]), 6),
                "geology_term": bool(item["node_score"] >= 2.0 + float(item["confidence"])),
                "raw_node_score": round(float(item["node_score"]), 6),
                "start_path_score": round(start_path_score(item), 6),
                "selected_complete_sequence": geometry_key in selected_keys,
            })
        raw_intervals = public_intervals(raw_row["predicted_intervals"])
        reference_intervals = public_intervals(raw_row["reference_intervals"])
        output.append({
            "record_key": record_key,
            "cohort": freeze,
            "cohort_ordinal": ordinal,
            "candidate_pool": public_candidates,
            "raw_intervals": raw_intervals,
            "reference_intervals": reference_intervals,
            "archived_complete_intervals": public_intervals(as_predictions(selected)),
        })
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper2/public/candidate_pool_v001.jsonl")
    parser.add_argument("--salt", default="paper2-candidate-pool-v001")
    args = parser.parse_args()
    rows = []
    for freeze, paths in FREEZES.items():
        rows.extend(export_freeze(freeze, paths, args.salt))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    metadata = {
        "schema_version": "paper2_candidate_pool_public_v001",
        "evidence_tier": "PUBLISHED_MANUAL_TRANSCRIPTION_GOLD",
        "source_status": "derived_from_frozen_v004_v005_candidate_pools",
        "record_count": len(rows),
        "candidate_count": sum(len(row["candidate_pool"]) for row in rows),
        "pseudonymization": ["stable salted record_key", "no source record ID", "no OCR text", "no absolute bbox", "no absolute path", "normalized page geometry"],
        "linkage_warning": "Ordered reference depth sequences may be unique and linkable to the public USGS transcription tables; this release is not anonymous.",
        "recomputation_scope": "candidate sequence ablation and boundary matching; no PDF or OCR rerun",
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
    }
    args.output.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
