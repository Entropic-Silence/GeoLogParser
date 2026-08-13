"""Privacy-minimized direct-text and layout coverage audits for native PDFs."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import resource
import time
from typing import Any, Mapping, Protocol

import pymupdf

from geologparser.constraints import ConstraintEngine
from geologparser.datasets.manifest import sha256_file
from geologparser.experiment import create_run_directory
from geologparser.extraction import extract_structured
from geologparser.layout import extract_depth_column_intervals
from geologparser.ocr import TextRegion
from geologparser.ocr_coverage_audit import canonical_record_sha256
from geologparser.schema import validate_record


REQUIRED_CONTENT_FIELDS = {
    "record_id", "dataset_id", "source_path", "source_page", "source_file_sha256",
    "source_content_type", "content_class", "phase1_scope", "classification_status",
    "human_content_review", "human_privacy_review", "human_ground_truth",
    "benchmark_eligible",
}


class PageTextAdapter(Protocol):
    name: str

    def extract_panel(
        self,
        path: Path,
        page_number: int,
        normalized_bbox: tuple[float, float, float, float],
    ) -> list[TextRegion]: ...


def _read_manifest(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"content manifest line {line_number} is not an object")
        rows.append(row)
    return rows


def _select_items(
    rows: list[dict[str, Any]],
    *,
    dataset_id: str | None,
    content_class: str | None,
    phase1_scope: str | None,
) -> list[dict[str, Any]]:
    return [
        row for row in rows
        if (dataset_id is None or row.get("dataset_id") == dataset_id)
        and (content_class is None or row.get("content_class") == content_class)
        and (phase1_scope is None or row.get("phase1_scope") == phase1_scope)
    ]


def _preflight_items(items: list[dict[str, Any]]) -> None:
    identifiers: set[str] = set()
    source_cache: dict[Path, tuple[str, int]] = {}
    for item in items:
        missing = sorted(REQUIRED_CONTENT_FIELDS - set(item))
        if missing:
            raise ValueError(f"content item is missing required fields: {', '.join(missing)}")
        identifier = str(item["record_id"])
        if not identifier or Path(identifier).name != identifier or identifier in identifiers:
            raise ValueError(f"unsafe or duplicate content record_id: {identifier!r}")
        identifiers.add(identifier)
        if item["source_content_type"] != "application/pdf":
            raise ValueError(f"native PDF audit received non-PDF content: {identifier}")
        if any(item[name] is not False for name in (
            "human_content_review", "human_privacy_review", "human_ground_truth",
            "benchmark_eligible",
        )):
            raise ValueError(f"native PDF coverage audit requires unreviewed non-GT input: {identifier}")
        source = Path(str(item["source_path"]))
        if not source.is_file():
            raise ValueError(f"content source is missing: {identifier}")
        if source not in source_cache:
            digest = sha256_file(source)
            if digest != item["source_file_sha256"]:
                raise ValueError(f"content source hash mismatch: {identifier}")
            with pymupdf.open(source) as document:
                page_count = len(document)
            source_cache[source] = (digest, page_count)
        digest, page_count = source_cache[source]
        if digest != item["source_file_sha256"]:
            raise ValueError(f"content source hash mismatch: {identifier}")
        page_number = item["source_page"]
        if not isinstance(page_number, int) or not 1 <= page_number <= page_count:
            raise ValueError(f"content source page is outside document: {identifier}")


def _field_presence(record: Mapping[str, Any]) -> tuple[list[str], dict[str, int]]:
    borehole = sorted(
        name for name, envelope in record["borehole"].items()
        if envelope.get("value") is not None
    )
    interval_fields: Counter[str] = Counter()
    for interval in record["intervals"]:
        interval_fields.update(
            name for name, envelope in interval.items()
            if name != "interval_id" and envelope.get("value") is not None
        )
    return borehole, dict(sorted(interval_fields.items()))


def _constraint_counts(results: list[Any]) -> tuple[int, int, dict[str, int]]:
    codes = Counter(
        violation.code for result in results for violation in result.violations
    )
    return (
        sum(result.evaluated_count for result in results),
        sum(len(result.violations) for result in results),
        dict(sorted(codes.items())),
    )


def privacy_minimized_native_diagnostics(
    item: Mapping[str, Any],
    regions: list[TextRegion],
    regex_record: Mapping[str, Any],
    layout_record: Mapping[str, Any],
    regex_constraints: list[Any],
    layout_constraints: list[Any],
    latency_seconds: float,
) -> dict[str, Any]:
    regex_borehole, regex_interval_fields = _field_presence(regex_record)
    layout_borehole, layout_interval_fields = _field_presence(layout_record)
    regex_evaluated, regex_violations, regex_codes = _constraint_counts(regex_constraints)
    layout_evaluated, layout_violations, layout_codes = _constraint_counts(layout_constraints)
    return {
        "item_id": item["record_id"],
        "source_file_sha256": item["source_file_sha256"],
        "status": "completed",
        "record_serialized": False,
        "raw_text_serialized": False,
        "extracted_values_serialized": False,
        "source_bboxes_serialized": False,
        "text_region_count": len(regions),
        "text_character_count": sum(len(region.text) for region in regions),
        "regex_record_sha256": canonical_record_sha256(regex_record),
        "regex_borehole_fields_present": regex_borehole,
        "regex_interval_count": len(regex_record["intervals"]),
        "regex_interval_field_presence_counts": regex_interval_fields,
        "regex_constraint_evaluated_count": regex_evaluated,
        "regex_constraint_violation_count": regex_violations,
        "regex_constraint_violation_code_counts": regex_codes,
        "layout_record_sha256": canonical_record_sha256(layout_record),
        "layout_borehole_fields_present": layout_borehole,
        "layout_interval_count": len(layout_record["intervals"]),
        "layout_interval_field_presence_counts": layout_interval_fields,
        "layout_constraint_evaluated_count": layout_evaluated,
        "layout_constraint_violation_count": layout_violations,
        "layout_constraint_violation_code_counts": layout_codes,
        "latency_seconds": latency_seconds,
    }


def run_native_pdf_coverage_audit(
    *,
    manifest_path: Path,
    expected_manifest_sha256: str,
    results_root: Path,
    run_metadata: Mapping[str, Any],
    adapter: PageTextAdapter,
    constraint_engine: ConstraintEngine,
    dataset_id: str | None = None,
    content_class: str | None = None,
    phase1_scope: str | None = None,
    x_bin_points: float = 12.0,
    minimum_unique_ranges: int = 3,
) -> tuple[Path, dict[str, Any]]:
    """Run two extraction paths without persisting text, values, or bboxes."""

    manifest_path = Path(manifest_path).resolve()
    if sha256_file(manifest_path) != expected_manifest_sha256:
        raise ValueError("content manifest hash differs from expected evidence")
    items = _select_items(
        _read_manifest(manifest_path), dataset_id=dataset_id,
        content_class=content_class, phase1_scope=phase1_scope,
    )
    if not items:
        raise ValueError("native PDF coverage audit selection is empty")
    _preflight_items(items)
    run = create_run_directory(results_root, run_metadata)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    total_started = time.perf_counter()
    for item in items:
        started = time.perf_counter()
        try:
            source = Path(str(item["source_path"]))
            regions = adapter.extract_panel(
                source, int(item["source_page"]), (0.0, 0.0, 1.0, 1.0),
            )
            regex_record = extract_structured(regions, source)
            regex_record["document"]["document_id"] = item["record_id"]
            regex_record["document"]["metadata"].update({
                "source_id": item["dataset_id"],
                "source_document_page": item["source_page"],
                "source_content_review_status": "unreviewed",
            })
            validate_record(regex_record)
            layout_record = copy.deepcopy(regex_record)
            layout_record["intervals"] = extract_depth_column_intervals(
                regions, x_bin_points=x_bin_points,
                minimum_unique_ranges=minimum_unique_ranges,
            )
            validate_record(layout_record)
            regex_constraints = constraint_engine.evaluate(regex_record)
            layout_constraints = constraint_engine.evaluate(layout_record)
            rows.append(privacy_minimized_native_diagnostics(
                item, regions, regex_record, layout_record,
                regex_constraints, layout_constraints,
                time.perf_counter() - started,
            ))
        except Exception as exc:
            rows.append({
                "item_id": item["record_id"],
                "source_file_sha256": item["source_file_sha256"],
                "status": "failed",
                "record_serialized": False,
                "raw_text_serialized": False,
                "extracted_values_serialized": False,
                "source_bboxes_serialized": False,
                "error_type": type(exc).__name__,
                "latency_seconds": time.perf_counter() - started,
            })
            errors.append({
                "item_id": item["record_id"],
                "error_type": type(exc).__name__,
                "error_message_sha256": hashlib.sha256(str(exc).encode("utf-8")).hexdigest(),
                "raw_error_message_serialized": False,
            })
    elapsed = time.perf_counter() - total_started
    completed = [row for row in rows if row["status"] == "completed"]
    metrics = {
        "scope": "privacy-minimized native-PDF regex and positioned-layout coverage audit; no accuracy claim",
        "data_status": "public_candidates_unreviewed_no_ground_truth",
        "coverage_channels": ["direct_text_regex", "positioned_text_layout"],
        "selected_items": len(rows),
        "completed_items": len(completed),
        "failed_items": len(rows) - len(completed),
        "text_regions": sum(row["text_region_count"] for row in completed),
        "text_characters": sum(row["text_character_count"] for row in completed),
        "regex_items_with_borehole_id": sum(
            "borehole_id" in row["regex_borehole_fields_present"] for row in completed
        ),
        "regex_items_with_any_interval": sum(row["regex_interval_count"] > 0 for row in completed),
        "regex_emitted_intervals": sum(row["regex_interval_count"] for row in completed),
        "regex_constraint_evaluations": sum(
            row["regex_constraint_evaluated_count"] for row in completed
        ),
        "regex_constraint_violations": sum(
            row["regex_constraint_violation_count"] for row in completed
        ),
        "layout_items_with_any_interval": sum(row["layout_interval_count"] > 0 for row in completed),
        "layout_emitted_intervals": sum(row["layout_interval_count"] for row in completed),
        "layout_constraint_evaluations": sum(
            row["layout_constraint_evaluated_count"] for row in completed
        ),
        "layout_constraint_violations": sum(
            row["layout_constraint_violation_count"] for row in completed
        ),
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
        "scope=privacy_minimized_native_pdf_unreviewed_no_gt_audit\n",
        encoding="utf-8",
    )
    return run, metrics
