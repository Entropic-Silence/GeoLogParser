#!/usr/bin/env python3
"""Actual Qwen3.8-FP8 visual-module LoRA forward/backward smoke test.

This deliberately loads only the ``model.visual`` checkpoint tensors.  The
Qwen3.8 FP8 language weights are not loaded into a 32 GiB single-GPU process;
the test therefore answers the narrow feasibility question that can be tested
locally without pretending to validate full multimodal SFT.  It verifies that
the official checkpoint's visual weights load, that PEFT LoRA targets visual
linear layers, and that one synthetic structural loss produces finite,
non-zero visual LoRA gradients.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

import torch
from peft import LoraConfig, get_peft_model
from safetensors import safe_open
from transformers import AutoConfig, Qwen3_5VisionModel


def load_visual(path: Path, device: str) -> tuple[torch.nn.Module, dict]:
    config = AutoConfig.from_pretrained(path, local_files_only=True)
    vision = Qwen3_5VisionModel(config.vision_config)
    state: dict[str, torch.Tensor] = {}
    outside = path / "outside.safetensors"
    with safe_open(str(outside), framework="pt", device="cpu") as handle:
        for key in handle.keys():
            if key.startswith("model.visual."):
                state[key[len("model.visual.") :]] = handle.get_tensor(key)
    missing, unexpected = vision.load_state_dict(state, strict=False)
    vision = vision.to(device=device, dtype=torch.bfloat16)
    return vision, {
        "loaded_visual_keys": len(state),
        "missing_keys": len(missing),
        "unexpected_keys": len(unexpected),
        "vision_parameter_count": sum(p.numel() for p in vision.parameters()),
    }


def run(args: argparse.Namespace) -> dict:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this smoke test")
    torch.cuda.set_device(args.device)
    torch.cuda.reset_peak_memory_stats(args.device)
    started = time.perf_counter()
    vision, load_info = load_visual(args.model, args.device)
    vision.train()

    # task_type=None is intentional: PEFT's task-specific feature-extraction
    # wrapper injects attention_mask into Qwen3.5 vision attention and is not
    # compatible with this Transformers 5.14 vision forward signature.
    lora = LoraConfig(
        r=4,
        lora_alpha=8,
        lora_dropout=0.0,
        target_modules=["qkv", "proj", "linear_fc1", "linear_fc2"],
        bias="none",
        task_type=None,
    )
    model = get_peft_model(vision, lora)

    # One 64x64 image represented as four temporal/spatial patches.  The
    # synthetic loss is only a wiring/gradient test, not a task metric.
    grid = torch.tensor([[1, 2, 2]], device=args.device, dtype=torch.long)
    pixels = torch.randn(4, 3, 2, 16, 16, device=args.device, dtype=torch.bfloat16)
    with torch.autocast("cuda", dtype=torch.bfloat16):
        output = model(hidden_states=pixels, grid_thw=grid)
        pooled = output.pooler_output
        loss = (pooled.float() ** 2).mean()
    loss.backward()

    grad_norms: list[float] = []
    nonzero = 0
    trainable_tensors = 0
    for parameter in model.parameters():
        if not parameter.requires_grad:
            continue
        trainable_tensors += 1
        if parameter.grad is not None:
            norm = float(parameter.grad.detach().float().norm().item())
            grad_norms.append(norm)
            nonzero += int(parameter.grad.detach().abs().sum().item() > 0)

    return {
        "experiment_id": args.experiment_id,
        "model_path": str(args.model),
        "transformers_version": __import__("transformers").__version__,
        "torch_version": torch.__version__,
        "device": str(args.device),
        "gpu_name": torch.cuda.get_device_name(args.device),
        "parameter_dtype": str(next(model.parameters()).dtype),
        "load": load_info,
        "lora": {
            "target_modules": ["qkv", "proj", "linear_fc1", "linear_fc2"],
            "rank": 4,
            "alpha": 8,
            "trainable_parameter_count": sum(p.numel() for p in model.parameters() if p.requires_grad),
            "trainable_tensor_count": trainable_tensors,
        },
        "synthetic_forward_backward": {
            "output_shape": list(pooled.shape),
            "loss": float(loss.detach().cpu()),
            "finite_loss": bool(torch.isfinite(loss).item()),
            "gradient_tensor_count": len(grad_norms),
            "nonzero_gradient_tensor_count": nonzero,
            "grad_norm_min": min(grad_norms) if grad_norms else None,
            "grad_norm_max": max(grad_norms) if grad_norms else None,
        },
        "peak_memory_allocated_gib": torch.cuda.max_memory_allocated(args.device) / 2**30,
        "peak_memory_reserved_gib": torch.cuda.max_memory_reserved(args.device) / 2**30,
        "elapsed_seconds": time.perf_counter() - started,
        "scope": "visual-submodule-only; full multimodal SFT NOT_COMPLETED",
        "bgs_v003_accessed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("/data/LLM/Qwen/Qwen3.8-27B-FP8"))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--experiment-id", default="P2_QWEN38_FP8_VISION_LORA_SMOKE_001")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
