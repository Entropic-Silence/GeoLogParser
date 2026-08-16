#!/usr/bin/env python3
"""Evaluate a NativeMM adapter on source-disjoint development samples."""

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


def extract_json(text: str):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except (ValueError, TypeError):
                return None
    return None


def greedy_points(predicted: list[float], expected: list[float], tolerance: float) -> tuple[int, int, int, list[float]]:
    remaining = set(range(len(expected)))
    tp = fp = 0
    errors = []
    for value in predicted:
        options = sorted((abs(value - expected[index]), index) for index in remaining)
        if options and options[0][0] <= tolerance:
            tp += 1
            errors.append(options[0][0])
            remaining.remove(options[0][1])
        else:
            fp += 1
    return tp, fp, len(remaining), errors


def prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "precision": precision, "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "true_positive": tp, "false_positive": fp, "false_negative": fn,
    }


def normalized_intervals(value: dict | None) -> tuple[list[float], list[tuple[float, float]]]:
    if not isinstance(value, dict):
        return [], []
    intervals = value.get("intervals")
    if not isinstance(intervals, list):
        return [], []
    output = []
    for row in intervals:
        try:
            top, bottom = float(row["top"]), float(row["bottom"])
        except (KeyError, TypeError, ValueError):
            continue
        unit = str(row.get("unit") or value.get("source_unit") or "m").lower()
        factor = 0.3048 if unit.startswith("ft") else 1.0
        output.append((top * factor, bottom * factor))
    boundaries = sorted({value for row in output for value in row})
    return boundaries, output


def metric_accumulator() -> dict:
    return {"tp": 0, "fp": 0, "fn": 0, "errors": []}


def add_points(accumulator: dict, predicted: list[float], expected: list[float], tolerance: float) -> None:
    tp, fp, fn, errors = greedy_points(predicted, expected, tolerance)
    accumulator["tp"] += tp
    accumulator["fp"] += fp
    accumulator["fn"] += fn
    accumulator["errors"].extend(errors)


def encode_prompt(processor, row: dict, device: str, max_pixels: int):
    image = Image.open(row["images"][0]).convert("RGB")
    prompt = row["messages"][0]["content"].replace("<image>\n", "", 1)
    messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
    image_processor = processor.image_processor
    min_pixels = getattr(image_processor, "min_pixels", None) or getattr(image_processor, "size", {}).get("shortest_edge", 112896)
    inputs = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt",
        images_kwargs={"size": {"shortest_edge": min_pixels, "longest_edge": max_pixels}},
    ).to(device)
    image.close()
    return inputs


def evaluate(args: argparse.Namespace) -> dict:
    from peft import PeftModel

    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.source_dataset:
        rows = [row for row in rows if row["source_dataset"] in set(args.source_dataset)]
    if args.task_family:
        rows = [row for row in rows if row["task_family"] in set(args.task_family)]
    random.Random(args.seed).shuffle(rows)
    if args.maximum_samples:
        rows = rows[:args.maximum_samples]
    processor = AutoProcessor.from_pretrained(args.model, trust_remote_code=False)
    base = AutoModelForImageTextToText.from_pretrained(args.model, trust_remote_code=False, dtype=torch.bfloat16).to(args.device)
    model = PeftModel.from_pretrained(base, args.adapter).to(args.device).eval()
    torch.cuda.set_device(args.device)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(args.device)
    boundary = metric_accumulator()
    interval_boundary = metric_accumulator()
    interval_pair = metric_accumulator()
    json_valid = 0
    predictions = []
    started = time.perf_counter()
    for row in rows:
        inputs = encode_prompt(processor, row, args.device, args.max_pixels)
        prompt_tokens = inputs["input_ids"].shape[-1]
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
        text = processor.batch_decode(generated[:, prompt_tokens:], skip_special_tokens=True)[0]
        parsed = extract_json(text)
        target = json.loads(row["messages"][1]["content"])
        json_valid += int(parsed is not None)
        if row["task_family"] == "boundary_grounding":
            predicted_y = []
            if isinstance(parsed, dict):
                for item in parsed.get("boundaries", []):
                    try: predicted_y.append(float(item["y"]))
                    except (KeyError, TypeError, ValueError): pass
            expected_y = [float(item["y"]) for item in target["boundaries"]]
            add_points(boundary, predicted_y, expected_y, args.y_tolerance)
        elif row["task_family"] == "interval_sequence":
            predicted_boundaries, predicted_intervals = normalized_intervals(parsed)
            expected_boundaries, expected_intervals = normalized_intervals(target)
            add_points(interval_boundary, predicted_boundaries, expected_boundaries, args.depth_tolerance_m)
            remaining = set(range(len(expected_intervals)))
            tp = fp = 0
            for top, bottom in predicted_intervals:
                options = [
                    index for index in remaining
                    if abs(top - expected_intervals[index][0]) <= args.depth_tolerance_m
                    and abs(bottom - expected_intervals[index][1]) <= args.depth_tolerance_m
                ]
                if options:
                    tp += 1; remaining.remove(options[0])
                else:
                    fp += 1
            interval_pair["tp"] += tp; interval_pair["fp"] += fp; interval_pair["fn"] += len(remaining)
        predictions.append({
            "sample_id": row["sample_id"], "source_dataset": row["source_dataset"],
            "task_family": row["task_family"], "output": text, "parsed": parsed,
        })
    torch.cuda.synchronize(args.device)
    elapsed = time.perf_counter() - started
    def finalize(accumulator: dict) -> dict:
        metrics = prf(accumulator["tp"], accumulator["fp"], accumulator["fn"])
        metrics["mae"] = sum(accumulator["errors"]) / len(accumulator["errors"]) if accumulator["errors"] else None
        return metrics
    metrics = {
        "experiment_id": args.experiment_id,
        "status": "completed",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], text=True, stdout=subprocess.PIPE, check=True).stdout.strip(),
        "model": str(args.model), "adapter": str(args.adapter),
        "dataset": str(args.dataset), "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "sample_count": len(rows), "json_valid_count": json_valid,
        "json_valid_rate": json_valid / len(rows) if rows else 0.0,
        "grounded_boundary_y": finalize(boundary),
        "sequence_boundary_at_0_05m": finalize(interval_boundary),
        "interval_at_0_05m": finalize(interval_pair),
        "critical_numerical_error_rate": interval_boundary["fp"] / (interval_boundary["tp"] + interval_boundary["fp"]) if interval_boundary["tp"] + interval_boundary["fp"] else None,
        "wall_time_seconds": elapsed,
        "seconds_per_sample": elapsed / len(rows) if rows else None,
        "peak_allocated_gib": torch.cuda.max_memory_allocated(args.device) / 1024 ** 3,
        "peak_reserved_gib": torch.cuda.max_memory_reserved(args.device) / 1024 ** 3,
        "selective_precision": "NOT_RUN",
        "selective_coverage": "NOT_RUN",
        "false_correction_rate": "NOT_RUN",
        "scope": "source-disjoint development; frozen external sources excluded",
    }
    args.output.mkdir(parents=True)
    (args.output / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in predictions), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--model", type=Path, default=Path("/data/GeoLogParser/models/huggingface/PaddleOCR-VL-1.6"))
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=Path("/data/GeoLogParser/datasets/paper2_nativemm_v001/development.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-dataset", action="append")
    parser.add_argument("--task-family", action="append")
    parser.add_argument("--maximum-samples", type=int)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--max-pixels", type=int, default=501760)
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--y-tolerance", type=float, default=0.015)
    parser.add_argument("--depth-tolerance-m", type=float, default=0.05)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    print(json.dumps(evaluate(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
