#!/usr/bin/env python3
"""Run B4/B5 VLM engineering audits without treating auto labels as GT."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path

from geologparser.constraints import default_engine
from geologparser.experiment import create_run_directory
from geologparser.schema import validate_record
from geologparser.vlm import (
    Qwen3VLTransformersAdapter,
    compact_payload_to_record,
    parse_json_object,
)


ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"
MODEL_PATH = Path("/data/GeoLogParser/models/huggingface/Qwen3-VL-4B-Instruct")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def constraint_dict(result):
    return result.__dict__ | {
        "violations": [violation.__dict__ for violation in result.violations],
    }


def field_count(record: dict) -> tuple[int, int]:
    borehole_values = sum(item["value"] is not None for item in record["borehole"].values())
    interval_values = sum(
        item["value"] is not None
        for interval in record["intervals"]
        for name, item in interval.items()
        if name != "interval_id"
    )
    return borehole_values, interval_values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, default=ROOT / "prompts/vlm_extract_v001.md")
    parser.add_argument("--prompt-version", default="vlm_extract_v001")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--model-path", type=Path, default=MODEL_PATH)
    parser.add_argument("--max-new-tokens", type=int, default=2048)
    parser.add_argument("--min-pixels", type=int, default=256 * 28 * 28)
    parser.add_argument("--max-pixels", type=int, default=1280 * 28 * 28)
    parser.add_argument("--limit", type=int)
    arguments = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") in (None, "", "-1"):
        raise RuntimeError("set CUDA_VISIBLE_DEVICES to one explicitly selected, paused GPU")
    manifest = [
        json.loads(line) for line in arguments.manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if arguments.limit is not None:
        manifest = manifest[: arguments.limit]
    if not manifest:
        raise ValueError("audit manifest is empty")
    prompt = arguments.prompt.read_text(encoding="utf-8")
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    import torch

    device = torch.cuda.get_device_properties(0)
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": git_commit,
        "date": "2026-08-12",
        "dataset_version": arguments.dataset_version,
        "split_version": "engineering_audit_no_training_no_ground_truth",
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "prompt_version": arguments.prompt_version,
        "seed": None,
        "hardware": {
            "device": "cuda:0",
            "visible_physical_gpu": os.environ["CUDA_VISIBLE_DEVICES"],
            "gpu_name": device.name,
            "vram_bytes": device.total_memory,
        },
        "software": {
            "python": platform.python_version(), "torch": version("torch"),
            "transformers": version("transformers"), "accelerate": version("accelerate"),
        },
        "config": {
            "model_path": str(arguments.model_path),
            "manifest_path": str(arguments.manifest),
            "manifest_sha256": sha256(arguments.manifest),
            "prompt_path": str(arguments.prompt.resolve().relative_to(ROOT)),
            "prompt_sha256": sha256(arguments.prompt),
            "max_new_tokens": arguments.max_new_tokens,
            "min_pixels": arguments.min_pixels,
            "max_pixels": arguments.max_pixels,
            "do_sample": False,
            "scope": "engineering audit; no Ground Truth accuracy claim",
        },
    })
    adapter = Qwen3VLTransformersAdapter(
        arguments.model_path,
        model_id=MODEL_ID,
        model_revision=MODEL_REVISION,
        max_new_tokens=arguments.max_new_tokens,
        min_pixels=arguments.min_pixels,
        max_pixels=arguments.max_pixels,
    )
    outputs = []
    errors = []
    with (run / "predictions.jsonl").open("w", encoding="utf-8") as stream:
        for item in manifest:
            image_path = Path(item.get("rendered_path") or item.get("image_path") or item.get("local_path"))
            item_id = str(item.get("panel_id") or item.get("source_record_id") or image_path.stem)
            generation = adapter.generate([image_path], prompt, prompt_version=arguments.prompt_version)
            row = {
                "item_id": item_id,
                "image_path": str(image_path),
                "image_sha256": sha256(image_path),
                "raw_response": generation.text,
                "latency_seconds": generation.latency_seconds,
                "peak_gpu_memory_bytes": generation.peak_gpu_memory_bytes,
                "output_tokens": generation.output_tokens,
                "hit_max_new_tokens": generation.hit_max_new_tokens,
                "generation_config": dict(generation.generation_config),
                "parse_status": "failed",
                "record": None,
                "constraints": [],
            }
            try:
                payload = parse_json_object(generation.text)
                record = compact_payload_to_record(
                    payload,
                    document_id=item_id,
                    source_file=image_path,
                    source_sha256=row["image_sha256"],
                )
                record["document"]["metadata"].update({
                    "template_id": item.get("template_id"),
                    "project_id": item.get("project_id"),
                    "source_id": arguments.dataset_version,
                    "dpi": item.get("render_dpi"),
                })
                validate_record(record)
                row["record"] = record
                row["constraints"] = [constraint_dict(result) for result in default_engine().evaluate(record)]
                row["parse_status"] = "schema_valid"
            except Exception as exc:
                row["parse_error"] = f"{type(exc).__name__}: {exc}"
                errors.append({"item_id": item_id, "error_type": "vlm_structured_parse_failure", "message": row["parse_error"]})
            outputs.append(row)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
    valid = [row for row in outputs if row["parse_status"] == "schema_valid"]
    borehole_fields = interval_fields = total_intervals = evaluated = violations = 0
    for row in valid:
        borehole_count, interval_count = field_count(row["record"])
        borehole_fields += borehole_count
        interval_fields += interval_count
        total_intervals += len(row["record"]["intervals"])
        evaluated += sum(result["evaluated_count"] for result in row["constraints"])
        violations += sum(len(result["violations"]) for result in row["constraints"])
    metrics = {
        "scope": "engineering audit; no Ground Truth accuracy claim",
        "items": len(outputs),
        "schema_valid_responses": len(valid),
        "structured_parse_rate": len(valid) / len(outputs),
        "emitted_borehole_field_values": borehole_fields,
        "emitted_interval_field_values": interval_fields,
        "emitted_intervals": total_intervals,
        "constraint_evaluations": evaluated,
        "constraint_violations": violations,
        "latency_total_seconds": sum(row["latency_seconds"] for row in outputs),
        "latency_mean_seconds_per_image": sum(row["latency_seconds"] for row in outputs) / len(outputs),
        "peak_gpu_memory_bytes": max(row["peak_gpu_memory_bytes"] or 0 for row in outputs),
        "responses_hitting_max_new_tokens": sum(bool(row["hit_max_new_tokens"]) for row in outputs),
        "accuracy_metrics": None,
        "accuracy_metrics_reason": "no human-validated Ground Truth in this audit",
    }
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(error, ensure_ascii=False) + "\n" for error in errors), encoding="utf-8",
    )
    (run / "run.log").write_text(
        f"status=completed\nitems={len(outputs)}\nschema_valid={len(valid)}\nscope=engineering_audit_no_ground_truth\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
