"""Build auto annotation proposals from a completed human source-review gate."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping

import pymupdf

from geologparser.annotation import (
    create_annotation,
    pdf_bbox_to_rendered_pixels,
    save_annotation,
)
from geologparser.datasets.manifest import sha256_file
from geologparser.extraction import extract_structured
from geologparser.ocr import TesseractOCRAdapter
from geologparser.ocr.base import OCRAdapter, TextRegion
from geologparser.page_review import audit_page_reviews
from geologparser.pdf import PyMuPDFPanelTextAdapter


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} line {line_number} is not an object")
        rows.append(value)
    return rows


def _field_envelopes(record: Mapping[str, Any]):
    yield from record["borehole"].values()
    for interval in record.get("intervals", ()):
        for name, envelope in interval.items():
            if name != "interval_id":
                yield envelope


def _verified_eligible_rows(
    pack_root: Path,
    review_root: Path,
    schema_path: Path,
    eligible_manifest: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Regenerate the canonical eligible manifest and require an exact match."""

    if not eligible_manifest.is_file():
        raise FileNotFoundError(eligible_manifest)
    temporary_root = Path(tempfile.mkdtemp(prefix=".eligible-manifest-audit."))
    regenerated = temporary_root / "eligible.jsonl"
    try:
        audit = audit_page_reviews(
            pack_root, review_root, schema_path, eligible_manifest=regenerated,
        )
        if not audit["review_complete"]:
            raise ValueError("source review is incomplete")
        if sha256_file(regenerated) != sha256_file(eligible_manifest):
            raise ValueError(
                "eligible manifest is not the canonical output of the current complete review audit"
            )
        rows = _read_jsonl(eligible_manifest)
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)
    if not rows:
        raise ValueError("eligible manifest contains no annotation-eligible pages")
    for row in rows:
        identifier = str(row.get("review_item_id") or "")
        if not identifier or Path(identifier).name != identifier:
            raise ValueError(f"unsafe review_item_id: {identifier!r}")
        required_true = ("annotation_eligible", "human_content_review", "human_privacy_review")
        if any(row.get(name) is not True for name in required_true):
            raise ValueError(f"eligible row lacks a human source-review gate: {identifier}")
        if row.get("benchmark_eligible") is not False:
            raise ValueError(f"source review cannot grant benchmark eligibility: {identifier}")
        review_path = review_root / f"{identifier}.json"
        source_path = Path(str(row["source_path"]))
        image_path = pack_root / "images" / f"{identifier}.png"
        bindings = {
            review_path: row["content_review_sha256"],
            source_path: row["source_file_sha256"],
            image_path: row["rendered_sha256"],
        }
        for path, expected in bindings.items():
            if not path.is_file() or sha256_file(path) != expected:
                raise ValueError(f"frozen evidence hash mismatch for {identifier}: {path}")
    return rows, audit


def _pdf_panel_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    source = Path(str(row["source_path"]))
    with pymupdf.open(source) as document:
        page = document[int(row["source_page"]) - 1]
        visual = page.rect
        rotation_matrix = page.rotation_matrix
        return {
            "source_pdf_page_rect": [visual.x0, visual.y0, visual.x1, visual.y1],
            "source_pdf_rotation_degrees": page.rotation,
            "source_pdf_rotation_matrix": [
                rotation_matrix.a, rotation_matrix.b, rotation_matrix.c,
                rotation_matrix.d, rotation_matrix.e, rotation_matrix.f,
            ],
            "visual_clip_points": [visual.x0, visual.y0, visual.x1, visual.y1],
        }


def _is_native_pdf(source: Path, page_number: int) -> bool:
    if source.suffix.lower() != ".pdf":
        return False
    with pymupdf.open(source) as document:
        page = document[page_number - 1]
        return any(str(block[4]).strip() for block in page.get_text("blocks"))


def _panel(
    row: Mapping[str, Any], output_root: Path, *, native_pdf: bool,
) -> dict[str, Any]:
    identifier = str(row["review_item_id"])
    panel = {
        "panel_id": identifier,
        "source_path": str(row["source_path"]),
        "source_page": int(row["source_page"]),
        "normalized_bbox": [0.0, 0.0, 1.0, 1.0],
        "borehole_hint": None,
        "project_id": None,
        "template_id": None,
        "redistribution_status": str(row.get("license_id") or "unknown"),
        "source_sha256": row["source_file_sha256"],
        "render_dpi": row["render_dpi"],
        "rendered_path": str(output_root / "images" / f"{identifier}.png"),
        "rendered_sha256": row["rendered_sha256"],
        "rendered_width_px": row["rendered_width_px"],
        "rendered_height_px": row["rendered_height_px"],
        "bbox_coordinate_space": "normalized_0_1_visual_page",
        "eligible_manifest_sha256": None,
        "content_review_sha256": row["content_review_sha256"],
        "content_review_revision": row["content_review_revision"],
        "content_review_reviewer_id": row["content_review_reviewer_id"],
        "source_acquisition_sha256": row["source_acquisition_sha256"],
        "dataset_doi": row.get("dataset_doi"),
        "license_id": row.get("license_id"),
        "annotation_eligible": True,
        "benchmark_eligible": False,
    }
    if native_pdf:
        panel.update(_pdf_panel_metadata(row))
    return panel


def _extract_record(
    row: Mapping[str, Any], panel: Mapping[str, Any], image_path: Path,
    *, native_pdf: bool, ocr_adapter: OCRAdapter,
) -> dict[str, Any]:
    source = Path(str(row["source_path"]))
    if native_pdf:
        regions = PyMuPDFPanelTextAdapter().extract_panel(
            source, int(row["source_page"]), (0.0, 0.0, 1.0, 1.0),
        )
    else:
        regions = [
            TextRegion(
                page=int(row["source_page"]), bbox=region.bbox, text=region.text,
                confidence=region.confidence, method=region.method,
            )
            for region in ocr_adapter.extract(image_path)
        ]
    record = extract_structured(regions, source)
    for envelope in _field_envelopes(record):
        if not isinstance(envelope, dict) or envelope.get("source_bbox") is None:
            continue
        if native_pdf:
            envelope["display_bbox"] = pdf_bbox_to_rendered_pixels(
                envelope["source_bbox"], panel,
            )
            envelope["display_bbox_source"] = "pdf_transform_v001"
        else:
            envelope["display_bbox"] = copy.deepcopy(envelope["source_bbox"])
            envelope["display_bbox_source"] = "ocr_rendered_pixels_v001"
            envelope["source_bbox"] = None
        envelope["display_bbox_annotator_id"] = None
    identifier = str(row["review_item_id"])
    record["document"].update({
        "document_id": identifier,
        "page_count": 1,
        "bbox_coordinate_space": "pdf_points" if native_pdf else "pixels",
        "source_sha256": row["source_file_sha256"],
    })
    record["document"]["metadata"].update({
        "source_id": row.get("dataset_id"),
        "dpi": row.get("render_dpi"),
        "license": row.get("license_id"),
        "source_dataset_doi": row.get("dataset_doi"),
        "source_document_page": row.get("source_page"),
        "eligible_manifest_sha256": panel["eligible_manifest_sha256"],
        "content_review_sha256": row["content_review_sha256"],
        "content_review_revision": row["content_review_revision"],
        "content_review_reviewer_id": row["content_review_reviewer_id"],
        "source_acquisition_sha256": row["source_acquisition_sha256"],
        "rendered_sha256": row["rendered_sha256"],
        "annotation_proposal_status": "auto_needs_independent_human_verification",
        "human_verified_annotation_count": 0,
        "accuracy_metrics": None,
        "benchmark_eligible": False,
    })
    return record


def build_eligible_annotation_pack(
    pack_root: Path,
    review_root: Path,
    eligible_manifest: Path,
    output_root: Path,
    schema_path: Path,
    *,
    ocr_adapter: OCRAdapter | None = None,
) -> dict[str, Any]:
    """Create an immutable pack of auto proposals after the source-review gate."""

    pack_root = Path(pack_root).resolve()
    review_root = Path(review_root).resolve()
    eligible_manifest = Path(eligible_manifest).resolve()
    output_root = Path(output_root).resolve()
    schema_path = Path(schema_path).resolve()
    if output_root.exists():
        raise FileExistsError(f"annotation proposal pack already exists: {output_root}")
    rows, audit = _verified_eligible_rows(
        pack_root, review_root, schema_path, eligible_manifest,
    )
    # The audit is performed against a temporary canonical file; expose the
    # durable frozen manifest path in the persisted summary instead.
    audit = {**audit, "eligible_manifest_path": str(eligible_manifest)}
    eligible_sha256 = sha256_file(eligible_manifest)
    adapter = ocr_adapter or TesseractOCRAdapter(language="chi_sim+eng", psm=6)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent))
    try:
        panels = []
        extraction_counts = {"native_pdf_direct_text": 0, "rendered_image_ocr": 0}
        for row in rows:
            identifier = str(row["review_item_id"])
            source = Path(str(row["source_path"]))
            native_pdf = _is_native_pdf(source, int(row["source_page"]))
            mode = "native_pdf_direct_text" if native_pdf else "rendered_image_ocr"
            extraction_counts[mode] += 1
            source_image = pack_root / "images" / f"{identifier}.png"
            destination_image = temporary / "images" / f"{identifier}.png"
            destination_image.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_image, destination_image)
            if sha256_file(destination_image) != row["rendered_sha256"]:
                raise ValueError(f"copied render hash mismatch: {identifier}")
            panel = _panel(row, output_root, native_pdf=native_pdf)
            panel["eligible_manifest_sha256"] = eligible_sha256
            panel["proposal_extraction_mode"] = mode
            record = _extract_record(
                row, panel, destination_image,
                native_pdf=native_pdf, ocr_adapter=adapter,
            )
            annotation = create_annotation(
                identifier, panel, record,
                f"AUTO_SOURCE_REVIEW_GATED_{mode.upper()}_V001", "auto",
            )
            save_annotation(annotation, temporary / "annotations" / f"{identifier}.json")
            panels.append(panel)
        panel_manifest = temporary / "panel_manifest.jsonl"
        panel_manifest.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in panels),
            encoding="utf-8",
        )
        summary = {
            "proposal_pack_schema_version": "source_review_gated_auto_proposals_v001",
            "scope": "auto extraction proposals after human source review; not Ground Truth",
            "source_review_audit": audit,
            "eligible_manifest_path": str(eligible_manifest),
            "eligible_manifest_sha256": eligible_sha256,
            "proposal_count": len(panels),
            "extraction_counts": extraction_counts,
            "annotation_status": "auto",
            "human_verified_annotation_count": 0,
            "accuracy_metrics": None,
            "benchmark_eligible": False,
            "panel_manifest_sha256": sha256_file(panel_manifest),
        }
        (temporary / "proposal_pack_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, output_root)
        return {
            **summary,
            "proposal_pack_summary_sha256": sha256_file(
                output_root / "proposal_pack_summary.json"
            ),
        }
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
