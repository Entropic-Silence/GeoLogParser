#!/usr/bin/env python3
"""Train/evaluate a discriminative NativeMM structural boundary head."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time

import numpy as np
from PIL import Image
import torch
from torch.nn import functional as F
from transformers import AutoModelForImageTextToText, AutoProcessor

from geologparser.nativemm.dense_boundary import (
    DenseBoundaryHead,
    boundary_loss,
    extract_peaks,
    gaussian_targets,
)


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, text=True, stdout=subprocess.PIPE,
    ).stdout.strip()


def pixel_row_features(image: Image.Image, bins: int) -> torch.Tensor:
    gray = np.asarray(image.convert("L"), dtype=np.float32) / 255.0
    darkness = 1.0 - gray
    bands = np.array_split(darkness, 8, axis=1)
    features = [band.mean(axis=1) for band in bands]
    features.extend([darkness.mean(axis=1), darkness.std(axis=1), darkness.max(axis=1)])
    base = np.stack(features, axis=0)
    gradient = np.abs(np.diff(base, axis=1, prepend=base[:, :1]))
    value = torch.from_numpy(np.concatenate([base, gradient], axis=0)).unsqueeze(0)
    return F.interpolate(value, size=bins, mode="linear", align_corners=False).squeeze(0)


def cache_key(row: dict, model_revision: str, bins: int) -> str:
    payload = f"{row['sample_id']}|{row['image']}|{model_revision}|{bins}".encode()
    return hashlib.sha256(payload).hexdigest()


def load_or_extract(
    row: dict,
    *,
    processor,
    backbone,
    cache_root: Path,
    model_revision: str,
    bins: int,
    device: str,
) -> dict[str, torch.Tensor]:
    path = cache_root / f"{cache_key(row, model_revision, bins)}.pt"
    if path.exists():
        return torch.load(path, map_location="cpu", weights_only=True)
    image = Image.open(row["image"]).convert("RGB")
    inputs = processor.image_processor(images=image, return_tensors="pt")
    with torch.inference_mode():
        output = backbone.get_image_features(
            inputs["pixel_values"].to(device),
            image_grid_thw=inputs["image_grid_thw"].to(device),
        )
    grid = inputs["image_grid_thw"][0].tolist()
    height, width = int(grid[1] // 2), int(grid[2] // 2)
    projected = output.pooler_output.detach().float().cpu().reshape(height, width, -1)
    visual = projected.mean(dim=1).transpose(0, 1).unsqueeze(0)
    visual = F.interpolate(visual, size=bins, mode="linear", align_corners=False).squeeze(0)
    pixels = pixel_row_features(image, bins)
    image.close()
    value = {"visual": visual.to(torch.float16), "pixels": pixels.to(torch.float16)}
    cache_root.mkdir(parents=True, exist_ok=True)
    torch.save(value, path)
    return value


def match_points(predicted: list[float], expected: list[float], tolerance: float) -> tuple[int, int, int, list[float]]:
    remaining = set(range(len(expected)))
    errors: list[float] = []
    true_positive = false_positive = 0
    for value in predicted:
        options = sorted((abs(value - expected[index]), index) for index in remaining)
        if options and options[0][0] <= tolerance:
            true_positive += 1
            errors.append(options[0][0])
            remaining.remove(options[0][1])
        else:
            false_positive += 1
    return true_positive, false_positive, len(remaining), errors


def prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
    }


def infer_rows(model, rows: list[dict], features: dict[str, dict[str, torch.Tensor]], device: str) -> list[dict]:
    model.eval()
    output = []
    with torch.inference_mode():
        for row in rows:
            feature = features[row["sample_id"]]
            logits = model(
                feature["visual"].unsqueeze(0).to(device, dtype=torch.float32),
                feature["pixels"].unsqueeze(0).to(device, dtype=torch.float32),
            )[0]
            output.append({"row": row, "probabilities": torch.sigmoid(logits).cpu()})
    return output


def depth_predictions(item: dict, threshold: float, minimum_separation_bins: int) -> list[tuple[float, float, float]]:
    row = item["row"]
    geometry = row["geometry"]
    slope = geometry.get("depth_per_pixel")
    intercept = geometry.get("intercept_m")
    if slope is None or intercept is None:
        return []
    x1, y1, x2, y2 = geometry["crop_bbox_page"]
    output = []
    for normalized_y, confidence in extract_peaks(
        item["probabilities"], threshold=threshold,
        minimum_separation_bins=minimum_separation_bins,
    ):
        page_y = y1 + normalized_y * (y2 - y1)
        output.append((float(slope) * page_y + float(intercept), normalized_y, confidence))
    return output


def score(inferences: list[dict], threshold: float, minimum_separation_bins: int, tolerance_m: float) -> dict:
    boundary = {"tp": 0, "fp": 0, "fn": 0, "errors": []}
    interval = {"tp": 0, "fp": 0, "fn": 0}
    predictions = []
    for item in inferences:
        row = item["row"]
        predicted = depth_predictions(item, threshold, minimum_separation_bins)
        predicted_depths = sorted({round(value[0], 8) for value in predicted})
        expected_depths = sorted(float(value["depth_m"]) for value in row["boundaries"])
        tp, fp, fn, errors = match_points(predicted_depths, expected_depths, tolerance_m)
        boundary["tp"] += tp; boundary["fp"] += fp; boundary["fn"] += fn; boundary["errors"].extend(errors)
        predicted_intervals = list(zip(predicted_depths, predicted_depths[1:]))
        expected_intervals = list(zip(expected_depths, expected_depths[1:]))
        remaining = set(range(len(expected_intervals)))
        interval_tp = interval_fp = 0
        for top, bottom in predicted_intervals:
            candidates = [
                index for index in remaining
                if abs(top - expected_intervals[index][0]) <= tolerance_m
                and abs(bottom - expected_intervals[index][1]) <= tolerance_m
            ]
            if candidates:
                interval_tp += 1; remaining.remove(candidates[0])
            else:
                interval_fp += 1
        interval["tp"] += interval_tp; interval["fp"] += interval_fp; interval["fn"] += len(remaining)
        predictions.append({
            "sample_id": row["sample_id"],
            "source_group": row["source_group"],
            "expected_depths_m": expected_depths,
            "predicted": [
                {"depth_m": depth, "normalized_y": y, "confidence": confidence}
                for depth, y, confidence in predicted
            ],
        })
    boundary_metrics = prf(boundary["tp"], boundary["fp"], boundary["fn"])
    boundary_metrics["mae_m"] = sum(boundary["errors"]) / len(boundary["errors"]) if boundary["errors"] else None
    return {
        "threshold": threshold,
        "boundary_at_tolerance": boundary_metrics,
        "interval_at_tolerance": prf(interval["tp"], interval["fp"], interval["fn"]),
        "critical_numerical_error_rate": boundary["fp"] / (boundary["tp"] + boundary["fp"]) if boundary["tp"] + boundary["fp"] else None,
        "structural_evidence_coverage": boundary_metrics["recall"],
        "predictions": predictions,
    }


def choose_threshold(inferences: list[dict], minimum_separation_bins: int, tolerance_m: float) -> tuple[float, dict, str]:
    candidates = []
    for threshold in np.linspace(0.05, 0.95, 91):
        result = score(inferences, float(threshold), minimum_separation_bins, tolerance_m)
        metric = result["boundary_at_tolerance"]
        candidates.append((float(threshold), result, metric))
    reliable = [row for row in candidates if row[2]["precision"] >= 0.90]
    if reliable:
        chosen = max(reliable, key=lambda row: (row[2]["recall"], row[2]["f1"], row[0]))
        return chosen[0], chosen[1], "maximize_recall_subject_to_precision_ge_0.90"
    chosen = max(candidates, key=lambda row: (row[2]["f1"], row[2]["precision"], row[0]))
    return chosen[0], chosen[1], "maximize_f1_no_precision_0.90_operating_point"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--dataset-root", type=Path, default=Path("/data/GeoLogParser/datasets/paper2_nativemm_dense_boundary_v001"))
    parser.add_argument("--model", type=Path, default=Path("/data/GeoLogParser/models/huggingface/PaddleOCR-VL-1.6"))
    parser.add_argument("--model-revision", default="c5630abae1d940eafe0697512a0325494b02ab42")
    parser.add_argument("--cache-root", type=Path, default=Path("/root/GeoLogParser/.cache/nativemm_dense_v001"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--bins", type=int, default=512)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--synthetic-epochs", type=int, default=16)
    parser.add_argument("--real-epochs", type=int, default=45)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--seed", type=int, default=20260816)
    parser.add_argument("--minimum-separation-bins", type=int, default=3)
    parser.add_argument("--tolerance-m", type=float, default=0.05)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"immutable result path already exists: {args.output}")
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    torch.cuda.set_device(args.device); torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(args.device)
    train_rows = read_rows(args.dataset_root / "train.jsonl")
    development_rows = read_rows(args.dataset_root / "development.jsonl")
    processor = AutoProcessor.from_pretrained(args.model, trust_remote_code=False)
    backbone = AutoModelForImageTextToText.from_pretrained(
        args.model, trust_remote_code=False, dtype=torch.bfloat16,
    ).to(args.device).eval()
    for parameter in backbone.parameters():
        parameter.requires_grad_(False)
    all_rows = train_rows + development_rows
    features = {}
    extraction_started = time.perf_counter()
    for index, row in enumerate(all_rows, 1):
        features[row["sample_id"]] = load_or_extract(
            row, processor=processor, backbone=backbone, cache_root=args.cache_root,
            model_revision=args.model_revision, bins=args.bins, device=args.device,
        )
        if index % 25 == 0:
            print(f"cached {index}/{len(all_rows)}", flush=True)
    feature_seconds = time.perf_counter() - extraction_started
    del backbone
    torch.cuda.empty_cache()
    visual_dim = next(iter(features.values()))["visual"].shape[0]
    pixel_dim = next(iter(features.values()))["pixels"].shape[0]
    model = DenseBoundaryHead(visual_dim, pixel_dim, args.hidden_dim).to(args.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-4)
    synthetic = [row for row in train_rows if row["source_tier"] == "SYNTHETIC"]
    real_fit = [row for row in train_rows if row["source_tier"] != "SYNTHETIC" and row["fold"] != 1]
    calibration = [row for row in train_rows if row["source_tier"] != "SYNTHETIC" and row["fold"] == 1]
    losses = []

    def train_epochs(rows: list[dict], epochs: int, phase: str) -> None:
        model.train()
        for epoch in range(epochs):
            epoch_rows = list(rows)
            random.Random(args.seed + epoch + (1000 if phase == "real" else 0)).shuffle(epoch_rows)
            for row in epoch_rows:
                value = features[row["sample_id"]]
                targets = gaussian_targets([item["y"] for item in row["boundaries"]], args.bins).unsqueeze(0).to(args.device)
                logits = model(
                    value["visual"].unsqueeze(0).to(args.device, dtype=torch.float32),
                    value["pixels"].unsqueeze(0).to(args.device, dtype=torch.float32),
                )
                loss = boundary_loss(logits, targets)
                optimizer.zero_grad(set_to_none=True); loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step(); losses.append({"phase": phase, "loss": float(loss.detach().cpu())})

    training_started = time.perf_counter()
    train_epochs(synthetic, args.synthetic_epochs, "synthetic")
    for group in optimizer.param_groups:
        group["lr"] = args.learning_rate * 0.35
    # Retain a quarter of synthetic pages during real adaptation to reduce
    # catastrophic loss of graphical-boundary localization.
    mixed_real = real_fit + synthetic[::4]
    train_epochs(mixed_real, args.real_epochs, "real")
    training_seconds = time.perf_counter() - training_started
    calibration_inference = infer_rows(model, calibration, features, args.device)
    threshold, calibration_metrics, threshold_policy = choose_threshold(
        calibration_inference, args.minimum_separation_bins, args.tolerance_m,
    )
    evaluation_rows = [
        row for row in development_rows
        if row["source_dataset"] == "bgs_offshore_gold_v001" and row["fold"] == 0
    ]
    evaluation_inference = infer_rows(model, evaluation_rows, features, args.device)
    evaluation = score(evaluation_inference, threshold, args.minimum_separation_bins, args.tolerance_m)
    predictions = evaluation.pop("predictions")
    args.output.mkdir(parents=True)
    checkpoint = args.output / "dense_boundary_head.pt"
    torch.save({
        "state_dict": model.state_dict(), "visual_dim": visual_dim, "pixel_dim": pixel_dim,
        "hidden_dim": args.hidden_dim, "bins": args.bins, "threshold": threshold,
        "minimum_separation_bins": args.minimum_separation_bins,
    }, checkpoint)
    metrics = {
        "experiment_id": args.experiment_id,
        "status": "completed",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "backbone": str(args.model),
        "model_revision": args.model_revision,
        "dataset_root": str(args.dataset_root),
        "train_sha256": sha256(args.dataset_root / "train.jsonl"),
        "development_sha256": sha256(args.dataset_root / "development.jsonl"),
        "training_counts": {"synthetic": len(synthetic), "real_fit": len(real_fit), "real_calibration": len(calibration)},
        "evaluation_sample_count": len(evaluation_rows),
        "threshold": threshold,
        "threshold_policy": threshold_policy,
        "calibration_metrics": {key: value for key, value in calibration_metrics.items() if key != "predictions"},
        "boundary_at_0_05m": evaluation["boundary_at_tolerance"],
        "interval_at_0_05m": evaluation["interval_at_tolerance"],
        "critical_numerical_error_rate": evaluation["critical_numerical_error_rate"],
        "structural_evidence_coverage": evaluation["structural_evidence_coverage"],
        "feature_extraction_seconds": feature_seconds,
        "training_seconds": training_seconds,
        "seconds_per_evaluation_page": None,
        "peak_allocated_gib": torch.cuda.max_memory_allocated(args.device) / 1024 ** 3,
        "peak_reserved_gib": torch.cuda.max_memory_reserved(args.device) / 1024 ** 3,
        "mean_loss": sum(item["loss"] for item in losses) / len(losses),
        "final_loss": losses[-1]["loss"],
        "checkpoint_sha256": sha256(checkpoint),
        "scope": "source-disjoint BGS v001 development; BGS v002 and California v004/v005 unopened",
    }
    (args.output / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in predictions),
        encoding="utf-8",
    )
    (args.output / "losses.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in losses), encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
