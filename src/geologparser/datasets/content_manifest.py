"""Build page-level content manifests bound to frozen acquisition evidence."""

from __future__ import annotations

from collections import Counter
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pymupdf

from geologparser.datasets.manifest import sha256_file


SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png"}


def _require_mapping(value: Any, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _string_list(value: Any, *, name: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not all(isinstance(item, str) and item for item in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError(f"{name} must be a list of unique non-empty strings")
    return value


def _page_selected(rule: Mapping[str, Any], filename: str, page_number: int) -> bool:
    patterns = rule.get("filename_globs")
    if not isinstance(patterns, list) or not patterns or not all(isinstance(item, str) for item in patterns):
        raise ValueError("every content rule requires non-empty filename_globs")
    if not any(fnmatchcase(filename, pattern) for pattern in patterns):
        return False
    ranges = rule.get("page_ranges")
    if ranges is None:
        return True
    if not isinstance(ranges, list) or not ranges:
        raise ValueError("page_ranges must be a non-empty list when provided")
    for item in ranges:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not all(isinstance(value, int) and value >= 1 for value in item)
            or item[0] > item[1]
        ):
            raise ValueError("page ranges must be inclusive [start, end] positive integers")
        if item[0] <= page_number <= item[1]:
            return True
    return False


def _classify_page(
    rules: Sequence[Mapping[str, Any]], filename: str, page_number: int,
) -> Mapping[str, Any]:
    matches = [rule for rule in rules if _page_selected(rule, filename, page_number)]
    if len(matches) != 1:
        raise ValueError(
            f"{filename} page {page_number} must match exactly one content rule; matched {len(matches)}"
        )
    required = {
        "rule_id", "content_class", "phase1_scope", "classification_status",
        "paper_fit", "eligibility_blockers",
    }
    missing = sorted(required - matches[0].keys())
    if missing:
        raise ValueError(f"content rule is missing required fields: {', '.join(missing)}")
    return matches[0]


def _document_type(native_text_chars: int, embedded_images: int, vector_drawings: int) -> str:
    if native_text_chars:
        return "native_pdf"
    if vector_drawings:
        return "vector_pdf_without_extractable_text"
    if embedded_images:
        return "image_pdf_without_extractable_text"
    return "pdf_without_detected_content"


def _source_pages(path: Path, content_type: str) -> list[dict[str, Any]]:
    if content_type != "application/pdf" and content_type not in SUPPORTED_IMAGE_TYPES:
        raise ValueError(f"unsupported page-image content type: {content_type}")
    image_dimensions = None
    if content_type in SUPPORTED_IMAGE_TYPES:
        pixmap = pymupdf.Pixmap(path)
        image_dimensions = (pixmap.width, pixmap.height)
    with pymupdf.open(path) as document:
        if content_type in SUPPORTED_IMAGE_TYPES and len(document) != 1:
            raise ValueError(f"image source unexpectedly exposes {len(document)} pages: {path.name}")
        rows = []
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text") if content_type == "application/pdf" else ""
            images = len(page.get_images(full=True)) if content_type == "application/pdf" else 1
            drawings = len(page.get_drawings()) if content_type == "application/pdf" else 0
            if content_type == "application/pdf":
                document_type = _document_type(len(text), images, drawings)
                dimensions: dict[str, Any] = {
                    "page_width_pt": page.rect.width,
                    "page_height_pt": page.rect.height,
                }
            else:
                document_type = "standalone_image"
                dimensions = {
                    "pixel_width": image_dimensions[0],
                    "pixel_height": image_dimensions[1],
                }
            rows.append({
                "source_page": page_number,
                "document_type": document_type,
                "native_text_chars": len(text),
                "embedded_image_count": images,
                "vector_drawing_count": drawings,
                **dimensions,
            })
        return rows


def build_content_manifest(
    dataset_root: Path,
    config: Mapping[str, Any],
    *,
    output_directory: Path | None = None,
) -> dict[str, Any]:
    """Create a complete page/image inventory without granting benchmark eligibility."""

    acquisition_path = dataset_root / "metadata/acquisition.json"
    acquisition = _require_mapping(
        json.loads(acquisition_path.read_text(encoding="utf-8")), name="acquisition evidence",
    )
    expected_dataset_id = str(config.get("dataset_id") or "")
    if acquisition.get("dataset_id") != expected_dataset_id:
        raise ValueError("content-manifest config does not match acquisition dataset_id")
    files = acquisition.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("acquisition evidence contains no files")
    if acquisition.get("file_count") != len(files):
        raise ValueError("acquisition file count is inconsistent")
    rules = config.get("content_rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("content manifest requires at least one content rule")
    config_sha256 = _canonical_sha256(config)

    acquisition_sha256 = sha256_file(acquisition_path)
    review = _require_mapping(config.get("review"), name="review metadata")
    if review.get("human_content_review") is not False:
        raise ValueError("this automated builder only accepts human_content_review=false")
    if review.get("human_privacy_review") is not False:
        raise ValueError("this automated builder only accepts human_privacy_review=false")

    rows: list[dict[str, Any]] = []
    seen_filenames: set[str] = set()
    for file_index, item_value in enumerate(files, start=1):
        item = _require_mapping(item_value, name="acquisition file")
        filename = str(item.get("filename") or "")
        if not filename or Path(filename).name != filename or filename in seen_filenames:
            raise ValueError(f"unsafe or duplicate acquired filename: {filename!r}")
        seen_filenames.add(filename)
        path = dataset_root / "raw" / filename
        if path.stat().st_size != item.get("size_bytes"):
            raise ValueError(f"acquired size mismatch: {filename}")
        source_sha256 = sha256_file(path)
        if source_sha256 != item.get("sha256"):
            raise ValueError(f"acquired SHA256 mismatch: {filename}")
        content_type = str(item.get("content_type") or "")
        for page in _source_pages(path, content_type):
            rule = _classify_page(rules, filename, page["source_page"])
            paper_fit = _string_list(rule["paper_fit"], name="paper_fit")
            blockers = _string_list(
                rule["eligibility_blockers"], name="eligibility_blockers",
            )
            record_id = (
                f"{str(config['record_prefix'])}_{file_index:03d}_P{page['source_page']:03d}"
            )
            rows.append({
                "record_id": record_id,
                "source_record_id": record_id,
                "dataset_id": expected_dataset_id,
                "dataset_doi": acquisition.get("dataset_doi"),
                "dataset_version": acquisition.get("dataset_version"),
                "source_filename": filename,
                "source_path": str(path),
                "source_content_type": content_type,
                "source_file_sha256": source_sha256,
                "source_acquisition_sha256": acquisition_sha256,
                "source_inventory_sha256": acquisition.get("source_inventory_sha256"),
                "content_config_sha256": config_sha256,
                "access_date": acquisition.get("access_date"),
                "license_id": acquisition.get("license_id"),
                "language": rule.get("language", config.get("language")),
                **page,
                "classification_rule_id": rule["rule_id"],
                "content_class": rule["content_class"],
                "phase1_scope": rule["phase1_scope"],
                "classification_status": rule["classification_status"],
                "classification_provenance": review.get("provenance"),
                "human_content_review": False,
                "human_privacy_review": False,
                "annotation_status": "unannotated",
                "human_ground_truth": False,
                "benchmark_eligible": False,
                "paper_fit": paper_fit,
                "eligibility_blockers": blockers,
                "notes": rule.get("notes"),
            })

    output_root = output_directory or dataset_root / "metadata"
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / "content_manifest.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    class_counts = Counter(str(row["content_class"]) for row in rows)
    scope_counts = Counter(str(row["phase1_scope"]) for row in rows)
    type_counts = Counter(str(row["document_type"]) for row in rows)
    summary = {
        "content_manifest_schema_version": "page_content_manifest_v001",
        "dataset_id": expected_dataset_id,
        "dataset_doi": acquisition.get("dataset_doi"),
        "source_acquisition_path": str(acquisition_path),
        "source_acquisition_sha256": acquisition_sha256,
        "source_inventory_sha256": acquisition.get("source_inventory_sha256"),
        "content_config_sha256": config_sha256,
        "source_file_count": len(files),
        "page_or_image_count": len(rows),
        "content_class_counts": dict(sorted(class_counts.items())),
        "phase1_scope_counts": dict(sorted(scope_counts.items())),
        "document_type_counts": dict(sorted(type_counts.items())),
        "human_content_review_count": 0,
        "human_privacy_review_count": 0,
        "human_ground_truth_count": 0,
        "benchmark_eligible_count": 0,
        "classification_provenance": review.get("provenance"),
        "content_manifest_sha256": sha256_file(manifest_path),
    }
    summary_path = output_root / "content_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {**summary, "content_summary_sha256": sha256_file(summary_path)}
