#!/usr/bin/env python3
"""Run the local Qwen3-VL-4B direct interval baseline on a fixed panel.

The protocol mirrors ``run_modern_vlm_baseline.py``: one rendered page per
request, the frozen source-unit prompt, no OCR/candidate/reference conditioning,
and only deterministic schema/range normalisation before matching.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest
from geologparser.vlm import Qwen3VLTransformersAdapter, parse_json_object


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def references_for(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in source["intervals"]:
        if "top_depth_m" in item:
            top = float(item["top_depth_m"])
            bottom = float(item["bottom_depth_m"])
            thickness = float(item.get("thickness_m", bottom - top))
        elif "top_depth_ft" in item:
            top = float(item["top_depth_ft"]) * 0.3048
            bottom = float(item["bottom_depth_ft"]) * 0.3048
            thickness = float(item.get("thickness_ft", float(item["bottom_depth_ft"]) - float(item["top_depth_ft"]))) * 0.3048
        else:
            raise ValueError(f"reference interval lacks supported units: {item}")
        output.append({
            "top_depth_m": top,
            "bottom_depth_m": bottom,
            "thickness_m": thickness,
            "lithology_normalized": str(item.get("lithology_raw") or "").strip().lower(),
        })
    return output


def predicted_intervals(payload: Mapping[str, Any], scale_to_m: float) -> tuple[list[dict[str, Any]], int]:
    raw = payload.get("intervals")
    if not isinstance(raw, list):
        return [], 0
    output: list[dict[str, Any]] = []
    invalid = 0
    for item in raw:
        if not isinstance(item, Mapping):
            invalid += 1
            continue
        try:
            top = float(item["top_depth_source"])
            bottom = float(item["bottom_depth_source"])
        except (KeyError, TypeError, ValueError):
            invalid += 1
            continue
        if top < 0 or bottom <= top:
            invalid += 1
            continue
        lithology = item.get("lithology_raw")
        output.append({
            "top_depth_m": top * scale_to_m,
            "bottom_depth_m": bottom * scale_to_m,
            "thickness_m": (bottom - top) * scale_to_m,
            "lithology_raw": lithology.strip() if isinstance(lithology, str) and lithology.strip() else None,
        })
    return output, invalid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--page-manifest", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--scale-to-m", type=float, default=0.3048)
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--min-pixels", type=int, default=256 * 28 * 28)
    parser.add_argument("--max-pixels", type=int, default=1280 * 28 * 28)
    parser.add_argument("--limit-pages", type=int)
    args = parser.parse_args()
    if args.limit_pages is not None:
        if args.limit_pages < 1:
            raise ValueError("--limit-pages must be positive")
    sources = {str(row["record_id"]): row for row in load_jsonl(args.source_manifest)}
    pages = load_jsonl(args.page_manifest)
    if args.limit_pages is not None:
        pages = pages[: args.limit_pages]
    if not pages:
        raise ValueError("page manifest is empty")
    selected = {str(row["record_id"]) for row in pages}
    if not selected <= sources.keys():
        raise ValueError("page manifest contains records outside source manifest")
    sources = {key: sources[key] for key in selected}
    prompt = args.prompt.read_text(encoding="utf-8")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    import torch
    adapter = Qwen3VLTransformersAdapter(
        args.model_path,
        model_id=args.model_id,
        model_revision=args.model_revision,
        max_new_tokens=args.max_new_tokens,
        min_pixels=args.min_pixels,
        max_pixels=args.max_pixels,
    )
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": args.source_manifest.stem,
        "split_version": "fixed_source_shift_panel",
        "model": args.model_id,
        "model_revision": args.model_revision,
        "prompt_version": args.prompt.stem,
        "seed": 0,
        "hardware": {"device": "local_RTX_5090", "gpu_used": True, "visible_device": "CUDA_VISIBLE_DEVICES=0"},
        "software": {"python": platform.python_version(), "torch": torch.__version__, "transformers": __import__("transformers").__version__},
        "config": {
            "source_manifest_sha256": file_sha256(args.source_manifest),
            "page_manifest_sha256": file_sha256(args.page_manifest),
            "prompt_sha256": hash_text(prompt),
            "model_path": str(args.model_path),
            "model_id": args.model_id,
            "model_revision": args.model_revision,
            "source_unit_conversion": args.scale_to_m,
            "boundary_tolerance_m": 0.05,
            "rendering": "inherited frozen page manifests; 200 DPI lossless PNG",
            "decoding": {"temperature": 0.0, "top_p": "not applicable; greedy", "max_new_tokens": args.max_new_tokens, "retries": 0},
            "response_parsing": "strict JSON object; JSON only; no YAML, repair, completion, reorder, or deduplication",
            "conditioning": "none; no OCR, candidate, reference, or source-specific prompt",
        },
        "started_utc": datetime.now(timezone.utc).isoformat(),
    })
    page_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for ordinal, page in enumerate(pages, 1):
        image_path = Path(str(page["image_path"]))
        row: dict[str, Any] = {
            "page_key": image_path.stem,
            "record_id": str(page["record_id"]),
            "page_index": page.get("page_index"),
            "image_path": str(image_path),
            "image_sha256": file_sha256(image_path),
            "parse_status": "request_failed",
        }
        try:
            generation = adapter.generate([image_path], prompt, prompt_version=args.prompt.stem)
            row.update({
                "model_id": generation.model_id,
                "model_revision": generation.model_revision,
                "latency_seconds": generation.latency_seconds,
                "peak_gpu_memory_bytes": generation.peak_gpu_memory_bytes,
                "output_tokens": generation.output_tokens,
                "hit_max_new_tokens": generation.hit_max_new_tokens,
                "generation_config": generation.generation_config,
                "raw_response": generation.text,
            })
            payload = parse_json_object(generation.text)
            intervals, invalid = predicted_intervals(payload, args.scale_to_m)
            row.update({"parse_status": "json_valid", "intervals": intervals, "invalid_numeric_interval_count": invalid, "raw_interval_count": len(payload.get("intervals", [])) if isinstance(payload.get("intervals"), list) else 0})
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            errors.append({"page_key": row["page_key"], "record_id": row["record_id"], "error_type": "local_vlm_page_failure", "message": row["error"]})
        page_rows.append(row)
        print(json.dumps({"progress": f"{ordinal}/{len(pages)}", "page_key": row["page_key"], "status": row["parse_status"]}), flush=True)
    by_record: dict[str, list[dict[str, Any]]] = {key: [] for key in sources}
    for row in page_rows:
        by_record[row["record_id"]].append(row)
    documents: list[dict[str, Any]] = []
    references: list[list[dict[str, Any]]] = []
    predictions: list[list[dict[str, Any]]] = []
    for record_id, source in sources.items():
        record_pages = sorted(by_record[record_id], key=lambda item: (item.get("page_index") or 0, item["page_key"]))
        prediction = [interval for page in record_pages if page["parse_status"] == "json_valid" for interval in page.get("intervals", [])]
        reference = references_for(source)
        matches, missing, extra = match_intervals_by_boundaries(reference, prediction, tolerance_m=0.05)
        documents.append({"record_id": record_id, "page_count": len(record_pages), "predicted_intervals": prediction, "reference_intervals": reference, "matched_interval_count": len(matches), "unmatched_reference_indices": missing, "unmatched_prediction_indices": extra, "document_boundary_exact": len(matches) == len(reference) == len(prediction) and not missing and not extra})
        references.append(reference)
        predictions.append(prediction)
    interval_metrics = boundary_matched_interval_metrics(references, predictions, tolerance_m=0.05)
    raw_count = sum(int(row.get("raw_interval_count") or 0) for row in page_rows)
    metrics = {
        "scope": "fixed modern open-VLM source-shift transport panel",
        "reference_ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION" if "california" in args.source_manifest.stem else "SOURCE_AGREEMENT_REFERENCE",
        "document_count": len(documents), "page_count": len(page_rows),
        "json_valid_page_count": sum(row["parse_status"] == "json_valid" for row in page_rows),
        "json_valid_page_rate": sum(row["parse_status"] == "json_valid" for row in page_rows) / len(page_rows),
        "documents_with_predictions": sum(bool(row["predicted_intervals"]) for row in documents),
        "zero_output_document_rate": sum(not row["predicted_intervals"] for row in documents) / len(documents),
        "reference_interval_count": sum(len(row["reference_intervals"]) for row in documents),
        "predicted_interval_count": sum(len(row["predicted_intervals"]) for row in documents),
        "invalid_numeric_interval_count": sum(int(row.get("invalid_numeric_interval_count") or 0) for row in page_rows),
        "critical_numeric_invalidity_rate": sum(int(row.get("invalid_numeric_interval_count") or 0) for row in page_rows) / raw_count if raw_count else None,
        "document_boundary_exact": {"numerator": sum(bool(row["document_boundary_exact"]) for row in documents), "denominator": len(documents), "value": sum(bool(row["document_boundary_exact"]) for row in documents) / len(documents)},
        "interval_metrics": {name: metric.to_dict() for name, metric in interval_metrics.items()},
        "latency_seconds_total": sum(float(row.get("latency_seconds") or 0.0) for row in page_rows),
        "latency_seconds_per_page": sum(float(row.get("latency_seconds") or 0.0) for row in page_rows) / len(page_rows),
        "peak_gpu_memory_bytes": max(int(row.get("peak_gpu_memory_bytes") or 0) for row in page_rows),
        "limitations": ["Direct page-to-JSON only; no OCR/candidate/reference conditioning, repair, or deduplication.", "Transport comparison is source-shift evidence, not a universal model capability estimate."],
    }
    write_jsonl(run / "page_predictions.jsonl", page_rows)
    write_jsonl(run / "predictions.jsonl", documents)
    write_jsonl(run / "errors.jsonl", errors)
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(f"status=completed\npages={len(page_rows)}\ndocuments={len(documents)}\n", encoding="utf-8")
    metadata = json.loads((run / "run.json").read_text(encoding="utf-8"))
    metadata["completed_utc"] = datetime.now(timezone.utc).isoformat()
    (run / "run.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
