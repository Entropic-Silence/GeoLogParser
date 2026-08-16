#!/usr/bin/env python3
"""Evaluate NativeMM structural tasks as one image-level bundle.

Boundary grounding and depth-scale predictions are generated independently,
then handed to the deterministic geometry decoder.  This avoids treating a
generative depth value as evidence and provides the Paper II structural
coverage and geometry metrics in one artifact.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time

from PIL import Image
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor

from geologparser.nativemm.geometry import decode_depth_geometry
try:
    from scripts.nativemm.evaluate_adapter import extract_json, greedy_points, prf
except ModuleNotFoundError:  # direct execution from scripts/nativemm
    from evaluate_adapter import extract_json, greedy_points, prf


def _groups(path: Path, source_dataset: list[str] | None, maximum: int | None, seed: int) -> list[list[dict]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if source_dataset:
        allowed = set(source_dataset)
        rows = [row for row in rows if row["source_dataset"] in allowed]
    by_image: dict[str, list[dict]] = {}
    for row in rows:
        by_image.setdefault(row["images"][0], []).append(row)
    bundles = list(by_image.values())
    random.Random(seed).shuffle(bundles)
    return bundles[:maximum] if maximum else bundles


def _encode(processor, row: dict, device: str, max_pixels: int):
    image = Image.open(row["images"][0]).convert("RGB")
    prompt = row["messages"][0]["content"].replace("<image>\n", "", 1)
    messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
    image_processor = processor.image_processor
    minimum = getattr(image_processor, "min_pixels", None) or getattr(image_processor, "size", {}).get("shortest_edge", 112896)
    inputs = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt",
        images_kwargs={"size": {"shortest_edge": minimum, "longest_edge": max_pixels}},
    ).to(device)
    image.close()
    return inputs


def _as_points(parsed: dict | None, key: str, value_key: str) -> list[float]:
    if not isinstance(parsed, dict) or not isinstance(parsed.get(key), list):
        return []
    values = []
    for item in parsed[key]:
        try:
            values.append(float(item[value_key]))
        except (KeyError, TypeError, ValueError):
            continue
    return values


def evaluate(args: argparse.Namespace) -> dict:
    from peft import PeftModel

    bundles = _groups(args.dataset, args.source_dataset, args.maximum_bundles, args.seed)
    processor = AutoProcessor.from_pretrained(args.model, trust_remote_code=False)
    base = AutoModelForImageTextToText.from_pretrained(args.model, trust_remote_code=False, dtype=torch.bfloat16).to(args.device)
    model = PeftModel.from_pretrained(base, args.adapter).to(args.device).eval()
    torch.cuda.set_device(args.device)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(args.device)
    boundary_tp = boundary_fp = boundary_fn = 0
    decoded_tp = decoded_fp = decoded_fn = 0
    json_valid = 0
    task_counts: dict[str, int] = {}
    predictions = []
    started = time.perf_counter()
    for bundle in bundles:
        by_task = {row["task_family"]: row for row in bundle}
        bundle_out = {"image": bundle[0]["images"][0], "sample_id": bundle[0]["sample_id"], "tasks": {}}
        parsed_by_task: dict[str, dict | None] = {}
        for task in args.task_family:
            row = by_task.get(task)
            if row is None:
                continue
            inputs = _encode(processor, row, args.device, args.max_pixels)
            prompt_tokens = inputs["input_ids"].shape[-1]
            with torch.inference_mode():
                generated = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
            text = processor.batch_decode(generated[:, prompt_tokens:], skip_special_tokens=True)[0]
            parsed = extract_json(text)
            parsed_by_task[task] = parsed
            task_counts[task] = task_counts.get(task, 0) + 1
            json_valid += int(parsed is not None)
            bundle_out["tasks"][task] = {"text": text, "parsed": parsed}
        boundary_row = by_task.get("boundary_grounding")
        boundary_pred = _as_points(parsed_by_task.get("boundary_grounding"), "boundaries", "y")
        if boundary_row:
            target = json.loads(boundary_row["messages"][1]["content"])
            boundary_ref = [float(item["y"]) for item in target.get("boundaries", [])]
            tp, fp, fn, _ = greedy_points(boundary_pred, boundary_ref, args.y_tolerance)
            boundary_tp += tp; boundary_fp += fp; boundary_fn += fn
        scale_pred = _as_points(parsed_by_task.get("depth_scale"), "scale_points", "y")
        scale_parsed = parsed_by_task.get("depth_scale")
        scale_points = []
        if isinstance(scale_parsed, dict):
            for item in scale_parsed.get("scale_points", []):
                try:
                    scale_points.append((float(item["y"]), float(item["depth"])))
                except (KeyError, TypeError, ValueError):
                    continue
        if boundary_row and scale_points and boundary_pred:
            target = json.loads(boundary_row["messages"][1]["content"])
            ref_depths = [float(item["depth"]) for item in target.get("boundaries", [])]
            decoded = decode_depth_geometry(boundary_pred, scale_points, residual_tolerance_m=args.scale_tolerance)
            tp, fp, fn, _ = greedy_points(list(decoded.boundaries_m), ref_depths, args.depth_tolerance_m)
            decoded_tp += tp; decoded_fp += fp; decoded_fn += fn
            bundle_out["geometry"] = {
                "decoded_depths_m": list(decoded.boundaries_m),
                "scale_rmse_m": decoded.scale_rmse_m,
                "scale_inliers": decoded.scale_inliers,
                "warnings": list(decoded.warnings),
            }
        predictions.append(bundle_out)
    torch.cuda.synchronize(args.device)
    elapsed = time.perf_counter() - started
    boundary = prf(boundary_tp, boundary_fp, boundary_fn)
    decoded = prf(decoded_tp, decoded_fp, decoded_fn)
    metrics = {
        "experiment_id": args.experiment_id,
        "status": "completed",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], text=True, stdout=subprocess.PIPE, check=True).stdout.strip(),
        "model": str(args.model), "adapter": str(args.adapter),
        "dataset": str(args.dataset), "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "bundle_count": len(bundles), "task_counts": task_counts,
        "json_valid_rate": json_valid / sum(task_counts.values()) if task_counts else 0.0,
        "direct_boundary_y": boundary,
        "geometry_decoded_depth": decoded,
        "structural_evidence_coverage": boundary["recall"],
        "critical_numerical_error_rate": decoded_fp / (decoded_tp + decoded_fp) if decoded_tp + decoded_fp else None,
        "wall_time_seconds": elapsed,
        "seconds_per_bundle": elapsed / len(bundles) if bundles else None,
        "peak_allocated_gib": torch.cuda.max_memory_allocated(args.device) / 1024 ** 3,
        "peak_reserved_gib": torch.cuda.max_memory_reserved(args.device) / 1024 ** 3,
        "scope": "development only; frozen external sources excluded",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in predictions), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--model", type=Path, default=Path("/data/GeoLogParser/models/huggingface/PaddleOCR-VL-1.6"))
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-dataset", action="append")
    parser.add_argument("--task-family", action="append", default=["boundary_grounding", "depth_scale"])
    parser.add_argument("--maximum-bundles", type=int)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--max-pixels", type=int, default=501760)
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--y-tolerance", type=float, default=0.015)
    parser.add_argument("--depth-tolerance-m", type=float, default=0.05)
    parser.add_argument("--scale-tolerance", type=float, default=0.10)
    parser.add_argument("--device", default="cuda:0")
    print(json.dumps(evaluate(parser.parse_args()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
