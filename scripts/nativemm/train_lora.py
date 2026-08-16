#!/usr/bin/env python3
"""Checkpointed single-GPU LoRA training for NativeMM structural tasks."""

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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def language_lora_targets(model) -> list[str]:
    return [
        name for name, _ in model.named_modules()
        if name.startswith("model.language_model.layers.")
        and (name.endswith(".self_attn.q_proj") or name.endswith(".self_attn.v_proj"))
    ]


def multimodal_lora_targets(model, include_projector: bool = True) -> list[str]:
    """Select language attention plus the visual-to-language projector.

    The original v001 adapter intentionally froze the aligner.  That is a
    useful OCR-preserving baseline, but it leaves the visual tokens aligned
    for transcription rather than structural grounding.  The v002 native
    branch therefore adapts only the small projector in addition to the
    language q/v blocks; the vision tower remains frozen.
    """
    targets = language_lora_targets(model)
    if include_projector:
        targets.extend(
            name for name, _ in model.named_modules()
            if name in {"model.projector.linear_1", "model.projector.linear_2"}
        )
    return targets


def git_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], text=True, stdout=subprocess.PIPE, check=True).stdout.strip()


def load_rows(path: Path, source_mode: str, task_families: set[str] | None, maximum_samples: int | None, seed: int) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if source_mode == "synthetic":
        rows = [row for row in rows if row["source_tier"] == "SYNTHETIC"]
    elif source_mode == "real":
        rows = [row for row in rows if row["source_tier"] != "SYNTHETIC"]
    if task_families:
        rows = [row for row in rows if row["task_family"] in task_families]
    random.Random(seed).shuffle(rows)
    return rows[:maximum_samples] if maximum_samples else rows


def conversation(row: dict, image: Image.Image, include_answer: bool) -> list[dict]:
    prompt = row["messages"][0]["content"].replace("<image>\n", "", 1)
    messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
    if include_answer:
        messages.append({"role": "assistant", "content": [{"type": "text", "text": row["messages"][1]["content"]}]})
    return messages


def encode(processor, row: dict, *, max_pixels: int, max_length: int, device: str) -> dict[str, torch.Tensor]:
    image = Image.open(row["images"][0]).convert("RGB")
    full_messages = conversation(row, image, True)
    prompt_messages = conversation(row, image, False)
    image_processor = processor.image_processor
    min_pixels = getattr(image_processor, "min_pixels", None) or getattr(image_processor, "size", {}).get("shortest_edge", 112896)
    kwargs = {
        "tokenize": True,
        "return_dict": True,
        "return_tensors": "pt",
        "images_kwargs": {"size": {"shortest_edge": min_pixels, "longest_edge": max_pixels}},
    }
    full = processor.apply_chat_template(full_messages, add_generation_prompt=False, **kwargs)
    prompt = processor.apply_chat_template(prompt_messages, add_generation_prompt=True, **kwargs)
    if full["input_ids"].shape[-1] > max_length:
        for key in ("input_ids", "attention_mask", "token_type_ids"):
            if key in full:
                full[key] = full[key][..., :max_length]
    labels = full["input_ids"].clone()
    prompt_length = min(prompt["input_ids"].shape[-1], labels.shape[-1])
    labels[:, :prompt_length] = -100
    if processor.tokenizer.pad_token_id is not None:
        labels[labels == processor.tokenizer.pad_token_id] = -100
    full["labels"] = labels
    image.close()
    return full.to(device)


def save_checkpoint(model, output: Path, metadata: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output / "adapter")
    (output / "training_state.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def train(args: argparse.Namespace) -> dict:
    from peft import LoraConfig, PeftModel, get_peft_model

    if args.output.exists():
        raise FileExistsError(f"immutable training output already exists: {args.output}")
    rows = load_rows(args.dataset, args.source_mode, set(args.task_family) if args.task_family else None, args.maximum_samples, args.seed)
    if not rows:
        raise RuntimeError("training selection is empty")
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.set_device(args.device)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(args.device)
    processor = AutoProcessor.from_pretrained(args.model, trust_remote_code=False)
    base = AutoModelForImageTextToText.from_pretrained(args.model, trust_remote_code=False, dtype=torch.bfloat16).to(args.device)
    base.config.use_cache = False
    target_modules = multimodal_lora_targets(base, include_projector=args.include_projector)
    if args.resume_adapter:
        model = PeftModel.from_pretrained(base, args.resume_adapter, is_trainable=True)
    else:
        model = get_peft_model(base, LoraConfig(
            r=args.lora_rank, lora_alpha=args.lora_alpha, lora_dropout=0.0,
            bias="none", target_modules=target_modules, task_type="CAUSAL_LM",
        ))
    model.train()
    trainable = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    total = sum(parameter.numel() for parameter in model.parameters())
    optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad), lr=args.learning_rate)
    losses = []
    optimizer_steps = 0
    sample_steps = 0
    started = time.perf_counter()
    optimizer.zero_grad(set_to_none=True)
    for epoch in range(args.epochs):
        epoch_rows = list(rows)
        random.Random(args.seed + epoch).shuffle(epoch_rows)
        for row in epoch_rows:
            inputs = encode(processor, row, max_pixels=args.max_pixels, max_length=args.max_length, device=args.device)
            result = model(**inputs)
            loss = result.loss / args.gradient_accumulation
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite loss for {row['sample_id']}: {float(loss)}")
            loss.backward()
            losses.append(float(loss.detach().cpu()) * args.gradient_accumulation)
            sample_steps += 1
            if sample_steps % args.gradient_accumulation == 0 or row is epoch_rows[-1]:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                optimizer_steps += 1
    torch.cuda.synchronize(args.device)
    elapsed = time.perf_counter() - started
    metadata = {
        "experiment_id": args.experiment_id,
        "status": "completed",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "model": str(args.model),
        "model_revision": args.model_revision,
        "resume_adapter": str(args.resume_adapter) if args.resume_adapter else None,
        "dataset": str(args.dataset),
        "dataset_sha256": file_sha256(args.dataset),
        "source_mode": args.source_mode,
        "task_families": args.task_family or "all",
        "seed": args.seed,
        "epochs": args.epochs,
        "sample_count": len(rows),
        "sample_steps": sample_steps,
        "optimizer_steps": optimizer_steps,
        "gradient_accumulation": args.gradient_accumulation,
        "learning_rate": args.learning_rate,
        "lora_rank": args.lora_rank,
        "lora_alpha": args.lora_alpha,
        "target_modules": target_modules,
        "trainable_parameters": trainable,
        "total_parameters_with_adapter": total,
        "trainable_fraction": trainable / total,
        "mean_training_loss": sum(losses) / len(losses),
        "final_training_loss": losses[-1],
        "minimum_training_loss": min(losses),
        "wall_time_seconds": elapsed,
        "samples_per_second": sample_steps / elapsed,
        "peak_allocated_gib": torch.cuda.max_memory_allocated(args.device) / 1024 ** 3,
        "peak_reserved_gib": torch.cuda.max_memory_reserved(args.device) / 1024 ** 3,
        "scope": "development training; no frozen external source used",
    }
    save_checkpoint(model, args.output, metadata)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--model", type=Path, default=Path("/data/GeoLogParser/models/huggingface/PaddleOCR-VL-1.6"))
    parser.add_argument("--model-revision", default="c5630abae1d940eafe0697512a0325494b02ab42")
    parser.add_argument("--dataset", type=Path, default=Path("/data/GeoLogParser/datasets/paper2_nativemm_v001/train.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume-adapter", type=Path)
    parser.add_argument("--source-mode", choices=["all", "synthetic", "real"], default="all")
    parser.add_argument("--task-family", action="append")
    parser.add_argument("--maximum-samples", type=int)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--gradient-accumulation", type=int, default=4)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--lora-rank", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--max-pixels", type=int, default=501760)
    parser.add_argument("--max-length", type=int, default=4096)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--include-projector", action=argparse.BooleanOptionalAction, default=False,
        help="adapt the visual-to-language projector (enabled for NativeMM v002; v001 stays language-only)",
    )
    args = parser.parse_args()
    print(json.dumps(train(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
