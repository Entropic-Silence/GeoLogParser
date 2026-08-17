#!/usr/bin/env python3
"""Evaluate PaddleOCR-VL's official table-recognition mode on California Gold.

This is intentionally a document-specialist baseline, not an image-to-JSON
prompting variant.  The model receives its published ``Table Recognition:``
task prompt and its HTML-like output is decoded only when an explicit top and
bottom column header is present.  No interval is inferred from row order,
thickness, neighbouring rows, or the reference record.
"""

from __future__ import annotations

import argparse
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
from geologparser.vlm.mineru_tables import decode_mineru_intervals


ROOT = Path(__file__).resolve().parents[1]
TABLE_PROMPT = "Table Recognition:"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def reference_intervals(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "top_depth_m": float(item["top_depth_ft"]) * 0.3048,
            "bottom_depth_m": float(item["bottom_depth_ft"]) * 0.3048,
            "thickness_m": float(item["thickness_ft"]) * 0.3048,
            "lithology_normalized": str(item.get("lithology_raw") or "").strip().lower(),
        }
        for item in source["intervals"]
    ]


def table_markup_from_output(text: str) -> str:
    """Keep only the generated table payload passed to the fixed decoder."""
    first = text.find("<table")
    last = text.rfind("</table>")
    if first < 0 or last < first:
        return ""
    return text[first : last + len("</table>")]


def encode_page(processor: Any, image: Any, *, max_pixels: int) -> Any:
    messages = [{
        "role": "user",
        "content": [{"type": "image", "image": image}, {"type": "text", "text": TABLE_PROMPT}],
    }]
    minimum_pixels = getattr(processor.image_processor, "min_pixels", None)
    if minimum_pixels is None:
        minimum_pixels = getattr(processor.image_processor, "size", {}).get("shortest_edge", 112896)
    return processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        images_kwargs={"size": {"shortest_edge": minimum_pixels, "longest_edge": max_pixels}},
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--page-manifest", type=Path, required=True)
    parser.add_argument("--model-config", type=Path, required=True)
    parser.add_argument("--protocol-config", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--limit-pages", type=int)
    parser.add_argument("--scale-to-m", type=float, default=0.3048)
    arguments = parser.parse_args()
    if arguments.limit_pages is not None and arguments.limit_pages < 1:
        raise ValueError("--limit-pages must be positive")

    model_config = json.loads(arguments.model_config.read_text(encoding="utf-8"))
    sources = {str(row["record_id"]): row for row in load_jsonl(arguments.source_manifest)}
    pages = load_jsonl(arguments.page_manifest)
    if arguments.limit_pages is not None:
        pages = pages[:arguments.limit_pages]
    selected = {str(row["record_id"]) for row in pages}
    if not selected <= sources.keys():
        raise ValueError("page manifest contains records outside source manifest")
    sources = {key: sources[key] for key in selected}

    try:
        import torch
        from PIL import Image
        from transformers import AutoModelForImageTextToText, AutoProcessor
    except ImportError as exc:
        raise RuntimeError("PaddleOCR-VL baseline requires its locked local runtime") from exc
    if not torch.cuda.is_available():
        raise RuntimeError("PaddleOCR-VL baseline requires an available CUDA GPU")
    model_path = Path(model_config["local_path"])
    if not model_path.is_dir():
        raise FileNotFoundError(model_path)

    torch.cuda.set_device(arguments.device)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(arguments.device)
    processor = AutoProcessor.from_pretrained(str(model_path), trust_remote_code=False, local_files_only=True)
    model = AutoModelForImageTextToText.from_pretrained(
        str(model_path), dtype=torch.bfloat16, trust_remote_code=False, local_files_only=True,
    ).to(arguments.device).eval()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": arguments.source_manifest.stem,
        "split_version": "all_pages_of_frozen_manifest",
        "model": model_config["model_id"],
        "model_revision": model_config["model_revision"],
        "prompt_version": "official_table_recognition_v001",
        "seed": 0,
        "hardware": {"device": model_config["hardware"], "gpu_used": True},
        "software": {"python": platform.python_version(), "torch": torch.__version__},
        "config": {
            "source_manifest_sha256": file_sha256(arguments.source_manifest),
            "page_manifest_sha256": file_sha256(arguments.page_manifest),
            "model_config_sha256": file_sha256(arguments.model_config),
            "protocol_config_sha256": file_sha256(arguments.protocol_config),
            "source_unit": "ft",
            "metres_per_source_unit": arguments.scale_to_m,
            "prediction_reference_conditioning": "none",
            "task_prompt": TABLE_PROMPT,
            "decoder": model_config["decoder"],
            "boundary_tolerance_m": 0.05,
            "max_new_tokens": int(model_config["max_new_tokens"]),
            "max_pixels": int(model_config["max_pixels"]),
        },
        "started_utc": datetime.now(timezone.utc).isoformat(),
    })

    page_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, page in enumerate(pages, 1):
        image_path = Path(str(page["image_path"]))
        row: dict[str, Any] = {
            "page_key": image_path.stem,
            "record_id": str(page["record_id"]),
            "page_index": page.get("page_index"),
            "image_path": str(image_path),
            "image_sha256": file_sha256(image_path),
            "parse_status": "request_failed",
        }
        started = time.perf_counter()
        try:
            with Image.open(image_path) as page_image:
                inputs = encode_page(processor, page_image.convert("RGB"), max_pixels=int(model_config["max_pixels"])).to(arguments.device)
            prompt_tokens = int(inputs["input_ids"].shape[-1])
            with torch.inference_mode():
                generated = model.generate(**inputs, max_new_tokens=int(model_config["max_new_tokens"]), do_sample=False)
            output = processor.decode(generated[0][prompt_tokens:-1], skip_special_tokens=True)
            markup = table_markup_from_output(output)
            intervals, rejected, table_count = decode_mineru_intervals(
                [{"type": "table", "content": markup}], scale_to_m=arguments.scale_to_m,
            )
            row.update({
                "parse_status": "table_decoded",
                "latency_seconds": time.perf_counter() - started,
                "raw_response": output,
                "table_markup_present": bool(markup),
                "intervals": intervals,
                "rejected_numeric_row_count": rejected,
                "table_element_count": table_count,
            })
        except Exception as exc:
            row["latency_seconds"] = time.perf_counter() - started
            row["error"] = f"{type(exc).__name__}: {exc}"
            errors.append({"page_key": row["page_key"], "record_id": row["record_id"], "error_type": "paddleocr_vl_page_failure", "message": row["error"]})
        page_rows.append(row)
        print(json.dumps({"progress": f"{index}/{len(pages)}", "page_key": row["page_key"], "status": row["parse_status"]}, ensure_ascii=False), flush=True)

    pages_by_record: dict[str, list[dict[str, Any]]] = {key: [] for key in sources}
    for row in page_rows:
        pages_by_record[row["record_id"]].append(row)
    documents: list[dict[str, Any]] = []
    reference_all: list[list[dict[str, Any]]] = []
    prediction_all: list[list[dict[str, Any]]] = []
    for record_id, source in sources.items():
        record_pages = sorted(pages_by_record[record_id], key=lambda row: (row.get("page_index") or 0, row["page_key"]))
        prediction = [interval for page in record_pages if page["parse_status"] == "table_decoded" for interval in page.get("intervals", [])]
        reference = reference_intervals(source)
        matches, missing, extra = match_intervals_by_boundaries(reference, prediction, tolerance_m=0.05)
        documents.append({
            "record_id": record_id,
            "page_count": len(record_pages),
            "decoded_page_count": sum(page["parse_status"] == "table_decoded" for page in record_pages),
            "predicted_intervals": prediction,
            "reference_intervals": reference,
            "matched_interval_count": len(matches),
            "unmatched_reference_indices": missing,
            "unmatched_prediction_indices": extra,
            "document_boundary_exact": len(matches) == len(reference) == len(prediction) and not missing and not extra,
        })
        reference_all.append(reference)
        prediction_all.append(prediction)
    interval_metrics = boundary_matched_interval_metrics(reference_all, prediction_all, tolerance_m=0.05)
    metrics = {
        "scope": "frozen PaddleOCR-VL official-table-recognition California Gold benchmark evaluation",
        "reference_ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION",
        "prediction_reference_conditioning": "none",
        "document_count": len(documents),
        "page_count": len(page_rows),
        "decoded_page_count": sum(row["parse_status"] == "table_decoded" for row in page_rows),
        "documents_with_predictions": sum(bool(row["predicted_intervals"]) for row in documents),
        "zero_output_document_rate": sum(not row["predicted_intervals"] for row in documents) / len(documents),
        "reference_interval_count": sum(len(row["reference_intervals"]) for row in documents),
        "predicted_interval_count": sum(len(row["predicted_intervals"]) for row in documents),
        "rejected_numeric_row_count": sum(int(row.get("rejected_numeric_row_count") or 0) for row in page_rows),
        "document_boundary_exact": {
            "numerator": sum(bool(row["document_boundary_exact"]) for row in documents),
            "denominator": len(documents),
            "value": sum(bool(row["document_boundary_exact"]) for row in documents) / len(documents),
        },
        "interval_metrics": {name: value.to_dict() for name, value in interval_metrics.items()},
        "latency_seconds_total": sum(float(row.get("latency_seconds") or 0.0) for row in page_rows),
        "latency_seconds_per_page": sum(float(row.get("latency_seconds") or 0.0) for row in page_rows) / len(page_rows),
        "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(arguments.device)),
        "limitations": [
            "PaddleOCR-VL runs the official table-recognition task; the task is not a generalist JSON prompt.",
            "The shared decoder performs source-unit conversion but does not infer, complete, merge, or reorder intervals.",
        ],
    }
    write_jsonl(run / "page_predictions.jsonl", page_rows)
    write_jsonl(run / "predictions.jsonl", documents)
    write_jsonl(run / "errors.jsonl", errors)
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(f"status=completed\npages={len(page_rows)}\ndocuments={len(documents)}\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
