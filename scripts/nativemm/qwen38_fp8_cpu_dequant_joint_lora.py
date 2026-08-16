#!/usr/bin/env python3
"""CPU-dequantized-from-FP8 fallback for a complete multimodal gradient chain.

This path does not download BF16 weights.  Transformers dequantizes the local
FP8 checkpoint into BF16 in host RAM because no CUDA quantized kernel is used
for the language stack.  The visual encoder/projector and their BF16 LoRA
adapters run on RTX 5090; the frozen language stack and optional selective
language LoRA remain on CPU.  The multimodal merge is executed explicitly so
the autograd path from language loss back through the image features remains
observable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
import traceback
from pathlib import Path

from PIL import Image
import torch
from torch import nn
from transformers import AutoConfig, AutoModelForImageTextToText, AutoProcessor


class ResidualLoRA(nn.Module):
    def __init__(self, base: nn.Module, rank: int = 4, alpha: int = 8, device: torch.device | None = None):
        super().__init__()
        self.base = base
        for p in base.parameters():
            p.requires_grad = False
        device = device or next(base.parameters()).device
        self.lora_a = nn.Linear(int(base.in_features), rank, bias=False, device=device, dtype=torch.bfloat16)
        self.lora_b = nn.Linear(rank, int(base.out_features), bias=False, device=device, dtype=torch.bfloat16)
        nn.init.kaiming_uniform_(self.lora_a.weight, a=5**0.5)
        nn.init.zeros_(self.lora_b.weight)
        self.scale = alpha / rank
        self.enabled = True

    def forward(self, hidden_states, *args, **kwargs):
        base = self.base(hidden_states, *args, **kwargs)
        if not self.enabled:
            return base
        delta = self.lora_b(self.lora_a(hidden_states.to(torch.bfloat16))) * self.scale
        return base + delta.to(base.dtype)


def resolve(root: nn.Module, name: str):
    parent = root
    parts = name.split(".")
    for part in parts[:-1]:
        parent = parent[int(part)] if part.isdigit() else getattr(parent, part)
    key = parts[-1]
    module = parent[int(key)] if key.isdigit() else getattr(parent, key)
    return parent, key, module


def replace(root: nn.Module, name: str, replacement: nn.Module):
    parent, key, _ = resolve(root, name)
    if key.isdigit():
        parent[int(key)] = replacement
    else:
        setattr(parent, key, replacement)


def wrap_group(model: nn.Module, names: list[str], device: torch.device) -> list[str]:
    out = []
    for name in names:
        _, _, module = resolve(model, name)
        if not isinstance(module, ResidualLoRA):
            replace(model, name, ResidualLoRA(module, device=device))
        out.append(name)
    return out


def toggle(model: nn.Module, groups: dict[str, list[str]], active: set[str]):
    for group, names in groups.items():
        for name in names:
            _, _, module = resolve(model, name)
            module.enabled = group in active
            module.lora_a.weight.requires_grad = group in active
            module.lora_b.weight.requires_grad = group in active


def grad_summary(model: nn.Module, names: list[str]):
    norms, nonzero, tensors, parameters = [], 0, 0, 0
    for name in names:
        _, _, module = resolve(model, name)
        for p in (module.lora_a.weight, module.lora_b.weight):
            if not p.requires_grad:
                continue
            tensors += 1
            parameters += p.numel()
            if p.grad is not None:
                norms.append(float(p.grad.detach().float().norm().item()))
                nonzero += int(p.grad.detach().abs().sum().item() > 0)
    return {
        "trainable_parameters": parameters,
        "trainable_tensors": tensors,
        "gradient_tensors": len(norms),
        "nonzero_gradient_tensors": nonzero,
        "gradient_norm_min": min(norms) if norms else None,
        "gradient_norm_max": max(norms) if norms else None,
    }


def build_inputs(processor, image_path: Path):
    image = Image.open(image_path).convert("RGB")
    prompt = (
        "Infer an intermediate structural graph: visual regions, column roles, structural events, "
        "semantic owners, boundary bbox/y, depth-axis relations and event relations. Do not output intervals."
    )
    target = json.dumps({
        "regions": [{"role": "log_table", "bbox": [0.05, 0.13, 0.95, 0.70]}],
        "columns": [
            {"role": "cumulative_depth", "bbox": [0.05, 0.13, 0.36, 0.70]},
            {"role": "layer_thickness", "bbox": [0.36, 0.13, 0.53, 0.70]},
            {"role": "description", "bbox": [0.53, 0.13, 0.95, 0.70]},
        ],
        "events": [{"type": "geological_boundary", "owner": "geological_description", "y": 0.256, "bbox": [0.05, 0.253, 0.95, 0.258]}],
        "depth_axis": [{"y": 0.168, "depth_m": 0.0}, {"y": 0.256, "depth_m": 3.23}],
        "relations": [["event_0", "depth_axis", "grounded_by"], ["description", "event_0", "owns"]],
    }, separators=(",", ":"))
    user = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
    full = user + [{"role": "assistant", "content": [{"type": "text", "text": target}]}]
    kwargs = {"images_kwargs": {"min_pixels": 65536, "max_pixels": 65536}}
    prompt_inputs = processor.apply_chat_template(user, tokenize=True, return_dict=True, return_tensors="pt", add_generation_prompt=True, processor_kwargs=kwargs)
    inputs = processor.apply_chat_template(full, tokenize=True, return_dict=True, return_tensors="pt", add_generation_prompt=False, processor_kwargs=kwargs)
    image.close()
    labels = inputs["input_ids"].clone()
    labels[:, : prompt_inputs["input_ids"].shape[-1]] = -100
    inputs["labels"] = labels
    return inputs, target


def multimodal_forward(model, inputs, vision_device: torch.device):
    input_ids = inputs["input_ids"]
    attention_mask = inputs.get("attention_mask")
    mm_token_type_ids = inputs.get("mm_token_type_ids")
    labels = inputs["labels"]
    pixel_values = inputs["pixel_values"].to(vision_device)
    image_grid_thw_gpu = inputs["image_grid_thw"].to(vision_device)
    image_grid_thw_cpu = inputs["image_grid_thw"]
    inputs_embeds = model.model.get_input_embeddings()(input_ids)
    image_outputs = model.model.get_image_features(pixel_values, image_grid_thw_gpu, return_dict=True)
    image_embeds = torch.cat(image_outputs.pooler_output, dim=0).to(inputs_embeds.device, inputs_embeds.dtype)
    image_mask, _ = model.model.get_placeholder_mask(input_ids, inputs_embeds=inputs_embeds, image_features=image_embeds)
    inputs_embeds = inputs_embeds.masked_scatter(image_mask, image_embeds)
    model.model.rope_deltas = None
    position_ids = model.model.compute_3d_position_ids(
        input_ids=input_ids,
        inputs_embeds=inputs_embeds,
        image_grid_thw=image_grid_thw_cpu,
        attention_mask=attention_mask,
        mm_token_type_ids=mm_token_type_ids,
    )
    outputs = model.model.language_model(
        input_ids=None,
        position_ids=position_ids,
        attention_mask=attention_mask,
        inputs_embeds=inputs_embeds,
        use_cache=False,
    )
    logits = model.lm_head(outputs[0])
    loss = model.loss_function(logits=logits, labels=labels, vocab_size=model.config.text_config.vocab_size)
    return loss


def run(args):
    vision_device = torch.device("cuda:0")
    started = time.perf_counter()
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=True)
    # With CUDA hidden, Transformers explicitly dequantizes the local FP8
    # checkpoint to BF16 in host RAM; no BF16 file is downloaded.
    config = AutoConfig.from_pretrained(args.model, local_files_only=True)
    # Force Transformers' official FP8 quantizer to dequantize in memory even
    # though CUDA is visible; this avoids downloading a BF16 checkpoint.
    if isinstance(config.quantization_config, dict):
        config.quantization_config["dequantize"] = True
    else:
        config.quantization_config.dequantize = True
    model = AutoModelForImageTextToText.from_pretrained(args.model, config=config, local_files_only=True, dtype=torch.bfloat16, device_map="cpu", low_cpu_mem_usage=True, trust_remote_code=False)
    for p in model.parameters():
        p.requires_grad = False
    model.model.visual.to(vision_device)
    vision = [f"model.visual.blocks.{i}.{s}" for i in range(27) for s in ("attn.qkv", "attn.proj", "mlp.linear_fc1", "mlp.linear_fc2")]
    projector = ["model.visual.merger.linear_fc1", "model.visual.merger.linear_fc2"]
    language = ["language_model.layers.3.self_attn.q_proj", "language_model.layers.3.self_attn.v_proj", "language_model.layers.3.self_attn.o_proj"]
    groups = {
        "vision": wrap_group(model.model, [x[len("model."):] for x in vision], vision_device),
        "projector": wrap_group(model.model, [x[len("model."):] for x in projector], vision_device),
        "language": wrap_group(model.model, language, torch.device("cpu")),
    }
    inputs, target = build_inputs(processor, args.image)
    for key in ("input_ids", "attention_mask", "labels", "mm_token_type_ids", "image_grid_thw"):
        if key in inputs:
            inputs[key] = inputs[key].to("cpu")
    stages = [("vision_lora", {"vision"}), ("vision_projector", {"vision", "projector"}), ("vision_projector_selective_llm", {"vision", "projector", "language"})]
    results = []
    for name, active in stages:
        toggle(model.model, groups, active)
        model.zero_grad(set_to_none=True)
        torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(0)
        t = time.perf_counter()
        try:
            loss = multimodal_forward(model, inputs, vision_device)
            loss.backward()
            sums = {g: grad_summary(model.model, groups[g]) for g in active}
            results.append({"stage": name, "status": "VERIFIED" if torch.isfinite(loss).item() and all(s["nonzero_gradient_tensors"] > 0 for s in sums.values()) else "FAILED_GRADIENT_GATE", "loss": float(loss.detach()), "finite_loss": bool(torch.isfinite(loss).item()), "gradient_groups": sums, "elapsed_seconds": time.perf_counter() - t, "peak_memory_allocated_gib": torch.cuda.max_memory_allocated(0) / 2**30, "peak_memory_reserved_gib": torch.cuda.max_memory_reserved(0) / 2**30})
        except BaseException as exc:
            results.append({"stage": name, "status": "FAILED", "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc(limit=8), "elapsed_seconds": time.perf_counter() - t, "peak_memory_allocated_gib": torch.cuda.max_memory_allocated(0) / 2**30, "peak_memory_reserved_gib": torch.cuda.max_memory_reserved(0) / 2**30})
            break
    return {"experiment_id": args.experiment_id, "checkpoint": str(args.model), "image": str(args.image), "gpu": torch.cuda.get_device_name(0), "backbone": "FP8 checkpoint dequantized to BF16 in host RAM", "adapter_dtype": "BF16", "prompt_tokens": int(inputs["labels"].shape[-1]), "visual_patch_tokens": int(inputs["pixel_values"].shape[0]), "target_sha256": hashlib.sha256(target.encode()).hexdigest(), "stages": results, "peak_process_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2, "elapsed_seconds": time.perf_counter() - started, "bgs_v003_accessed": False, "scope": "single synthetic joint-structure sample; complete multimodal autograd feasibility only"}


def main():
    p = argparse.ArgumentParser(); p.add_argument("--model", type=Path, default=Path("/data/LLM/Qwen/Qwen3.8-27B-FP8")); p.add_argument("--image", type=Path, default=Path("/data/GeoLogParser/datasets/synthetic_borehole_logs_v002/images/SYN-0008.png")); p.add_argument("--experiment-id", default="P2_QWEN38_FP8_CPU_DEQUANT_JOINT_LORA_001"); p.add_argument("--output", type=Path, required=True); args = p.parse_args(); out = run(args); args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"); print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__": main()
