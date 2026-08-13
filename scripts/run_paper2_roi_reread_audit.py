#!/usr/bin/env python3
"""Run a hash-traceable OCR+VLM ROI audit without using auto labels as GT."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from importlib.metadata import version
from pathlib import Path
import subprocess

from geologparser.annotation import validate_annotation
from geologparser.annotation_reread import run_annotation_reread
from geologparser.experiment import create_run_directory
from geologparser.ocr import TesseractOCRAdapter
from geologparser.rereading import VLMNumericROIAdapter
from geologparser.vlm import Qwen3VLTransformersAdapter


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


def git_value(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument(
        "--cases", type=Path,
        default=ROOT / "configs/experiments/paper2_roi_reread_unipd_v001.jsonl",
    )
    parser.add_argument(
        "--prompt", type=Path,
        default=ROOT / "prompts/constraint_reread_numeric_v001.md",
    )
    parser.add_argument("--prompt-version", default="constraint_reread_numeric_v001")
    parser.add_argument("--dataset-version", default="unipd_levee_geotech_auto_roi_v001")
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--model-path", type=Path, default=MODEL_PATH)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--min-pixels", type=int, default=128 * 28 * 28)
    parser.add_argument("--max-pixels", type=int, default=512 * 28 * 28)
    parser.add_argument("--padding-pixels", type=int, default=12)
    parser.add_argument("--scale", type=float, default=3.0)
    arguments = parser.parse_args()

    if os.environ.get("CUDA_VISIBLE_DEVICES") in (None, "", "-1"):
        raise RuntimeError("set CUDA_VISIBLE_DEVICES to one explicitly selected, paused GPU")
    if git_value("status", "--porcelain"):
        raise RuntimeError("refusing to run an immutable audit from a dirty Git worktree")
    cases = [
        json.loads(line) for line in arguments.cases.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not cases:
        raise ValueError("ROI case manifest is empty")
    prompt = arguments.prompt.read_text(encoding="utf-8")
    resolved_cases = []
    for case in cases:
        annotation_path = Path(case["annotation_path"])
        annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
        validate_annotation(annotation)
        panel_path = Path(annotation["panel"]["rendered_path"])
        panel_sha256 = sha256(panel_path)
        declared_panel_sha256 = annotation["panel"].get("rendered_sha256")
        if declared_panel_sha256 is not None and declared_panel_sha256 != panel_sha256:
            raise ValueError(f"panel hash mismatch for {case['case_id']}")
        resolved_cases.append((case, annotation_path, annotation, panel_path, panel_sha256))

    import torch

    device = torch.cuda.get_device_properties(0)
    created_at = datetime.now(timezone.utc)
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": git_value("rev-parse", "HEAD"),
        "date": created_at.date().isoformat(),
        "dataset_version": arguments.dataset_version,
        "split_version": "public_engineering_audit_no_training_no_ground_truth",
        "model": f"tesseract_plus_{MODEL_ID}",
        "model_revision": f"tesseract_system_package+{MODEL_REVISION}",
        "prompt_version": arguments.prompt_version,
        "seed": None,
        "hardware": {
            "device": "cuda:0",
            "visible_physical_gpu": os.environ["CUDA_VISIBLE_DEVICES"],
            "gpu_name": device.name,
            "vram_bytes": device.total_memory,
        },
        "software": {
            "python": platform.python_version(),
            "torch": version("torch"),
            "transformers": version("transformers"),
            "accelerate": version("accelerate"),
            "tesseract": subprocess.run(
                ["tesseract", "--version"], text=True, capture_output=True, check=True,
            ).stdout.splitlines()[0],
        },
        "config": {
            "cases_path": str(arguments.cases.resolve().relative_to(ROOT)),
            "cases_sha256": sha256(arguments.cases),
            "prompt_path": str(arguments.prompt.resolve().relative_to(ROOT)),
            "prompt_sha256": sha256(arguments.prompt),
            "model_path": str(arguments.model_path),
            "max_new_tokens": arguments.max_new_tokens,
            "min_pixels": arguments.min_pixels,
            "max_pixels": arguments.max_pixels,
            "padding_pixels": arguments.padding_pixels,
            "scale": arguments.scale,
            "scope": "public auto-proposal ROI engineering audit; no Ground Truth accuracy claim",
        },
    })
    input_manifest = {
        "manifest_schema_version": "paper2_roi_reread_inputs_v001",
        "scope": "public auto annotations; not Ground Truth",
        "source_case_config": str(arguments.cases.resolve().relative_to(ROOT)),
        "source_case_config_sha256": sha256(arguments.cases),
        "cases": [
            {
                "case_id": case["case_id"],
                "field_path": case["field_path"],
                "annotation_path": str(annotation_path),
                "annotation_sha256": sha256(annotation_path),
                "annotation_status": annotation["annotation_status"],
                "panel_path": str(panel_path),
                "panel_sha256": panel_sha256,
            }
            for case, annotation_path, annotation, panel_path, panel_sha256 in resolved_cases
        ],
    }
    (run / "input_manifest.json").write_text(
        json.dumps(input_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    vlm = Qwen3VLTransformersAdapter(
        arguments.model_path,
        model_id=MODEL_ID,
        model_revision=MODEL_REVISION,
        max_new_tokens=arguments.max_new_tokens,
        min_pixels=arguments.min_pixels,
        max_pixels=arguments.max_pixels,
    )
    readers = [
        TesseractOCRAdapter(language="eng", psm=7),
        VLMNumericROIAdapter(
            vlm, prompt, prompt_version=arguments.prompt_version,
            name="qwen3vl4b_numeric_roi",
        ),
    ]
    predictions = []
    errors = []
    with (run / "predictions.jsonl").open("w", encoding="utf-8") as stream:
        for case, annotation_path, annotation, _, _ in resolved_cases:
            try:
                result = run_annotation_reread(
                    annotation, case["field_path"], readers, run / "case_artifacts",
                    padding_pixels=arguments.padding_pixels, scale=arguments.scale,
                )
                row = {
                    "case_id": case["case_id"],
                    "field_path": case["field_path"],
                    "annotation_id": annotation["annotation_id"],
                    "annotation_sha256": sha256(annotation_path),
                    "annotation_status": annotation["annotation_status"],
                    "ground_truth_used": False,
                    "result": result,
                }
                predictions.append(row)
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
            except Exception as exc:
                errors.append({
                    "case_id": case.get("case_id"),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                })

    agreement_cases = 0
    for row in predictions:
        sources_by_value: dict[str, set[str]] = {}
        for score in row["result"]["decision"]["scores"]:
            candidate = score["candidate"]
            sources_by_value.setdefault(str(candidate["value"]), set()).add(candidate["source"])
        agreement_cases += int(any(len(sources) > 1 for sources in sources_by_value.values()))
    vlm_audits = [
        row["result"]["reader_audits"]["qwen3vl4b_numeric_roi"] for row in predictions
    ]
    metrics = {
        "scope": "public auto-proposal ROI engineering audit; no Ground Truth accuracy claim",
        "case_count": len(cases),
        "completed_case_count": len(predictions),
        "failed_case_count": len(errors),
        "vlm_schema_valid_count": sum(audit["parse_status"] == "valid" for audit in vlm_audits),
        "vlm_uncertain_count": sum(audit.get("uncertain") is True for audit in vlm_audits),
        "cross_reader_numeric_agreement_case_count": agreement_cases,
        "accept_proposal_count": sum(
            row["result"]["decision"]["status"] == "ACCEPT_PROPOSAL" for row in predictions
        ),
        "needs_review_count": sum(
            row["result"]["decision"]["status"] == "NEEDS_REVIEW" for row in predictions
        ),
        "vlm_latency_total_seconds": sum(audit["latency_seconds"] for audit in vlm_audits),
        "vlm_latency_mean_seconds_per_roi": (
            sum(audit["latency_seconds"] for audit in vlm_audits) / len(vlm_audits)
            if vlm_audits else None
        ),
        "peak_gpu_memory_bytes": max(
            (audit.get("peak_gpu_memory_bytes") or 0 for audit in vlm_audits), default=0,
        ),
        "accuracy_metrics": None,
        "accuracy_metrics_reason": "all source annotations remain auto; no human Ground Truth",
        "false_correction_rate": None,
        "false_correction_rate_reason": "requires human Ground Truth",
    }
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(error, ensure_ascii=False) + "\n" for error in errors),
        encoding="utf-8",
    )
    status = "failed" if errors else "completed"
    (run / "run.log").write_text(
        f"status={status}\ncases={len(cases)}\ncompleted={len(predictions)}\n"
        "scope=public_auto_proposal_roi_audit_no_ground_truth\n",
        encoding="utf-8",
    )
    if errors:
        raise RuntimeError(f"{len(errors)} ROI case(s) failed; run is not indexable")
    print(run)


if __name__ == "__main__":
    main()
