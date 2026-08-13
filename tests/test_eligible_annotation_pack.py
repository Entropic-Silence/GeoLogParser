import copy
import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from geologparser.eligible_annotation_pack import build_eligible_annotation_pack
from geologparser.ocr.base import TextRegion
from geologparser.page_review import (
    CHECK_NAMES, audit_page_reviews, build_page_review, build_page_review_pack,
    load_review_items, save_page_review,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/page_content_review_v001.schema.json"


class FakeOCR:
    name = "fake_ocr"

    def extract(self, path: Path):
        return [TextRegion(1, (10, 20, 180, 45), "孔号 BH-IMG-01", 0.9, "ocr")]


def _manifest(tmp_path: Path, *, image: bool = False) -> Path:
    source = tmp_path / ("source.png" if image else "source.pdf")
    document = pymupdf.open()
    page = document.new_page(width=300, height=200)
    page.insert_text((20, 30), "Borehole ID: BH-PDF-01")
    if image:
        pixmap = page.get_pixmap()
        pixmap.save(source)
    else:
        document.save(source)
    document.close()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    row = {
        "record_id": "CANDIDATE_001", "dataset_id": "dataset",
        "dataset_doi": "10.test/1", "source_filename": source.name,
        "source_path": str(source), "source_page": 1,
        "source_file_sha256": digest, "source_acquisition_sha256": "a" * 64,
        "source_inventory_sha256": "b" * 64, "content_config_sha256": "c" * 64,
        "content_class": "engineering_borehole_log",
        "classification_status": "provisional_automated_review",
        "phase1_scope": "international_candidate", "language": "English",
        "license_id": "CC-BY-4.0", "human_content_review": False,
        "benchmark_eligible": False,
    }
    manifest = tmp_path / "content.jsonl"
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
    return manifest


def _complete_gate(tmp_path: Path, *, image: bool = False):
    manifest = _manifest(tmp_path, image=image)
    pack = tmp_path / "review_pack"
    reviews = tmp_path / "reviews"
    build_page_review_pack([manifest], pack, dpi=72)
    item = next(iter(load_review_items(pack / "review_pack_manifest.jsonl").values()))
    payload = {
        "reviewer_id": "human-source-reviewer", "decision": "eligible_for_annotation",
        "phase1_borehole_content": True, "render_complete": True,
        "redactions_required": False, "notes": None,
        "checks": {
            name: {"status": "absent", "action": "not_applicable", "notes": None}
            for name in CHECK_NAMES
        },
    }
    save_page_review(build_page_review(payload, item, 1), reviews)
    eligible = tmp_path / "eligible.jsonl"
    audit_page_reviews(pack, reviews, SCHEMA, eligible_manifest=eligible)
    return pack, reviews, eligible


def test_builds_native_pdf_auto_proposal_with_two_coordinate_spaces(tmp_path: Path):
    pack, reviews, eligible = _complete_gate(tmp_path)
    output = tmp_path / "proposals"
    result = build_eligible_annotation_pack(
        pack, reviews, eligible, output, SCHEMA, ocr_adapter=FakeOCR(),
    )
    annotation = json.loads((output / "annotations/CANDIDATE_001.json").read_text())
    field = annotation["record"]["borehole"]["borehole_id"]
    assert result["proposal_count"] == 1
    assert result["source_review_audit"]["eligible_manifest_path"] == str(eligible.resolve())
    assert result["human_verified_annotation_count"] == 0
    assert result["accuracy_metrics"] is None
    assert result["benchmark_eligible"] is False
    assert annotation["annotation_status"] == "auto"
    assert field["source_bbox"] is not None
    assert field["display_bbox"] is not None
    assert field["display_bbox_source"] == "pdf_transform_v001"
    assert annotation["record"]["document"]["bbox_coordinate_space"] == "pdf_points"
    assert hashlib.sha256((output / "images/CANDIDATE_001.png").read_bytes()).hexdigest() == annotation["panel"]["rendered_sha256"]


def test_image_ocr_bbox_is_display_only(tmp_path: Path):
    pack, reviews, eligible = _complete_gate(tmp_path, image=True)
    output = tmp_path / "proposals"
    build_eligible_annotation_pack(
        pack, reviews, eligible, output, SCHEMA, ocr_adapter=FakeOCR(),
    )
    annotation = json.loads((output / "annotations/CANDIDATE_001.json").read_text())
    field = annotation["record"]["borehole"]["borehole_id"]
    assert field["value"] == "BH-IMG-01"
    assert field["source_bbox"] is None
    assert field["display_bbox"] == [10.0, 20.0, 180.0, 45.0]
    assert field["display_bbox_source"] == "ocr_rendered_pixels_v001"
    assert annotation["panel"]["proposal_extraction_mode"] == "rendered_image_ocr"


def test_rejects_incomplete_review_even_with_forged_manifest(tmp_path: Path):
    manifest = _manifest(tmp_path)
    pack = tmp_path / "review_pack"
    reviews = tmp_path / "reviews"
    build_page_review_pack([manifest], pack, dpi=72)
    forged = tmp_path / "eligible.jsonl"
    row = json.loads((pack / "review_pack_manifest.jsonl").read_text())
    row.update({
        "annotation_eligible": True, "human_content_review": True,
        "human_privacy_review": True, "benchmark_eligible": False,
        "content_review_sha256": "d" * 64,
    })
    forged.write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="unreviewed"):
        build_eligible_annotation_pack(
            pack, reviews, forged, tmp_path / "out", SCHEMA, ocr_adapter=FakeOCR(),
        )


@pytest.mark.parametrize("target", ["manifest", "review", "source", "render"])
def test_rejects_tampered_gate_evidence(tmp_path: Path, target: str):
    pack, reviews, eligible = _complete_gate(tmp_path)
    row = json.loads(eligible.read_text())
    paths = {
        "manifest": eligible,
        "review": reviews / "CANDIDATE_001.json",
        "source": Path(row["source_path"]),
        "render": pack / "images/CANDIDATE_001.png",
    }
    if target == "manifest":
        changed = copy.deepcopy(row)
        changed["dataset_doi"] = "10.test/tampered"
        paths[target].write_text(json.dumps(changed, sort_keys=True) + "\n")
    else:
        paths[target].write_bytes(paths[target].read_bytes() + b"tampered")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        build_eligible_annotation_pack(
            pack, reviews, eligible, tmp_path / "out", SCHEMA, ocr_adapter=FakeOCR(),
        )


def test_output_pack_is_immutable(tmp_path: Path):
    pack, reviews, eligible = _complete_gate(tmp_path)
    output = tmp_path / "proposals"
    build_eligible_annotation_pack(pack, reviews, eligible, output, SCHEMA, ocr_adapter=FakeOCR())
    with pytest.raises(FileExistsError):
        build_eligible_annotation_pack(pack, reviews, eligible, output, SCHEMA, ocr_adapter=FakeOCR())
