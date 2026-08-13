import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from geologparser.constraints import default_engine
from geologparser.native_pdf_coverage_audit import run_native_pdf_coverage_audit
from geologparser.ocr import TextRegion


class FakePageAdapter:
    name = "fake_positioned_text"

    def __init__(self):
        self.call_count = 0

    def extract_panel(self, path: Path, page_number: int, normalized_bbox):
        self.call_count += 1
        return [
            TextRegion(page_number, (10, 10, 100, 20),
                       "Borehole No: SECRET-01 Final Depth: 4.50", None, "direct_pdf_text"),
            TextRegion(page_number, (20, 100, 80, 110), "0.00-1.00", None, "direct_pdf_text"),
            TextRegion(page_number, (20, 120, 80, 130), "1.00-2.00", None, "direct_pdf_text"),
            TextRegion(page_number, (20, 140, 80, 150), "2.00-3.00", None, "direct_pdf_text"),
        ]


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    row = {
        "record_id": "ITEM_001", "dataset_id": "fixture",
        "source_path": str(source), "source_page": 1,
        "source_file_sha256": digest, "source_content_type": "application/pdf",
        "content_class": "digitised_sedlog_lithology_column",
        "phase1_scope": "international_candidate",
        "classification_status": "provisional_automated_review",
        "human_content_review": False, "human_privacy_review": False,
        "human_ground_truth": False, "benchmark_eligible": False,
    }
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
    return manifest, source


def _metadata() -> dict:
    return {
        "experiment_id": "TEST_NATIVE_COVERAGE_001", "git_commit": "a" * 40,
        "date": "2026-08-13", "dataset_version": "fixture",
        "split_version": "audit_no_ground_truth", "model": "fake",
        "model_revision": "fixture", "prompt_version": "not_applicable", "seed": None,
        "hardware": {"device": "cpu"}, "software": {"python": "test"}, "config": {},
    }


def _run(tmp_path: Path, adapter: FakePageAdapter):
    manifest, _source = _fixture(tmp_path)
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    return run_native_pdf_coverage_audit(
        manifest_path=manifest, expected_manifest_sha256=digest,
        results_root=tmp_path / "results", run_metadata=_metadata(), adapter=adapter,
        constraint_engine=default_engine(), dataset_id="fixture",
        content_class="digitised_sedlog_lithology_column",
        phase1_scope="international_candidate",
    )


def test_native_audit_serializes_hashes_and_counts_not_source_values(tmp_path: Path):
    run, metrics = _run(tmp_path, FakePageAdapter())
    output = (run / "predictions.jsonl").read_text(encoding="utf-8")
    row = json.loads(output)
    assert "SECRET-01" not in output
    assert "4.50" not in output
    assert "0.00-1.00" not in output
    assert row["raw_text_serialized"] is False
    assert row["source_bboxes_serialized"] is False
    assert row["regex_borehole_fields_present"] == ["borehole_id", "final_depth_m"]
    assert row["layout_interval_count"] == 3
    assert len(row["regex_record_sha256"]) == 64
    assert len(row["layout_record_sha256"]) == 64
    assert metrics["accuracy_metrics"] is None
    assert metrics["human_ground_truth_count"] == 0


def test_native_audit_rejects_manifest_hash_drift_before_adapter(tmp_path: Path):
    manifest, _source = _fixture(tmp_path)
    adapter = FakePageAdapter()
    with pytest.raises(ValueError, match="manifest hash differs"):
        run_native_pdf_coverage_audit(
            manifest_path=manifest, expected_manifest_sha256="f" * 64,
            results_root=tmp_path / "results", run_metadata=_metadata(), adapter=adapter,
            constraint_engine=default_engine(),
        )
    assert adapter.call_count == 0
    assert not (tmp_path / "results").exists()


def test_native_audit_rejects_source_hash_drift_before_adapter(tmp_path: Path):
    manifest, source = _fixture(tmp_path)
    expected = hashlib.sha256(manifest.read_bytes()).hexdigest()
    source.write_bytes(b"tampered")
    adapter = FakePageAdapter()
    with pytest.raises(ValueError, match="content source hash mismatch"):
        run_native_pdf_coverage_audit(
            manifest_path=manifest, expected_manifest_sha256=expected,
            results_root=tmp_path / "results", run_metadata=_metadata(), adapter=adapter,
            constraint_engine=default_engine(),
        )
    assert adapter.call_count == 0
    assert not (tmp_path / "results").exists()
