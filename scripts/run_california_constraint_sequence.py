#!/usr/bin/env python3
"""Constraint-guided interval-sequence recovery on frozen California OCR artifacts."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import math
import platform
import re
import resource
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest

from run_california_wcr_interval_benchmark import (
    FT_TO_M, GEOLOGY_TERMS, PAIR_NUMBER, Region, anchor, normalize_lithology,
    parse_number, reference_intervals, render_pdf,
)


ROOT = Path(__file__).resolve().parents[1]
FORM_MARKERS = re.compile(
    r"(?:address|permit|latitude|longitude|diameter|casing|annular|screen|blank|pvc|steel|cement|grout|attachments|certification|license|total depth|water level|date measured|estimated yield)",
    re.I,
)


def load_regions(path: Path) -> list[Region]:
    return [
        Region(row["text"], float(row["confidence"]), tuple(float(value) for value in row["bbox"]))
        for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    ]


def hypotheses(regions: list[Region], width: int, height: int, page: int) -> list[dict]:
    page_anchor = anchor(regions, width, height)
    if page_anchor is not None:
        anchor_x, anchor_y = page_anchor
        if anchor_x < 0.45:
            x_min, x_max = 0.015, 0.49
        else:
            x_min, x_max = 0.45, 0.995
        y_min = max(0.08, anchor_y + 0.005)
    else:
        x_min, x_max, y_min = 0.03, 0.90, 0.15
    usable = [
        item for item in regions
        if x_min <= item.center_x / width <= x_max and y_min <= item.center_y / height <= 0.90
    ]
    numeric = [(item, parse_number(item.text)) for item in usable]
    numeric = [(item, value) for item, value in numeric if value is not None]
    raw: list[dict] = []

    for item in usable:
        match = PAIR_NUMBER.fullmatch(item.text)
        if not match:
            continue
        top, bottom = float(match.group(1).replace(",", ".")), float(match.group(2).replace(",", "."))
        if 0 <= top < bottom <= 5000:
            raw.append({
                "top": top, "bottom": bottom, "page": page, "y": item.center_y / height,
                "x_top": item.bbox[0] / width, "x_bottom": item.center_x / width,
                "description_x": item.bbox[2] / width, "seed": match.group(3).strip(" |_:;.,"),
                "confidence": item.confidence, "evidence": [item], "anchor": page_anchor,
            })

    for left, top in numeric:
        matches = [
            (right, bottom) for right, bottom in numeric
            if right.center_x > left.center_x
            and 0.012 * width <= right.center_x - left.center_x <= 0.14 * width
            and abs(right.center_y - left.center_y) <= max(8.0, 0.50 * max(left.height, right.height))
            and top < bottom <= 5000
        ]
        if not matches:
            continue
        right, bottom = min(matches, key=lambda pair: pair[0].center_x)
        raw.append({
            "top": top, "bottom": bottom, "page": page,
            "y": (left.center_y + right.center_y) / (2 * height),
            "x_top": left.bbox[0] / width, "x_bottom": right.bbox[0] / width,
            "description_x": right.bbox[2] / width, "seed": "",
            "confidence": min(left.confidence, right.confidence), "evidence": [left, right], "anchor": page_anchor,
        })

    unique: dict[tuple, dict] = {}
    for item in raw:
        key = (round(item["top"], 3), round(item["bottom"], 3), item["page"], round(item["y"], 3))
        if key not in unique or item["confidence"] > unique[key]["confidence"]:
            unique[key] = item
    output = []
    cutoff = x_max * width
    for item in unique.values():
        center = item["y"] * height
        description_regions = [
            region for region in usable
            if region.bbox[0] >= item["description_x"] * width - 5
            and region.bbox[0] <= cutoff
            and abs(region.center_y - center) <= max(8.0, 0.55 * region.height)
            and re.search(r"[A-Za-z]", region.text)
            and region not in item["evidence"]
        ]
        description_regions.sort(key=lambda region: region.bbox[0])
        description = " ".join([item["seed"], *(region.text for region in description_regions)]).strip()
        description = re.sub(r"\s+", " ", description).strip(" |_:;.,-")
        if not description or not re.search(r"[A-Za-z]", description):
            continue
        if FORM_MARKERS.search(description) and not GEOLOGY_TERMS.search(description):
            continue
        item["description"] = description
        item["evidence"] = [*item["evidence"], *description_regions]
        item["node_score"] = (
            1.0 + item["confidence"]
            + (1.0 if GEOLOGY_TERMS.search(description) else 0.0)
        )
        output.append(item)
    return output


def transition_score(left: dict, right: dict) -> float | None:
    if (right["page"], right["y"]) <= (left["page"], left["y"]):
        return None
    if right["top"] < left["top"]:
        return None
    overlap = left["bottom"] - right["top"]
    if overlap > 1.0:
        return None
    gap = abs(left["bottom"] - right["top"])
    if gap <= 0.05:
        continuity = 5.0
    elif gap <= 1.0:
        continuity = 2.0 - gap
    else:
        continuity = -min(6.0, math.log1p(gap))
    column_penalty = 4.0 * (abs(left["x_top"] - right["x_top"]) + abs(left["x_bottom"] - right["x_bottom"]))
    page_penalty = 0.15 * max(0, right["page"] - left["page"] - 1)
    return continuity - column_penalty - page_penalty


def select_sequence(candidates: list[dict]) -> list[dict]:
    ordered = sorted(candidates, key=lambda item: (item["page"], item["y"], item["top"], item["bottom"]))
    if not ordered:
        return []
    scores = [item["node_score"] - 0.0005 * item["top"] for item in ordered]
    parents: list[int | None] = [None] * len(ordered)
    lengths = [1] * len(ordered)
    for right_index, right in enumerate(ordered):
        for left_index in range(max(0, right_index - 400), right_index):
            edge = transition_score(ordered[left_index], right)
            if edge is None:
                continue
            candidate_score = scores[left_index] + right["node_score"] + edge
            candidate_length = lengths[left_index] + 1
            if candidate_score > scores[right_index] or (
                abs(candidate_score - scores[right_index]) < 1e-9 and candidate_length > lengths[right_index]
            ):
                scores[right_index] = candidate_score
                parents[right_index] = left_index
                lengths[right_index] = candidate_length
    end = max(range(len(ordered)), key=lambda index: (scores[index], lengths[index]))
    path = []
    while end is not None:
        path.append(ordered[end])
        end = parents[end]
    return list(reversed(path))


def as_predictions(sequence: list[dict]) -> list[dict]:
    output, seen = [], set()
    for item in sequence:
        key = (round(item["top"], 4), round(item["bottom"], 4))
        if key in seen:
            continue
        seen.add(key)
        output.append({
            "top_depth_m": item["top"] * FT_TO_M,
            "bottom_depth_m": item["bottom"] * FT_TO_M,
            "thickness_m": (item["bottom"] - item["top"]) * FT_TO_M,
            "lithology_raw": item["description"],
            "lithology_normalized": normalize_lithology(item["description"]),
            "source_page": item["page"],
            "source_unit": "ft_bls",
            "evidence": {
                "backend": "rapidocr_frozen_regions_constraint_sequence_v001",
                "node_score": item["node_score"],
                "regions": [
                    {"text": region.text, "confidence": region.confidence, "bbox": list(region.bbox)}
                    for region in item["evidence"]
                ],
            },
        })
    return output


def boundary_set(rows: list[dict]) -> set[tuple[float, float]]:
    return {(round(row["top_depth_m"], 5), round(row["bottom_depth_m"], 5)) for row in rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--raw-run", type=Path, required=True)
    parser.add_argument("--partition", choices=("development", "test"), required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "datasets/manifests/california_wcr_gold_v001.jsonl")
    parser.add_argument("--split", type=Path, default=ROOT / "datasets/splits/california_wcr_gold_split_v001.json")
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    split = json.loads(args.split.read_text(encoding="utf-8"))
    ids = set(split[args.partition])
    manifest = {
        row["record_id"]: row
        for row in (json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip())
        if row["record_id"] in ids
    }
    raw_rows = {
        row["record_id"]: row
        for row in (json.loads(line) for line in (args.raw_run / "predictions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    }
    if set(manifest) != ids or set(raw_rows) != ids:
        raise ValueError("raw run, manifest, and split do not align")
    raw_run = json.loads((args.raw_run / "run.json").read_text(encoding="utf-8"))
    if raw_run["config"].get("prediction_reference_conditioning") != "none":
        raise ValueError("raw run is reference-conditioned")

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": "california_wcr_gold_v001",
        "split_version": split["split_version"] + f"_{args.partition}",
        "model": "rapidocr_constraint_guided_sequence_ranker_v001",
        "model_revision": "deterministic_dynamic_programming_v001",
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "ground_truth_sha256": file_sha256(args.manifest),
            "split_sha256": file_sha256(args.split),
            "partition": args.partition,
            "prediction_reference_conditioning": "none",
            "reference_blinded_decision_policy": True,
            "raw_run_id": raw_run["experiment_id"],
            "raw_artifact_manifest_sha256": file_sha256(args.raw_run / "artifact_manifest.json"),
            "candidate_source": "frozen RapidOCR positioned regions",
            "constraint": "depth monotonicity plus adjacent boundary continuity plus layout-column stability",
            "reference_doi": "10.5066/P9M85U0T",
        },
        "started_utc": started.isoformat(),
    })
    wall_started = time.perf_counter()
    refs_all, raw_all, constrained_all = [], [], []
    output_rows, errors = [], []
    correction_totals = {key: 0 for key in [
        "raw_correct_kept", "raw_correct_removed", "raw_incorrect_removed",
        "constrained_correct_added", "constrained_incorrect_added",
    ]}
    for index, record_id in enumerate(sorted(ids), start=1):
        source = manifest[record_id]
        raw = raw_rows[record_id]
        references = reference_intervals(source)
        candidates = []
        with tempfile.TemporaryDirectory(prefix="geologparser-california-constraint-") as temporary:
            rendered = dict(render_pdf(Path(source["pdf_path"]), Path(temporary), 300))
            for evidence in raw["evidence"]:
                page = int(evidence["page"])
                regions = load_regions(args.raw_run / evidence["ocr_regions_path"])
                with Image.open(rendered[page]) as image:
                    width, height = image.size
                candidates.extend(hypotheses(regions, width, height, page))
        sequence = select_sequence(candidates)
        constrained = as_predictions(sequence)
        raw_predictions = raw["predicted_intervals"]
        reference_boundaries = boundary_set(references)
        raw_boundaries = boundary_set(raw_predictions)
        constrained_boundaries = boundary_set(constrained)
        raw_correct = raw_boundaries & reference_boundaries
        raw_incorrect = raw_boundaries - reference_boundaries
        constrained_correct = constrained_boundaries & reference_boundaries
        constrained_incorrect = constrained_boundaries - reference_boundaries
        taxonomy = {
            "raw_correct_kept": len(raw_correct & constrained_boundaries),
            "raw_correct_removed": len(raw_correct - constrained_boundaries),
            "raw_incorrect_removed": len(raw_incorrect - constrained_boundaries),
            "constrained_correct_added": len(constrained_correct - raw_boundaries),
            "constrained_incorrect_added": len(constrained_incorrect - raw_boundaries),
        }
        for key, value in taxonomy.items():
            correction_totals[key] += value
        raw_matches, _, _ = match_intervals_by_boundaries(references, raw_predictions, tolerance_m=0.05)
        constrained_matches, missing, extra = match_intervals_by_boundaries(references, constrained, tolerance_m=0.05)
        refs_all.append(references)
        raw_all.append(raw_predictions)
        constrained_all.append(constrained)
        output_rows.append({
            "record_id": record_id,
            "county": source["county"],
            "reference_intervals": references,
            "raw_predictions": raw_predictions,
            "candidate_count": len(candidates),
            "constrained_predictions": constrained,
            "raw_match_count": len(raw_matches),
            "constrained_match_count": len(constrained_matches),
            "correction_taxonomy": taxonomy,
            "unmatched_reference_indices": missing,
            "unmatched_constrained_indices": extra,
        })
        errors.extend({"record_id": record_id, "error_type": "missing_interval_after_constraint", "reference_index": value} for value in missing)
        errors.extend({"record_id": record_id, "error_type": "spurious_interval_after_constraint", "prediction_index": value} for value in extra)
        print(f"[{index}/{len(ids)}] {record_id} candidates={len(candidates)} raw={len(raw_predictions)} constrained={len(constrained)} raw_match={len(raw_matches)} constrained_match={len(constrained_matches)}")

    raw_metrics = boundary_matched_interval_metrics(refs_all, raw_all, tolerance_m=0.05)
    constrained_metrics = boundary_matched_interval_metrics(refs_all, constrained_all, tolerance_m=0.05)
    actions = sum(correction_totals[key] for key in ["raw_correct_removed", "raw_incorrect_removed", "constrained_correct_added", "constrained_incorrect_added"])
    harmful = correction_totals["raw_correct_removed"] + correction_totals["constrained_incorrect_added"]
    metrics = {
        "scope": "human-GT benchmark evaluation",
        "comparison": "single_pass_vs_constraint_guided_sequence_recovery",
        "reference_ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION",
        "prediction_reference_conditioning": "none",
        "reference_blinded_decision_policy": True,
        "partition": args.partition,
        "document_count": len(ids),
        "county_count": len({row["county"] for row in manifest.values()}),
        "reference_interval_count": sum(len(rows) for rows in refs_all),
        "raw_prediction_count": sum(len(rows) for rows in raw_all),
        "constrained_prediction_count": sum(len(rows) for rows in constrained_all),
        "candidate_count": sum(row["candidate_count"] for row in output_rows),
        "raw_interval_metrics": {name: value.to_dict() for name, value in raw_metrics.items()},
        "constrained_interval_metrics": {name: value.to_dict() for name, value in constrained_metrics.items()},
        "correction_taxonomy": correction_totals,
        "automatic_correction_actions": actions,
        "harmful_correction_actions": harmful,
        "false_correction_rate": {
            "value": harmful / actions if actions else None,
            "numerator": harmful,
            "denominator": actions,
            "definition": "(removed correct raw boundaries + added incorrect constrained boundaries) / all added or removed boundaries",
        },
        "wall_time_seconds": time.perf_counter() - wall_started,
        "latency_seconds_per_document_wall": (time.perf_counter() - wall_started) / len(ids),
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (run / "predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in errors), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(
        f"started_utc={started.isoformat()}\npartition={args.partition}\ndocuments={len(ids)}\nraw_run={raw_run['experiment_id']}\nstatus=completed\n",
        encoding="utf-8",
    )
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
