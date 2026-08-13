import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from geologparser.datasets.content_manifest import build_content_manifest


def _fixture(tmp_path: Path) -> tuple[Path, dict]:
    raw = tmp_path / "raw"
    metadata = tmp_path / "metadata"
    raw.mkdir()
    metadata.mkdir()
    source = raw / "report.pdf"
    document = pymupdf.open()
    for index in range(3):
        page = document.new_page()
        page.insert_text((20, 30), f"page {index + 1}")
    document.save(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    acquisition = {
        "dataset_id": "fixture", "dataset_doi": "10.test/fixture", "dataset_version": 1,
        "license_id": "CC-BY-4.0", "access_date": "2026-08-13",
        "source_inventory_sha256": "a" * 64, "file_count": 1,
        "files": [{
            "filename": source.name, "content_type": "application/pdf",
            "size_bytes": source.stat().st_size, "sha256": digest,
        }],
    }
    (metadata / "acquisition.json").write_text(json.dumps(acquisition), encoding="utf-8")
    config = {
        "dataset_id": "fixture", "record_prefix": "FIX", "language": "English",
        "review": {
            "provenance": "automated_test", "human_content_review": False,
            "human_privacy_review": False,
        },
        "content_rules": [
            {
                "rule_id": "candidate", "filename_globs": ["*.pdf"], "page_ranges": [[1, 1]],
                "content_class": "borehole_log", "phase1_scope": "international_candidate",
                "classification_status": "provisional_automated_review", "paper_fit": ["paper1"],
                "eligibility_blockers": ["NO_GT"],
            },
            {
                "rule_id": "excluded", "filename_globs": ["*.pdf"], "page_ranges": [[2, 3]],
                "content_class": "lab_report", "phase1_scope": "out_of_scope",
                "classification_status": "provisional_automated_review", "paper_fit": [],
                "eligibility_blockers": ["OUT_OF_SCOPE"],
            },
        ],
    }
    return tmp_path, config


def test_build_content_manifest_binds_every_page_to_acquisition(tmp_path: Path):
    root, config = _fixture(tmp_path)
    result = build_content_manifest(root, config)
    rows = [
        json.loads(line)
        for line in (root / "metadata/content_manifest.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert result["page_or_image_count"] == 3
    assert result["content_class_counts"] == {"borehole_log": 1, "lab_report": 2}
    assert result["human_ground_truth_count"] == 0
    assert result["benchmark_eligible_count"] == 0
    assert len({row["source_acquisition_sha256"] for row in rows}) == 1
    assert len({row["content_config_sha256"] for row in rows}) == 1
    assert rows[0]["content_config_sha256"] == result["content_config_sha256"]
    assert all(row["annotation_status"] == "unannotated" for row in rows)
    assert all(row["benchmark_eligible"] is False for row in rows)
    assert all(row["document_type"] == "native_pdf" for row in rows)


def test_content_manifest_rejects_unclassified_page(tmp_path: Path):
    root, config = _fixture(tmp_path)
    config["content_rules"].pop()
    with pytest.raises(ValueError, match="must match exactly one content rule"):
        build_content_manifest(root, config)


def test_content_manifest_rejects_overlapping_rules(tmp_path: Path):
    root, config = _fixture(tmp_path)
    config["content_rules"][1]["page_ranges"] = [[1, 3]]
    with pytest.raises(ValueError, match="matched 2"):
        build_content_manifest(root, config)


def test_content_manifest_rejects_source_hash_drift(tmp_path: Path):
    root, config = _fixture(tmp_path)
    with (root / "raw/report.pdf").open("ab") as stream:
        stream.write(b"drift")
    with pytest.raises(ValueError, match="size mismatch"):
        build_content_manifest(root, config)


def test_content_manifest_cannot_claim_human_review(tmp_path: Path):
    root, config = _fixture(tmp_path)
    config["review"]["human_content_review"] = True
    with pytest.raises(ValueError, match="human_content_review=false"):
        build_content_manifest(root, config)


def test_content_manifest_rejects_non_list_blockers(tmp_path: Path):
    root, config = _fixture(tmp_path)
    config["content_rules"][0]["eligibility_blockers"] = "NO_GT"
    with pytest.raises(ValueError, match="eligibility_blockers must be a list"):
        build_content_manifest(root, config)


def test_content_manifest_preserves_source_image_pixel_dimensions(tmp_path: Path):
    raw = tmp_path / "raw"
    metadata = tmp_path / "metadata"
    raw.mkdir()
    metadata.mkdir()
    source = raw / "section.png"
    pixmap = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 37, 23), False)
    pixmap.clear_with(255)
    pixmap.save(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    (metadata / "acquisition.json").write_text(json.dumps({
        "dataset_id": "image", "dataset_doi": "10.test/image", "dataset_version": 1,
        "license_id": "CC-BY-4.0", "access_date": "2026-08-13",
        "source_inventory_sha256": "a" * 64, "file_count": 1,
        "files": [{
            "filename": source.name, "content_type": "image/png",
            "size_bytes": source.stat().st_size, "sha256": digest,
        }],
    }), encoding="utf-8")
    config = {
        "dataset_id": "image", "record_prefix": "IMG", "language": "English",
        "review": {
            "provenance": "automated_test", "human_content_review": False,
            "human_privacy_review": False,
        },
        "content_rules": [{
            "rule_id": "image", "filename_globs": ["*.png"],
            "content_class": "section", "phase1_scope": "out_of_scope",
            "classification_status": "provisional_automated_review", "paper_fit": [],
            "eligibility_blockers": ["OUT_OF_SCOPE"],
        }],
    }
    build_content_manifest(tmp_path, config)
    row = json.loads((metadata / "content_manifest.jsonl").read_text(encoding="utf-8"))
    assert (row["pixel_width"], row["pixel_height"]) == (37, 23)
