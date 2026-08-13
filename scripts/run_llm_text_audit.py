#!/usr/bin/env python3
"""Run B2 direct/OCR text to local LLM JSON as an unannotated audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path

from geologparser.constraints import load_engine_config
from geologparser.experiment import create_run_directory
from geologparser.llm import Qwen3VLTextTransformersAdapter
from geologparser.pdf import PyMuPDFPanelTextAdapter
from geologparser.schema import validate_record
from geologparser.result_index import file_sha256
from geologparser.vlm import compact_payload_to_record, parse_json_object


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONSTRAINT_CONFIG = ROOT / "configs/constraints/default_v001.yaml"
MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"
MODEL_PATH = Path("/data/GeoLogParser/models/huggingface/Qwen3-VL-4B-Instruct")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--prompt", type=Path, default=ROOT / "prompts/llm_extract_v001.md")
    parser.add_argument("--prompt-version", default="llm_extract_v001")
    parser.add_argument("--model-path", type=Path, default=MODEL_PATH)
    parser.add_argument("--max-new-tokens", type=int, default=1536)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--constraint-config", type=Path, default=DEFAULT_CONSTRAINT_CONFIG)
    arguments = parser.parse_args()
    constraint_engine = load_engine_config(arguments.constraint_config)
    if os.environ.get("CUDA_VISIBLE_DEVICES") in (None, "", "-1"):
        raise RuntimeError("set CUDA_VISIBLE_DEVICES to one explicitly selected, paused GPU")
    import torch

    items = [json.loads(line) for line in arguments.manifest.read_text(encoding="utf-8").splitlines() if line]
    prompt = arguments.prompt.read_text(encoding="utf-8")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    device = torch.cuda.get_device_properties(0)
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id, "git_commit": commit, "date": "2026-08-12",
        "dataset_version": arguments.dataset_version,
        "split_version": "engineering_audit_no_training_no_ground_truth",
        "model": MODEL_ID, "model_revision": MODEL_REVISION,
        "prompt_version": arguments.prompt_version, "seed": None,
        "hardware": {"device": "cuda:0", "visible_physical_gpu": os.environ["CUDA_VISIBLE_DEVICES"], "gpu_name": device.name, "vram_bytes": device.total_memory},
        "software": {"python": platform.python_version(), "torch": version("torch"), "transformers": version("transformers")},
        "config": {
            "model_path": str(arguments.model_path), "manifest_path": str(arguments.manifest),
            "manifest_sha256": sha256(arguments.manifest), "prompt_path": str(arguments.prompt),
            "prompt_sha256": sha256(arguments.prompt), "max_new_tokens": arguments.max_new_tokens,
            "input_channel": "positioned native PDF text flattened in block order; no image",
            "constraint_config_path": str(arguments.constraint_config.resolve()),
            "constraint_config_sha256": file_sha256(arguments.constraint_config),
            "scope": "public unannotated B2 engineering audit; no accuracy claim",
        },
    })
    text_adapter = PyMuPDFPanelTextAdapter()
    model = Qwen3VLTextTransformersAdapter(
        arguments.model_path, model_id=MODEL_ID, model_revision=MODEL_REVISION,
        max_new_tokens=arguments.max_new_tokens,
    )
    rows, errors = [], []
    with (run / "predictions.jsonl").open("w", encoding="utf-8") as stream:
        for item in items:
            source = Path(item["source_path"])
            regions = text_adapter.extract_panel(source, int(item["source_page"]), tuple(item["normalized_bbox"]))
            text_input = "\n".join(region.text for region in regions)
            generation = model.generate(text_input, prompt, prompt_version=arguments.prompt_version)
            row = {
                "item_id": item["panel_id"], "source_path": str(source),
                "source_text_sha256": hashlib.sha256(text_input.encode()).hexdigest(),
                "text_region_count": len(regions), "input_tokens": generation.input_tokens,
                "raw_response": generation.text, "latency_seconds": generation.latency_seconds,
                "output_tokens": generation.output_tokens, "hit_max_new_tokens": generation.hit_max_new_tokens,
                "peak_gpu_memory_bytes": generation.peak_gpu_memory_bytes,
                "generation_config": dict(generation.generation_config), "parse_status": "failed",
                "record": None, "constraints": [],
            }
            try:
                payload = parse_json_object(generation.text)
                record = compact_payload_to_record(
                    payload, document_id=item["panel_id"], source_file=source,
                    source_sha256=item["source_sha256"], extraction_method="llm",
                )
                record["document"]["metadata"].update({
                    "project_id": item.get("project_id"), "template_id": item.get("template_id"),
                    "source_id": arguments.dataset_version,
                })
                validate_record(record)
                constraints = constraint_engine.evaluate(record)
                row["record"] = record
                row["constraints"] = [result.__dict__ | {"violations": [v.__dict__ for v in result.violations]} for result in constraints]
                row["parse_status"] = "schema_valid"
            except Exception as exc:
                row["parse_error"] = f"{type(exc).__name__}: {exc}"
                errors.append({"item_id": item["panel_id"], "error_type": "llm_structured_parse_failure", "message": row["parse_error"]})
            rows.append(row)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
    valid = [row for row in rows if row["parse_status"] == "schema_valid"]
    metrics = {
        "scope": "public unannotated B2 engineering audit; no Ground Truth accuracy claim",
        "items": len(rows), "schema_valid_responses": len(valid),
        "structured_parse_rate": len(valid) / len(rows),
        "emitted_intervals": sum(len(row["record"]["intervals"]) for row in valid),
        "constraint_evaluations": sum(sum(x["evaluated_count"] for x in row["constraints"]) for row in valid),
        "constraint_violations": sum(sum(len(x["violations"]) for x in row["constraints"]) for row in valid),
        "input_tokens_total": sum(row["input_tokens"] or 0 for row in rows),
        "latency_total_seconds": sum(row["latency_seconds"] for row in rows),
        "latency_mean_seconds_per_page": sum(row["latency_seconds"] for row in rows) / len(rows),
        "peak_gpu_memory_bytes": max(row["peak_gpu_memory_bytes"] or 0 for row in rows),
        "responses_hitting_max_new_tokens": sum(bool(row["hit_max_new_tokens"]) for row in rows),
        "accuracy_metrics": None,
        "accuracy_metrics_reason": "all source annotations remain auto; no human-validated Ground Truth",
    }
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps(row) + "\n" for row in errors), encoding="utf-8")
    (run / "run.log").write_text(f"status=completed\nitems={len(rows)}\nschema_valid={len(valid)}\nscope=audit_no_gt\n", encoding="utf-8")
    print(run)


if __name__ == "__main__":
    main()
