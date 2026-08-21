import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from geologparser.constraints import default_engine
from geologparser.ocr import TextRegion
from geologparser.ocr_coverage_audit import (
    bind_rendered_evidence,
    run_ocr_coverage_audit,
)


class FakeOCR:
    name = "fake"

    def __init__(self):
        self.call_count = 0

    def extract(self, path: Path):
        self.call_count += 1
        return [TextRegion(
            page=1, bbox=(10, 20, 200, 60), confidence=0.9, method="ocr",
            text="Borehole No: SECRET-01 Final Depth: 4.50",
        )]


def _pack(tmp_path: Path) -> Path:
    root = tmp_path / "pack"
    images = root / "images"
    images.mkdir(parents=True)
    source = tmp_path / "source.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(source)
    image = images / "ITEM_001.png"
    pixmap = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 300, 200), False)
    pixmap.clear_with(255)
    pixmap.save(image)
    row = {
        "review_item_id": "ITEM_001", "dataset_id": "dataset",
        "source_filename": source.name, "source_path": str(source), "source_page": 1,
        "source_file_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_acquisition_sha256": "a" * 64, "content_config_sha256": "b" * 64,
        "provisional_content_class": "engineering_borehole_log",
        "render_dpi": 72, "rendered_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
    }
    manifest = root / "review_pack_manifest.jsonl"
    manifest.write_text(json.dumps(row) + "\n")
    (root / "review_pack_summary.json").write_text(json.dumps({
        "review_pack_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }))
    return root


def _metadata() -> dict:
    return {
        "experiment_id": "TEST_OCR_COVERAGE_001", "git_commit": "a" * 40,
        "date": "2026-08-13", "dataset_version": "fixture",
        "split_version": "audit_no_ground_truth", "model": "fake",
        "model_revision": "fixture", "prompt_version": "not_applicable", "seed": None,
        "hardware": {"device": "cpu"}, "software": {"python": "test"}, "config": {},
    }


def test_rendered_bbox_does_not_masquerade_as_pdf_bbox(tmp_path: Path):
    root = _pack(tmp_path)
    item = json.loads((root / "review_pack_manifest.jsonl").read_text(encoding="utf-8"))
    from geologparser.extraction import extract_structured
    regions = FakeOCR().extract(root / "images/ITEM_001.png")
    record = bind_rendered_evidence(
        extract_structured(regions, root / "images/ITEM_001.png"), item,
    )
    field = record["borehole"]["borehole_id"]
    assert field["value"] == "SECRET-01"
    assert field["source_bbox"] is None
    assert field["display_bbox"] == [10, 20, 200, 60]
    assert field["display_bbox_source"] == "model_grounded"
    assert record["document"]["source_file"] == str(tmp_path / "source.pdf")


def test_audit_serializes_presence_and_hash_not_ocr_text_or_values(tmp_path: Path):
    root = _pack(tmp_path)
    run, metrics = run_ocr_coverage_audit(
        review_pack_root=root, results_root=tmp_path / "results",
        run_metadata=_metadata(), adapter=FakeOCR(), constraint_engine=default_engine(),
        dataset_id="dataset", content_class="engineering_borehole_log",
    )
    output = (run / "predictions.jsonl").read_text(encoding="utf-8")
    row = json.loads(output)
    assert "SECRET-01" not in output
    assert "4.50" not in output
    assert row["borehole_fields_present"] == ["borehole_id", "final_depth_m"]
    assert row["raw_ocr_text_serialized"] is False
    assert row["extracted_values_serialized"] is False
    assert len(row["record_sha256"]) == 64
    assert metrics["accuracy_metrics"] is None
    assert metrics["human_ground_truth_count"] == 0


def test_audit_rejects_review_image_hash_drift_before_ocr(tmp_path: Path):
    root = _pack(tmp_path)
    (root / "images/ITEM_001.png").write_bytes(b"tampered")
    adapter = FakeOCR()
    with pytest.raises(ValueError, match="review image hash mismatch"):
        run_ocr_coverage_audit(
            review_pack_root=root, results_root=tmp_path / "results",
            run_metadata=_metadata(), adapter=adapter, constraint_engine=default_engine(),
        )
    assert adapter.call_count == 0
    assert not (tmp_path / "results").exists()


def test_audit_rejects_source_hash_drift_before_ocr(tmp_path: Path):
    root = _pack(tmp_path)
    item = json.loads((root / "review_pack_manifest.jsonl").read_text(encoding="utf-8"))
    Path(item["source_path"]).write_bytes(b"tampered")
    adapter = FakeOCR()
    with pytest.raises(ValueError, match="review source hash mismatch"):
        run_ocr_coverage_audit(
            review_pack_root=root, results_root=tmp_path / "results",
            run_metadata=_metadata(), adapter=adapter, constraint_engine=default_engine(),
        )
    assert adapter.call_count == 0
    assert not (tmp_path / "results").exists()
