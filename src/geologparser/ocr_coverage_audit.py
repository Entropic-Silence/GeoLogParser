"""Privacy-minimized OCR/extraction coverage audits on rendered review packs."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import resource
import time
from typing import Any, Mapping

from geologparser.constraints import ConstraintEngine
from geologparser.datasets.manifest import sha256_file
from geologparser.experiment import create_run_directory
from geologparser.extraction import extract_structured
from geologparser.ocr import OCRAdapter, TextRegion
from geologparser.schema import validate_record


REQUIRED_REVIEW_ITEM_FIELDS = {
    "review_item_id", "dataset_id", "source_filename", "source_path", "source_page",
    "source_file_sha256", "provisional_content_class", "render_dpi", "rendered_sha256",
}


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    body = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _field_envelopes(record: Mapping[str, Any]):
    for name, envelope in record["borehole"].items():
        yield f"borehole.{name}", envelope
    for index, interval in enumerate(record["intervals"]):
        for name, envelope in interval.items():
            if name != "interval_id":
                yield f"intervals[{index}].{name}", envelope


def _preflight_items(review_pack_root: Path, items: list[dict[str, Any]]) -> None:
    """Verify every selected input before creating a run or invoking OCR."""

    identifiers: set[str] = set()
    for item in items:
        missing = sorted(REQUIRED_REVIEW_ITEM_FIELDS - set(item))
        if missing:
            raise ValueError(f"review item is missing required fields: {', '.join(missing)}")
        identifier = str(item["review_item_id"])
        if not identifier or Path(identifier).name != identifier or identifier in identifiers:
            raise ValueError(f"unsafe or duplicate review_item_id: {identifier!r}")
        identifiers.add(identifier)
        source_path = Path(str(item["source_path"]))
        if not source_path.is_file():
            raise ValueError(f"review source is missing: {identifier}")
        if sha256_file(source_path) != item["source_file_sha256"]:
            raise ValueError(f"review source hash mismatch: {identifier}")
        image_path = review_pack_root / "images" / f"{identifier}.png"
        if not image_path.is_file() or sha256_file(image_path) != item["rendered_sha256"]:
            raise ValueError(f"review image hash mismatch: {identifier}")


def bind_rendered_evidence(record: Mapping[str, Any], item: Mapping[str, Any]) -> dict[str, Any]:
    """Move OCR pixel boxes to display evidence and restore original source identity."""

    revised = copy.deepcopy(record)
    for _path, envelope in _field_envelopes(revised):
        if envelope.get("source_bbox") is not None:
            envelope["display_bbox"] = envelope["source_bbox"]
            envelope["display_bbox_source"] = "model_grounded"
            envelope["display_bbox_annotator_id"] = None
            envelope["source_bbox"] = None
        if envelope.get("value") is not None:
            envelope["source_page"] = int(item["source_page"])
    document = revised["document"]
    document.update({
        "document_id": item["review_item_id"],
        "source_file": item["source_path"],
        "source_sha256": item["source_file_sha256"],
        "document_type": "native_pdf" if str(item["source_filename"]).lower().endswith(".pdf") else "image",
        "page_count": 1,
        "bbox_coordinate_space": "unknown",
    })
    document["metadata"].update({
        "source_id": item["dataset_id"],
        "project_id": item["dataset_id"],
        "template_id": None,
        "dpi": item["render_dpi"],
        "source_document_page": item["source_page"],
        "ocr_display_bbox_coordinate_space": "rendered_pixels",
        "review_pack_rendered_sha256": item["rendered_sha256"],
        "source_content_review_status": "unreviewed",
    })
    validate_record(revised)
    return revised


def privacy_minimized_diagnostics(
    item: Mapping[str, Any],
    regions: list[TextRegion],
    record: Mapping[str, Any],
    constraint_results: list[Any],
    latency_seconds: float,
) -> dict[str, Any]:
    """Summarize coverage without serializing OCR text or extracted values."""

    confidences = [region.confidence for region in regions if region.confidence is not None]
    borehole_present = sorted(
        name for name, envelope in record["borehole"].items()
        if envelope.get("value") is not None
    )
    interval_presence: Counter[str] = Counter()
    for interval in record["intervals"]:
        interval_presence.update(
            name for name, envelope in interval.items()
            if name != "interval_id" and envelope.get("value") is not None
        )
    violation_codes = Counter(
        violation.code
        for result in constraint_results
        for violation in result.violations
    )
    return {
        "item_id": item["review_item_id"],
        "source_file_sha256": item["source_file_sha256"],
        "rendered_sha256": item["rendered_sha256"],
        "status": "completed",
        "record_sha256": _canonical_sha256(record),
        "record_serialized": False,
        "raw_ocr_text_serialized": False,
        "extracted_values_serialized": False,
        "ocr_region_count": len(regions),
        "ocr_character_count": sum(len(region.text) for region in regions),
        "ocr_confidence": {
            "count": len(confidences),
            "minimum": min(confidences) if confidences else None,
            "mean": sum(confidences) / len(confidences) if confidences else None,
            "maximum": max(confidences) if confidences else None,
        },
        "borehole_fields_present": borehole_present,
        "interval_count": len(record["intervals"]),
        "interval_field_presence_counts": dict(sorted(interval_presence.items())),
        "constraint_evaluated_count": sum(result.evaluated_count for result in constraint_results),
        "constraint_violation_count": sum(len(result.violations) for result in constraint_results),
        "constraint_violation_code_counts": dict(sorted(violation_codes.items())),
        "latency_seconds": latency_seconds,
    }


def run_ocr_coverage_audit(
    *,
    review_pack_root: Path,
    results_root: Path,
    run_metadata: Mapping[str, Any],
    adapter: OCRAdapter,
    constraint_engine: ConstraintEngine,
    dataset_id: str | None = None,
    content_class: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Execute an immutable no-GT OCR audit with privacy-minimized output."""

    review_pack_root = Path(review_pack_root).resolve()
    manifest_path = review_pack_root / "review_pack_manifest.jsonl"
    summary_path = review_pack_root / "review_pack_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("review_pack_manifest_sha256") != sha256_file(manifest_path):
        raise ValueError("review pack manifest differs from pack summary")
    items = [
        json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    items = [
        item for item in items
        if (dataset_id is None or item["dataset_id"] == dataset_id)
        and (content_class is None or item["provisional_content_class"] == content_class)
    ]
    if not items:
        raise ValueError("OCR coverage audit selection is empty")
    _preflight_items(review_pack_root, items)
    run = create_run_directory(results_root, run_metadata)
    rows = []
    errors = []
    total_started = time.perf_counter()
    for item in items:
        image_path = review_pack_root / "images" / f"{item['review_item_id']}.png"
        started = time.perf_counter()
        try:
            regions = adapter.extract(image_path)
            extracted = extract_structured(regions, image_path)
            record = bind_rendered_evidence(extracted, item)
            constraints = constraint_engine.evaluate(record)
            rows.append(privacy_minimized_diagnostics(
                item, regions, record, constraints, time.perf_counter() - started,
            ))
        except Exception as exc:
            rows.append({
                "item_id": item["review_item_id"],
                "source_file_sha256": item["source_file_sha256"],
                "rendered_sha256": item["rendered_sha256"],
                "status": "failed",
                "error_type": type(exc).__name__,
                "record_serialized": False,
                "raw_ocr_text_serialized": False,
                "extracted_values_serialized": False,
                "latency_seconds": time.perf_counter() - started,
            })
            errors.append({
                "item_id": item["review_item_id"],
                "error_type": type(exc).__name__,
                "error_message_sha256": hashlib.sha256(str(exc).encode("utf-8")).hexdigest(),
                "raw_error_message_serialized": False,
            })
    elapsed = time.perf_counter() - total_started
    completed = [row for row in rows if row["status"] == "completed"]
    metrics = {
        "scope": "privacy-minimized OCR+regex coverage audit on unreviewed public candidates; no accuracy claim",
        "data_status": "public_candidates_unreviewed_no_ground_truth",
        "selected_items": len(rows),
        "completed_items": len(completed),
        "failed_items": len(rows) - len(completed),
        "items_with_any_borehole_field": sum(bool(row["borehole_fields_present"]) for row in completed),
        "items_with_borehole_id": sum("borehole_id" in row["borehole_fields_present"] for row in completed),
        "items_with_final_depth": sum("final_depth_m" in row["borehole_fields_present"] for row in completed),
        "items_with_any_interval": sum(row["interval_count"] > 0 for row in completed),
        "emitted_intervals": sum(row["interval_count"] for row in completed),
        "ocr_regions": sum(row["ocr_region_count"] for row in completed),
        "ocr_characters": sum(row["ocr_character_count"] for row in completed),
        "constraint_evaluations": sum(row["constraint_evaluated_count"] for row in completed),
        "constraint_violations": sum(row["constraint_violation_count"] for row in completed),
        "latency_total_seconds": elapsed,
        "latency_mean_seconds_per_item": elapsed / len(rows),
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "record_output_policy": "hash_and_presence_only",
        "accuracy_metrics": None,
        "accuracy_metrics_reason": "source candidates have no human Ground Truth",
        "human_review_count": 0,
        "human_ground_truth_count": 0,
        "benchmark_eligible_count": 0,
    }
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in errors),
        encoding="utf-8",
    )
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run / "run.log").write_text(
        f"status=completed\nselected_items={len(rows)}\ncompleted_items={len(completed)}\n"
        "scope=privacy_minimized_unreviewed_no_gt_audit\n",
        encoding="utf-8",
    )
    return run, metrics
