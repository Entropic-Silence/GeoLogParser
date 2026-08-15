#!/usr/bin/env python3
"""Aggregate page-level VLM outputs and score them on California Gold."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from datetime import date
from pathlib import Path

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest

ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--split", type=Path)
    parser.add_argument("--prediction-run", type=Path, action="append", required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    manifest_rows = load_jsonl(args.manifest)
    if args.split:
        split = json.loads(args.split.read_text(encoding="utf-8"))
        selected = set(split["test"])
        manifest_rows = [row for row in manifest_rows if row["record_id"] in selected]
        if not manifest_rows:
            raise ValueError("split selected no records from manifest")
    manifest = {row["record_id"]: row for row in manifest_rows}
    wall_started = time.perf_counter()
    pages = []
    seen = set()
    for run_path in args.prediction_run:
        for row in load_jsonl(run_path / "predictions.jsonl"):
            # Use the rendered page stem as the canonical page key.  This
            # keeps aggregation correct even for legacy audit shards whose
            # item_id was the repeated source record id.
            page_stem = Path(row["image_path"]).stem
            item_id = page_stem
            if item_id in seen:
                raise ValueError(f"duplicate page prediction: {item_id}")
            seen.add(item_id)
            record_id = item_id.rsplit("_p", 1)[0]
            if record_id not in manifest:
                raise ValueError(f"prediction outside manifest: {item_id}")
            pages.append(row | {"item_id": item_id, "record_id": record_id})
    expected_pages = {
        f'{record_id}_p{page:03d}'
        for record_id, row in manifest.items()
        for page in range(1, int(row.get("pdf_pages", 1)) + 1)
    }
    if seen != expected_pages:
        missing = sorted(expected_pages - seen)
        extra = sorted(seen - expected_pages)
        raise ValueError(f"page coverage mismatch; missing={missing[:5]} extra={extra[:5]}")
    grouped = {record_id: [] for record_id in manifest}
    for row in pages:
        grouped[row["record_id"]].append(row)
    references = []
    predictions = []
    output_rows = []
    for record_id, source in manifest.items():
        reference = [
            {
                "top_depth_m": float(interval["top_depth_ft"]) * 0.3048,
                "bottom_depth_m": float(interval["bottom_depth_ft"]) * 0.3048,
                "thickness_m": float(interval["thickness_ft"]) * 0.3048,
                "lithology_normalized": str(interval.get("lithology_raw") or "").strip().lower(),
            }
            for interval in source["intervals"]
        ]
        page_rows = sorted(grouped[record_id], key=lambda row: row["item_id"])
        predicted = []
        valid_pages = 0
        for page in page_rows:
            if page.get("parse_status") == "schema_valid" and page.get("record"):
                valid_pages += 1
                predicted.extend(page["record"].get("intervals", []))
        matches, missing, extra = match_intervals_by_boundaries(reference, predicted, tolerance_m=0.05)
        lithology_exact = sum(
            str(predicted[p]["lithology_raw"] or "").strip().lower() == str(reference[r].get("lithology_normalized") or "").strip().lower()
            for r, p in matches
            if predicted[p].get("lithology_raw") is not None
        )
        references.append(reference)
        predictions.append(predicted)
        output_rows.append({
            "record_id": record_id,
            "page_count": len(page_rows),
            "schema_valid_page_count": valid_pages,
            "predicted_intervals": predicted,
            "reference_intervals": reference,
            "matched_interval_count": len(matches),
            "matched_lithology_exact_count": lithology_exact,
            "unmatched_reference_indices": missing,
            "unmatched_prediction_indices": extra,
            "document_full_exact": len(matches) == len(reference) == len(predicted) and not missing and not extra,
        })
    metrics_intervals = boundary_matched_interval_metrics(references, predictions, tolerance_m=0.05)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": "california_wcr_gold_v001",
        "split_version": "california_wcr_gold_split_v001_test",
        "model": "Qwen3-VL-4B-Instruct_page_aggregate",
        "model_revision": "ebb281ec70b05090aa6165b016eac8ec08e71b17",
        "prompt_version": "vlm_extract_v001",
        "seed": 0,
        "hardware": {"device": "cuda_multi_gpu", "gpu_used": True},
        "software": {"python": platform.python_version()},
        "config": {
            "ground_truth_sha256": file_sha256(args.manifest),
            "prediction_runs": [str(path) for path in args.prediction_run],
            "prediction_reference_conditioning": "none",
            "aggregation": "concatenate_schema_valid_page_intervals_by_record_in_page_order",
            "unit_conversion": "published_feet_bls_to_meters_multiply_0.3048",
            "reference_scope": "USGS-published verbatim manual transcriptions from DWR WCR images",
        },
    })
    metrics = {
        "scope": "human-GT benchmark evaluation",
        "reference_ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION",
        "prediction_reference_conditioning": "none",
        "document_count": len(output_rows),
        "page_count": len(pages),
        "county_count": len({source.get("county") for source in manifest.values() if source.get("county")}),
        "latency_seconds_total": sum(float(row.get("latency_seconds") or 0.0) for row in pages),
        # This is aggregation wall time, not inference wall time.  Inference
        # latency is retained separately from each page prediction and summed
        # below so parallel shard execution is not misrepresented.
        "latency_seconds_per_document_wall": (time.perf_counter() - wall_started) / len(output_rows),
        "prediction_generation_latency_seconds_total": sum(float(row.get("latency_seconds") or 0.0) for row in pages),
        "prediction_generation_latency_seconds_per_document": (
            sum(float(row.get("latency_seconds") or 0.0) for row in pages) / len(output_rows)
            if output_rows else 0.0
        ),
        "wall_time_seconds": time.perf_counter() - wall_started,
        "documents_with_predictions": sum(bool(row["predicted_intervals"]) for row in output_rows),
        "documents_with_schema_valid_pages": sum(row["schema_valid_page_count"] > 0 for row in output_rows),
        "reference_interval_count": sum(len(x) for x in references),
        "predicted_interval_count": sum(len(x) for x in predictions),
        "matched_lithology_exact": {
            "numerator": sum(row["matched_lithology_exact_count"] for row in output_rows),
            "denominator": sum(row["matched_interval_count"] for row in output_rows),
            "value": (sum(row["matched_lithology_exact_count"] for row in output_rows) / sum(row["matched_interval_count"] for row in output_rows)) if sum(row["matched_interval_count"] for row in output_rows) else None,
        },
        "matched_lithology_exact_count": sum(row["matched_lithology_exact_count"] for row in output_rows),
        "document_boundary_exact_count": sum(bool(row["document_full_exact"]) for row in output_rows),
        "document_boundary_exact": {
            "numerator": sum(bool(row["document_full_exact"]) for row in output_rows),
            "denominator": len(output_rows),
            "value": sum(bool(row["document_full_exact"]) for row in output_rows) / len(output_rows),
        },
        "interval_metrics": {name: value.to_dict() for name, value in metrics_intervals.items()},
        "limitations": [
            "Page aggregation preserves only schema-valid VLM pages and does not repair or deduplicate intervals.",
            "The prompt requests metres while the published reference is feet; the benchmark converts only the reference feet to metres.",
        ],
    }
    (run / "predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps({"record_id": row["record_id"], "error_type": "missing_reference_interval", "reference_index": index}, ensure_ascii=False) + "\n" for row in output_rows for index in row["unmatched_reference_indices"]), encoding="utf-8")
    (run / "run.log").write_text(f"status=completed\ndocuments={len(output_rows)}\npages={len(pages)}\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
