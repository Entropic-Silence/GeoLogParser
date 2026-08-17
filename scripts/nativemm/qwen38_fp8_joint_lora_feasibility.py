#!/usr/bin/env python3
"""Staged low-bit multimodal gradient-chain feasibility for Qwen3.8-27B-FP8.

The FP8 backbone remains frozen.  Small BF16 residual LoRA adapters are added
to (1) the visual encoder, (2) the visual merger/projector, and (3) one
selected language attention layer.  This is a controlled one-sample gradient
test, not a performance experiment and not FP8 full-parameter training.
"""

from __future__ import annotations

import argparse
import json
from geologparser.runtime_resources import peak_process_rss_kib
from pathlib import Path
import time
import traceback

from PIL import Image
import torch
from torch import nn
from transformers import AutoModelForImageTextToText, AutoProcessor


class ResidualLoRA(nn.Module):
    """Adapter wrapper that also works around frozen FP8 linear modules."""

    def __init__(self, base: nn.Module, rank: int = 4, alpha: int = 8) -> None:
        super().__init__()
        if not hasattr(base, "in_features") or not hasattr(base, "out_features"):
            raise TypeError(f"Module lacks linear dimensions: {type(base).__name__}")
        self.base = base
        for parameter in base.parameters():
            parameter.requires_grad = False
        device = next(base.parameters()).device
        self.lora_a = nn.Linear(int(base.in_features), rank, bias=False, device=device, dtype=torch.bfloat16)
        self.lora_b = nn.Linear(rank, int(base.out_features), bias=False, device=device, dtype=torch.bfloat16)
        nn.init.kaiming_uniform_(self.lora_a.weight, a=5**0.5)
        nn.init.zeros_(self.lora_b.weight)
        self.scale = alpha / rank
        self.enabled = True

    def forward(self, hidden_states: torch.Tensor, *args, **kwargs):
        result = self.base(hidden_states, *args, **kwargs)
        if not self.enabled:
            return result
        update = self.lora_b(self.lora_a(hidden_states.to(torch.bfloat16))) * self.scale
        return result + update.to(result.dtype)


def _resolve(root: nn.Module, name: str) -> tuple[nn.Module, str, nn.Module]:
    parts = name.split(".")
    parent = root
    for part in parts[:-1]:
        parent = parent[int(part)] if part.isdigit() else getattr(parent, part)
    key = parts[-1]
    module = parent[int(key)] if key.isdigit() else getattr(parent, key)
    return parent, key, module


def _replace(root: nn.Module, name: str, replacement: nn.Module) -> None:
    parent, key, _ = _resolve(root, name)
    if key.isdigit():
        parent[int(key)] = replacement
    else:
        setattr(parent, key, replacement)


def _wrap_group(model: nn.Module, names: list[str]) -> list[str]:
    wrapped = []
    for name in names:
        _, _, module = _resolve(model, name)
        if isinstance(module, ResidualLoRA):
            wrapped.append(name)
            continue
        _replace(model, name, ResidualLoRA(module))
        wrapped.append(name)
    return wrapped


def _toggle(model: nn.Module, group_names: dict[str, list[str]], enabled_groups: set[str]) -> None:
    for group, names in group_names.items():
        active = group in enabled_groups
        for name in names:
            _, _, module = _resolve(model, name)
            assert isinstance(module, ResidualLoRA)
            module.enabled = active
            module.lora_a.weight.requires_grad = active
            module.lora_b.weight.requires_grad = active


def _gradient_summary(model: nn.Module, names: list[str]) -> dict:
    norms = []
    nonzero = 0
    count = 0
    parameters = 0
    for name in names:
        _, _, module = _resolve(model, name)
        for parameter in (module.lora_a.weight, module.lora_b.weight):
            if not parameter.requires_grad:
                continue
            count += 1
            parameters += parameter.numel()
            if parameter.grad is not None:
                norm = float(parameter.grad.detach().float().norm().item())
                norms.append(norm)
                nonzero += int(parameter.grad.detach().abs().sum().item() > 0)
    return {
        "trainable_parameters": parameters,
        "trainable_tensors": count,
        "gradient_tensors": len(norms),
        "nonzero_gradient_tensors": nonzero,
        "gradient_norm_min": min(norms) if norms else None,
        "gradient_norm_max": max(norms) if norms else None,
    }


def _training_inputs(processor, image_path: Path):
    image = Image.open(image_path).convert("RGB")
    prompt = (
        "Infer an intermediate structural graph. Supervise visual regions, semantic column roles, "
        "structural events with owners, boundary y/bbox evidence, depth-axis relations and event relations. "
        "Do not output final intervals."
    )
    target = json.dumps(
        {
            "regions": [{"role": "log_table", "bbox": [0.05, 0.13, 0.95, 0.70]}],
            "columns": [
                {"role": "cumulative_depth", "bbox": [0.05, 0.13, 0.36, 0.70]},
                {"role": "layer_thickness", "bbox": [0.36, 0.13, 0.53, 0.70]},
                {"role": "description", "bbox": [0.53, 0.13, 0.95, 0.70]},
            ],
            "events": [
                {"type": "geological_boundary", "owner": "geological_description", "y": 0.256, "bbox": [0.05, 0.253, 0.95, 0.258]}
            ],
            "depth_axis": [{"y": 0.168, "depth_m": 0.0}, {"y": 0.256, "depth_m": 3.23}],
            "relations": [
                {"source": "event_0", "target": "depth_axis", "type": "grounded_by"},
                {"source": "description", "target": "event_0", "type": "owns"},
            ],
        },
        separators=(",", ":"),
    )
    user = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
    full = user + [{"role": "assistant", "content": [{"type": "text", "text": target}]}]
    processor_kwargs = {"images_kwargs": {"min_pixels": 65536, "max_pixels": 65536}}
    prompt_inputs = processor.apply_chat_template(
        user, tokenize=True, return_dict=True, return_tensors="pt", add_generation_prompt=True,
        processor_kwargs=processor_kwargs,
    )
    inputs = processor.apply_chat_template(
        full, tokenize=True, return_dict=True, return_tensors="pt", add_generation_prompt=False,
        processor_kwargs=processor_kwargs,
    )
    image.close()
    labels = inputs["input_ids"].clone()
    labels[:, : prompt_inputs["input_ids"].shape[-1]] = -100
    inputs["labels"] = labels
    return inputs, prompt_inputs["input_ids"].shape[-1], target


def run(args: argparse.Namespace) -> dict:
    torch.cuda.set_device(args.device)
    started = time.perf_counter()
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=True)
    max_memory = {0: args.gpu_memory}
    for index in range(1, args.gpu_count):
        max_memory[index] = args.secondary_gpu_memory
    max_memory["cpu"] = args.cpu_memory
    model = AutoModelForImageTextToText.from_pretrained(
        args.model,
        local_files_only=True,
        dtype=torch.bfloat16,
        device_map="auto",
        max_memory=max_memory,
        offload_folder=str(args.offload_folder),
        low_cpu_mem_usage=True,
        trust_remote_code=False,
    )
    model.config.use_cache = False
    for parameter in model.parameters():
        parameter.requires_grad = False

    vision = [
        f"model.visual.blocks.{index}.{suffix}"
        for index in range(27)
        for suffix in ("attn.qkv", "attn.proj", "mlp.linear_fc1", "mlp.linear_fc2")
    ]
    projector = ["model.visual.merger.linear_fc1", "model.visual.merger.linear_fc2"]
    language = [
        "model.language_model.layers.3.self_attn.q_proj",
        "model.language_model.layers.3.self_attn.v_proj",
        "model.language_model.layers.3.self_attn.o_proj",
    ]
    groups = {"vision": _wrap_group(model, vision), "projector": _wrap_group(model, projector)}
    language_error = None
    try:
        groups["language"] = _wrap_group(model, language)
    except Exception as exc:  # recorded as evidence, not silently ignored
        groups["language"] = []
        language_error = f"{type(exc).__name__}: {exc}"

    inputs, prompt_tokens, target = _training_inputs(processor, args.image)
    first_device = torch.device("cuda:0")
    inputs = {name: tensor.to(first_device) for name, tensor in inputs.items()}
    stages = [
        ("vision_lora", {"vision"}),
        ("vision_projector", {"vision", "projector"}),
        ("vision_projector_selective_llm", {"vision", "projector", "language"}),
    ]
    stage_results = []
    for stage_name, active in stages:
        if "language" in active and not groups["language"]:
            stage_results.append({"stage": stage_name, "status": "NOT_COMPLETED", "error": language_error})
            continue
        _toggle(model, groups, active)
        model.zero_grad(set_to_none=True)
        torch.cuda.empty_cache()
        for index in range(args.gpu_count):
            torch.cuda.reset_peak_memory_stats(index)
        stage_started = time.perf_counter()
        try:
            model.train()
            output = model(**inputs, use_cache=False)
            loss = output.loss
            loss.backward()
            summaries = {name: _gradient_summary(model, groups[name]) for name in active}
            stage_results.append({
                "stage": stage_name,
                "status": "VERIFIED" if torch.isfinite(loss).item() and all(v["nonzero_gradient_tensors"] > 0 for v in summaries.values()) else "FAILED_GRADIENT_GATE",
                "loss": float(loss.detach().cpu()),
                "finite_loss": bool(torch.isfinite(loss).item()),
                "gradient_groups": summaries,
                "elapsed_seconds": time.perf_counter() - stage_started,
                "peak_memory_allocated_gib": {str(index): torch.cuda.max_memory_allocated(index) / 2**30 for index in range(args.gpu_count)},
                "peak_memory_reserved_gib": {str(index): torch.cuda.max_memory_reserved(index) / 2**30 for index in range(args.gpu_count)},
            })
        except BaseException as exc:
            stage_results.append({
                "stage": stage_name,
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(limit=8),
                "elapsed_seconds": time.perf_counter() - stage_started,
                "peak_memory_allocated_gib": {str(index): torch.cuda.max_memory_allocated(index) / 2**30 for index in range(args.gpu_count)},
                "peak_memory_reserved_gib": {str(index): torch.cuda.max_memory_reserved(index) / 2**30 for index in range(args.gpu_count)},
            })
            break
    return {
        "experiment_id": args.experiment_id,
        "checkpoint": str(args.model),
        "image": str(args.image),
        "device": args.device,
        "gpu_names": {str(index): torch.cuda.get_device_name(index) for index in range(args.gpu_count)},
        "max_memory": {str(key): value for key, value in max_memory.items()},
        "frozen_backbone": True,
        "adapter_dtype": "torch.bfloat16",
        "device_map": getattr(model, "hf_device_map", None),
        "prompt_tokens": prompt_tokens,
        "total_tokens": int(inputs["input_ids"].shape[-1]),
        "visual_patch_tokens": int(inputs["pixel_values"].shape[0]),
        "target_sha256": __import__("hashlib").sha256(target.encode()).hexdigest(),
        "stages": stage_results,
        "load_and_run_elapsed_seconds": time.perf_counter() - started,
        "peak_process_rss_gib": (peak_process_rss_kib() or 0) / 1024**2,
        "bgs_v003_accessed": False,
        "scope": "single synthetic joint-structure sample; gradient-chain feasibility only",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("/data/LLM/Qwen/Qwen3.8-27B-FP8"))
    parser.add_argument("--image", type=Path, default=Path("/data/GeoLogParser/datasets/synthetic_borehole_logs_v002/images/SYN-0008.png"))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--gpu-memory", default="22GiB")
    parser.add_argument("--secondary-gpu-memory", default="18GiB")
    parser.add_argument("--gpu-count", type=int, default=1)
    parser.add_argument("--cpu-memory", default="180GiB")
    parser.add_argument("--offload-folder", type=Path, default=Path("/data/GeoLogParser/cache/qwen38_fp8_joint_lora"))
    parser.add_argument("--experiment-id", default="P2_QWEN38_FP8_JOINT_LORA_FEASIBILITY_001")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.offload_folder.mkdir(parents=True, exist_ok=True)
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
