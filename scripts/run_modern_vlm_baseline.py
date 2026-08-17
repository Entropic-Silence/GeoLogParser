#!/usr/bin/env python3
"""Run one frozen direct-VLM baseline on rendered California Gold pages.

This script intentionally performs no OCR repair, interval completion, or
deduplication.  It measures the direct page-to-source-unit JSON behaviour of a
model before GeoLogParser's evidence-aware parsing and risk policy are applied.
It is resumable at page granularity through ``--resume-page-predictions``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest
from geologparser.vlm import AnthropicMessagesVLMAdapter, OpenAICompatibleVLMAdapter, VLMAdapter, parse_json_object


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def normalized_intervals(payload: Mapping[str, Any], *, scale_to_m: float) -> tuple[list[dict[str, Any]], int]:
    """Convert only well-formed source-unit interval objects to metres."""
    raw_intervals = payload.get("intervals")
    if not isinstance(raw_intervals, list):
        return [], 0
    valid: list[dict[str, Any]] = []
    invalid = 0
    for raw in raw_intervals:
        if not isinstance(raw, Mapping):
            invalid += 1
            continue
        top = parse_number(raw.get("top_depth_source"))
        bottom = parse_number(raw.get("bottom_depth_source"))
        if top is None or bottom is None or top < 0 or bottom <= top:
            invalid += 1
            continue
        lithology = raw.get("lithology_raw")
        valid.append({
            "top_depth_m": top * scale_to_m,
            "bottom_depth_m": bottom * scale_to_m,
            "thickness_m": (bottom - top) * scale_to_m,
            "lithology_raw": lithology.strip() if isinstance(lithology, str) and lithology.strip() else None,
        })
    return valid, invalid


def references_for(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for interval in source["intervals"]:
        if "top_depth_m" in interval and "bottom_depth_m" in interval:
            top = float(interval["top_depth_m"])
            bottom = float(interval["bottom_depth_m"])
            thickness = float(interval.get("thickness_m", bottom - top))
        elif "top_depth_ft" in interval and "bottom_depth_ft" in interval:
            top = float(interval["top_depth_ft"]) * 0.3048
            bottom = float(interval["bottom_depth_ft"]) * 0.3048
            thickness = float(interval.get("thickness_ft", float(interval["bottom_depth_ft"]) - float(interval["top_depth_ft"]))) * 0.3048
        else:
            raise ValueError(f"reference interval lacks recognised metre or foot depth fields: {interval}")
        converted.append({
            "top_depth_m": top,
            "bottom_depth_m": bottom,
            "thickness_m": thickness,
            "lithology_normalized": str(interval.get("lithology_raw") or "").strip().lower(),
        })
    return converted


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def build_adapter(provider: Mapping[str, Any], *, timeout_seconds: float) -> VLMAdapter:
    """Construct only a declared, auditable provider transport."""
    adapter_kind = str(provider.get("adapter", "openai_compatible_chat_completions"))
    common: dict[str, Any] = {
        "base_url": str(provider["base_url"]),
        "model_id": str(provider["model_id"]),
        "model_revision": str(provider["model_revision"]),
        "api_key_env": provider.get("api_key_env"),
        "max_tokens": int(provider.get("max_tokens", 1024)),
        "timeout_seconds": timeout_seconds,
        "temperature": float(provider.get("temperature", 0.0)),
        "request_options": provider.get("request_options"),
    }
    if adapter_kind == "openai_compatible_chat_completions":
        return OpenAICompatibleVLMAdapter(**common)
    if adapter_kind == "anthropic_messages":
        api_key_env = common.pop("api_key_env")
        if not isinstance(api_key_env, str) or not api_key_env:
            raise ValueError("Anthropic adapter requires a non-empty api_key_env")
        return AnthropicMessagesVLMAdapter(
            **common,
            api_key_env=api_key_env,
            anthropic_version=str(provider.get("anthropic_version", "2023-06-01")),
        )
    raise ValueError(f"unsupported modern VLM adapter: {adapter_kind}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--page-manifest", type=Path, required=True)
    parser.add_argument("--provider-config", type=Path, required=True)
    parser.add_argument("--protocol-config", type=Path)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--resume-page-predictions", type=Path)
    parser.add_argument("--limit-pages", type=int)
    parser.add_argument("--scale-to-m", type=float, default=0.3048)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--scope", default="frozen direct-VLM California Gold benchmark evaluation")
    parser.add_argument("--reference-ground-truth-tier", default="GOLD_PUBLISHED_MANUAL_TRANSCRIPTION")
    arguments = parser.parse_args()
    if arguments.limit_pages is not None and arguments.limit_pages < 1:
        raise ValueError("--limit-pages must be positive")
    source_rows = load_jsonl(arguments.source_manifest)
    source_by_id = {str(row["record_id"]): row for row in source_rows}
    if len(source_by_id) != len(source_rows):
        raise ValueError("source manifest contains duplicate record IDs")
    pages = load_jsonl(arguments.page_manifest)
    if not pages:
        raise ValueError("page manifest is empty")
    if any(str(page.get("record_id")) not in source_by_id for page in pages):
        raise ValueError("page manifest contains a record outside the source manifest")
    if arguments.limit_pages is not None:
        pages = pages[:arguments.limit_pages]
    # Some legacy page manifests deliberately contain a pre-registered subset
    # of a larger source manifest. Only documents that have an input page are
    # in scope for this direct-VLM evaluation.
    selected_record_ids = {str(page["record_id"]) for page in pages}
    source_by_id = {record_id: source_by_id[record_id] for record_id in selected_record_ids}
    provider = json.loads(arguments.provider_config.read_text(encoding="utf-8"))
    prompt = arguments.prompt.read_text(encoding="utf-8")
    adapter = build_adapter(provider, timeout_seconds=arguments.timeout_seconds)
    resumed: dict[str, dict[str, Any]] = {}
    if arguments.resume_page_predictions:
        for row in load_jsonl(arguments.resume_page_predictions):
            key = str(row["page_key"])
            resumed[key] = row
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": arguments.source_manifest.stem,
        "split_version": "all_pages_of_frozen_manifest",
        "model": provider["model_id"],
        "model_revision": provider["model_revision"],
        "prompt_version": arguments.prompt.stem,
        "seed": 0,
        "hardware": {"device": provider.get("hardware", "endpoint_managed"), "gpu_used": provider.get("gpu_used")},
        "software": {"python": platform.python_version()},
        "config": {
            "source_manifest_sha256": file_sha256(arguments.source_manifest),
            "page_manifest_sha256": file_sha256(arguments.page_manifest),
            "provider_config_sha256": file_sha256(arguments.provider_config),
            "protocol_config_sha256": file_sha256(arguments.protocol_config) if arguments.protocol_config else None,
            "prompt_sha256": _hash_text(prompt),
            "source_unit": "ft",
            "metres_per_source_unit": arguments.scale_to_m,
            "prediction_reference_conditioning": "none",
            "aggregation": "page_order_concatenation_without_repair_or_deduplication",
            "boundary_tolerance_m": 0.05,
            "resumed_page_count": len(resumed),
        },
        "started_utc": datetime.now(timezone.utc).isoformat(),
    })
    page_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for ordinal, page in enumerate(pages, 1):
        image_path = Path(str(page["image_path"]))
        page_key = image_path.stem
        if page_key in resumed:
            row = resumed[page_key]
            row["resumed"] = True
            page_rows.append(row)
            continue
        row: dict[str, Any] = {
            "page_key": page_key,
            "record_id": str(page["record_id"]),
            "page_index": page.get("page_index"),
            "image_path": str(image_path),
            "image_sha256": file_sha256(image_path),
            "parse_status": "request_failed",
            "resumed": False,
        }
        try:
            generation = adapter.generate([image_path], prompt, prompt_version=arguments.prompt.stem)
            row.update({
                "model_id": generation.model_id,
                "model_revision": generation.model_revision,
                "latency_seconds": generation.latency_seconds,
                "output_tokens": generation.output_tokens,
                "hit_max_new_tokens": generation.hit_max_new_tokens,
                "generation_config": generation.generation_config,
                "raw_response": generation.text,
            })
            payload = parse_json_object(generation.text)
            intervals, invalid_count = normalized_intervals(payload, scale_to_m=arguments.scale_to_m)
            row.update({
                "parse_status": "json_valid",
                "intervals": intervals,
                "raw_interval_count": len(payload.get("intervals", [])) if isinstance(payload.get("intervals"), list) else 0,
                "invalid_numeric_interval_count": invalid_count,
            })
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            errors.append({"page_key": page_key, "record_id": row["record_id"], "error_type": "modern_vlm_page_failure", "message": row["error"]})
        page_rows.append(row)
        print(json.dumps({"progress": f"{ordinal}/{len(pages)}", "page_key": page_key, "status": row["parse_status"]}, ensure_ascii=False), flush=True)
    per_record: dict[str, list[dict[str, Any]]] = {record_id: [] for record_id in source_by_id}
    for row in page_rows:
        per_record[str(row["record_id"])].append(row)
    document_rows: list[dict[str, Any]] = []
    reference_all: list[list[dict[str, Any]]] = []
    prediction_all: list[list[dict[str, Any]]] = []
    for record_id, source in source_by_id.items():
        record_pages = sorted(per_record[record_id], key=lambda row: (row.get("page_index") or 0, row["page_key"]))
        predicted = [interval for row in record_pages if row["parse_status"] == "json_valid" for interval in row.get("intervals", [])]
        reference = references_for(source)
        matches, missing, extra = match_intervals_by_boundaries(reference, predicted, tolerance_m=0.05)
        document_rows.append({
            "record_id": record_id,
            "page_count": len(record_pages),
            "json_valid_page_count": sum(row["parse_status"] == "json_valid" for row in record_pages),
            "predicted_intervals": predicted,
            "reference_intervals": reference,
            "matched_interval_count": len(matches),
            "unmatched_reference_indices": missing,
            "unmatched_prediction_indices": extra,
            "document_boundary_exact": len(matches) == len(reference) == len(predicted) and not missing and not extra,
        })
        reference_all.append(reference)
        prediction_all.append(predicted)
    interval_metrics = boundary_matched_interval_metrics(reference_all, prediction_all, tolerance_m=0.05)
    metrics = {
        "scope": arguments.scope,
        "reference_ground_truth_tier": arguments.reference_ground_truth_tier,
        "prediction_reference_conditioning": "none",
        "document_count": len(document_rows),
        "page_count": len(page_rows),
        "json_valid_page_count": sum(row["parse_status"] == "json_valid" for row in page_rows),
        "json_valid_page_rate": sum(row["parse_status"] == "json_valid" for row in page_rows) / len(page_rows),
        "documents_with_predictions": sum(bool(row["predicted_intervals"]) for row in document_rows),
        "zero_output_document_rate": sum(not row["predicted_intervals"] for row in document_rows) / len(document_rows),
        "reference_interval_count": sum(len(row["reference_intervals"]) for row in document_rows),
        "predicted_interval_count": sum(len(row["predicted_intervals"]) for row in document_rows),
        "invalid_numeric_interval_count": sum(int(row.get("invalid_numeric_interval_count") or 0) for row in page_rows),
        "critical_numeric_invalidity_rate": (
            sum(int(row.get("invalid_numeric_interval_count") or 0) for row in page_rows)
            / sum(int(row.get("raw_interval_count") or 0) for row in page_rows)
            if sum(int(row.get("raw_interval_count") or 0) for row in page_rows) else None
        ),
        "document_boundary_exact": {
            "numerator": sum(bool(row["document_boundary_exact"]) for row in document_rows),
            "denominator": len(document_rows),
            "value": sum(bool(row["document_boundary_exact"]) for row in document_rows) / len(document_rows),
        },
        "interval_metrics": {name: value.to_dict() for name, value in interval_metrics.items()},
        "latency_seconds_total": sum(float(row.get("latency_seconds") or 0.0) for row in page_rows),
        "latency_seconds_per_page": sum(float(row.get("latency_seconds") or 0.0) for row in page_rows) / len(page_rows),
        "responses_hitting_max_new_tokens": sum(bool(row.get("hit_max_new_tokens")) for row in page_rows),
        "limitations": [
            "Direct VLM output is normalized only by deterministic source-unit conversion and range validation.",
            "No OCR candidate, reference interval, post-hoc repair, or deduplication is supplied to the model.",
        ],
    }
    _write_jsonl(run / "page_predictions.jsonl", page_rows)
    _write_jsonl(run / "predictions.jsonl", document_rows)
    _write_jsonl(run / "errors.jsonl", errors)
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(f"status=completed\npages={len(page_rows)}\ndocuments={len(document_rows)}\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
