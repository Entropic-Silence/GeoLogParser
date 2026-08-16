#!/usr/bin/env python3
"""GPU inference and one-step LoRA trainability audit for NativeMM backbones."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from PIL import Image
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor


BACKBONES = {
    "paddleocr_vl_1_6": {
        "path": Path("/data/GeoLogParser/models/huggingface/PaddleOCR-VL-1.6"),
        "revision": "c5630abae1d940eafe0697512a0325494b02ab42",
        "license": "Apache-2.0",
    },
    "mineru2_5_pro_2604": {
        "path": Path("/data/GeoLogParser/models/huggingface/MinerU2.5-Pro-2604-1.2B"),
        "revision": "d3f5e08d073c21466bbabe21c71bb1e9c2e595da",
        "license": "Apache-2.0",
    },
}


def language_lora_targets(model) -> list[str]:
    """Return exact language-block q/v modules, excluding the vision encoder."""
    return [
        name for name, _ in model.named_modules()
        if name.startswith("model.language_model.layers.")
        and (name.endswith(".self_attn.q_proj") or name.endswith(".self_attn.v_proj"))
    ]


def multimodal_lora_targets(model) -> list[str]:
    targets = language_lora_targets(model)
    targets.extend(
        name for name, _ in model.named_modules()
        if name in {"model.projector.linear_1", "model.projector.linear_2"}
    )
    return targets


def load_row(path: Path, task_family: str) -> dict:
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["task_family"] == task_family and row["source_dataset"] == "synthetic_borehole_logs_v001":
            return row
    raise RuntimeError(f"no {task_family} synthetic row in {path}")


def conversations(row: dict, image: Image.Image) -> tuple[list[dict], list[dict]]:
    user_text = row["messages"][0]["content"].replace("<image>\n", "", 1)
    answer = row["messages"][1]["content"]
    user = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": user_text}]}]
    full = user + [{"role": "assistant", "content": [{"type": "text", "text": answer}]}]
    return user, full


def encode(processor, messages: list[dict], *, generation_prompt: bool, max_pixels: int) -> dict[str, torch.Tensor]:
    image_processor = processor.image_processor
    minimum_pixels = getattr(image_processor, "min_pixels", None)
    if minimum_pixels is None:
        minimum_pixels = getattr(image_processor, "size", {}).get("shortest_edge", 112896)
    return processor.apply_chat_template(
        messages,
        add_generation_prompt=generation_prompt,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        images_kwargs={
            "size": {
                "shortest_edge": minimum_pixels,
                "longest_edge": max_pixels,
            }
        },
    )


def cuda_process_snapshot() -> list[dict[str, str]]:
    import subprocess

    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,process_name,used_gpu_memory", "--format=csv,noheader"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    return [{"row": line.strip()} for line in result.stdout.splitlines() if line.strip()]


def run(backbone: str, dataset: Path, output: Path, device: str, max_pixels: int) -> dict:
    from peft import LoraConfig, get_peft_model

    spec = BACKBONES[backbone]
    row = load_row(dataset, "boundary_grounding")
    image = Image.open(row["images"][0]).convert("RGB")
    torch.cuda.set_device(device)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    # PaddleOCR-VL is native in current Transformers.  Enabling remote code
    # loads the checkpoint's older flat config while dispatching to the newer
    # built-in model, which is an invalid mixed runtime.
    processor = AutoProcessor.from_pretrained(spec["path"], trust_remote_code=False)
    model = AutoModelForImageTextToText.from_pretrained(
        spec["path"], trust_remote_code=False, dtype=torch.bfloat16,
    ).to(device)
    model.eval()
    load_seconds = time.perf_counter() - started
    user, full = conversations(row, image)

    inference_inputs = encode(processor, user, generation_prompt=True, max_pixels=max_pixels).to(device)
    torch.cuda.synchronize(device)
    inference_started = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(**inference_inputs, max_new_tokens=96, do_sample=False)
    torch.cuda.synchronize(device)
    inference_seconds = time.perf_counter() - inference_started
    prompt_tokens = int(inference_inputs["input_ids"].shape[-1])
    new_tokens = generated[:, prompt_tokens:]
    new_token_count = int(new_tokens.shape[-1])
    output_text = processor.batch_decode(new_tokens, skip_special_tokens=True)[0]
    try:
        json.loads(output_text)
        json_valid = True
    except (ValueError, TypeError):
        json_valid = False
    del inference_inputs, generated, new_tokens
    torch.cuda.empty_cache()

    model.train()
    target_modules = multimodal_lora_targets(model)
    peft_model = get_peft_model(
        model,
        LoraConfig(
            r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
            target_modules=target_modules, task_type="CAUSAL_LM",
        ),
    )
    trainable = sum(parameter.numel() for parameter in peft_model.parameters() if parameter.requires_grad)
    total = sum(parameter.numel() for parameter in peft_model.parameters())
    train_inputs = encode(processor, full, generation_prompt=False, max_pixels=min(max_pixels, 640 * 28 * 28))
    prompt_inputs = encode(processor, user, generation_prompt=True, max_pixels=min(max_pixels, 640 * 28 * 28))
    labels = train_inputs["input_ids"].clone()
    prompt_length = min(prompt_inputs["input_ids"].shape[-1], labels.shape[-1])
    labels[:, :prompt_length] = -100
    labels[labels == processor.tokenizer.pad_token_id] = -100
    train_inputs["labels"] = labels
    train_inputs = train_inputs.to(device)
    optimizer = torch.optim.AdamW((parameter for parameter in peft_model.parameters() if parameter.requires_grad), lr=1e-4)
    torch.cuda.synchronize(device)
    train_started = time.perf_counter()
    optimizer.zero_grad(set_to_none=True)
    result = peft_model(**train_inputs)
    loss = result.loss
    loss.backward()
    gradient_norm_sq = 0.0
    finite_gradients = True
    for parameter in peft_model.parameters():
        if parameter.grad is None:
            continue
        finite_gradients = finite_gradients and bool(torch.isfinite(parameter.grad).all())
        gradient_norm_sq += float(parameter.grad.float().norm().item()) ** 2
    optimizer.step()
    torch.cuda.synchronize(device)
    train_seconds = time.perf_counter() - train_started
    report = {
        "experiment_id": f"P2_NATIVEMM_BACKBONE_SMOKE_{backbone.upper()}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "backbone": backbone,
        "model_path": str(spec["path"]),
        "model_revision": spec["revision"],
        "license": spec["license"],
        "dataset": str(dataset),
        "sample_id": row["sample_id"],
        "device": device,
        "torch_version": torch.__version__,
        "transformers_version": __import__("transformers").__version__,
        "peft_version": __import__("peft").__version__,
        "load_seconds": load_seconds,
        "inference_seconds": inference_seconds,
        "inference_prompt_tokens": prompt_tokens,
        "inference_new_tokens": new_token_count,
        "inference_output": output_text[:4000],
        "inference_json_valid": json_valid,
        "train_step_seconds": train_seconds,
        "train_loss": float(loss.detach().cpu()),
        "finite_gradients": finite_gradients,
        "gradient_norm": gradient_norm_sq ** 0.5,
        "trainable_parameters": trainable,
        "target_modules": target_modules,
        "total_parameters_with_adapter": total,
        "trainable_fraction": trainable / total,
        "peak_allocated_gib": torch.cuda.max_memory_allocated(device) / 1024 ** 3,
        "peak_reserved_gib": torch.cuda.max_memory_reserved(device) / 1024 ** 3,
        "cuda_processes_after": cuda_process_snapshot(),
        "status": "completed" if finite_gradients and torch.isfinite(loss) else "failed",
        "scope": "single-sample inference and one optimizer step; not a quality result",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backbone", choices=sorted(BACKBONES), required=True)
    parser.add_argument("--dataset", type=Path, default=Path("/data/GeoLogParser/datasets/paper2_nativemm_smoke_v001/train.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--max-pixels", type=int, default=1003520)
    args = parser.parse_args()
    print(json.dumps(run(args.backbone, args.dataset, args.output, args.device, args.max_pixels), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
