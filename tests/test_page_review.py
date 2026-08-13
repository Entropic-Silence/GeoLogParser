import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from geologparser.page_review import (
    CHECK_NAMES,
    audit_page_reviews,
    build_page_review,
    build_page_review_pack,
    create_page_review_app,
    save_page_review,
)


ROOT = Path(__file__).resolve().parents[1]


def _content_manifest(tmp_path: Path) -> Path:
    source = tmp_path / "source.pdf"
    document = pymupdf.open()
    page = document.new_page(width=300, height=200)
    page.insert_text((20, 30), "BH-01")
    document.save(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    row = {
        "record_id": "CANDIDATE_001", "dataset_id": "dataset", "dataset_doi": "10.test/1",
        "source_filename": source.name, "source_path": str(source), "source_page": 1,
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


def _item() -> dict:
    return {
        "review_item_id": "CANDIDATE_001", "source_file_sha256": "a" * 64,
        "source_acquisition_sha256": "b" * 64, "content_config_sha256": "c" * 64,
        "rendered_sha256": "d" * 64,
    }


def _payload(decision: str = "internal_only") -> dict:
    return {
        "reviewer_id": "human-reviewer-1", "decision": decision,
        "phase1_borehole_content": True, "render_complete": True,
        "redactions_required": False, "notes": None,
        "checks": {
            name: {"status": "absent", "action": "not_applicable", "notes": None}
            for name in CHECK_NAMES
        },
    }


def test_review_pack_renders_and_binds_candidate(tmp_path: Path):
    manifest = _content_manifest(tmp_path)
    output = tmp_path / "pack"
    result = build_page_review_pack([manifest], output, dpi=72)
    row = json.loads((output / "review_pack_manifest.jsonl").read_text(encoding="utf-8"))
    assert result["review_item_count"] == 1
    assert result["human_review_count"] == 0
    assert result["benchmark_eligible_count"] == 0
    assert row["rendered_width_px"] == 300
    assert row["rendered_height_px"] == 200
    assert hashlib.sha256(Path(row["rendered_path"]).read_bytes()).hexdigest() == row["rendered_sha256"]


def test_review_pack_is_immutable(tmp_path: Path):
    manifest = _content_manifest(tmp_path)
    output = tmp_path / "pack"
    build_page_review_pack([manifest], output)
    with pytest.raises(FileExistsError):
        build_page_review_pack([manifest], output)


def test_review_pack_rejects_unsafe_record_id(tmp_path: Path):
    manifest = _content_manifest(tmp_path)
    row = json.loads(manifest.read_text())
    row["record_id"] = "../escape"
    manifest.write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="unsafe or duplicate content record_id"):
        build_page_review_pack([manifest], tmp_path / "pack")


def test_eligible_review_allows_explicitly_cleared_present_content():
    payload = _payload("eligible_for_annotation")
    payload["checks"]["organization_or_project"] = {
        "status": "present", "action": "cleared", "notes": "public project",
    }
    review = build_page_review(payload, _item(), 1)
    assert review["annotation_eligible"] is True
    assert review["benchmark_eligible"] is False
    assert review["reviewer_provenance"] == "human_self_attested_not_identity_authenticated"


def test_present_content_requires_review_notes():
    payload = _payload("internal_only")
    payload["checks"]["organization_or_project"] = {
        "status": "present", "action": "restrict", "notes": None,
    }
    with pytest.raises(ValueError, match="requires non-empty review notes"):
        build_page_review(payload, _item(), 1)


def test_eligible_review_rejects_unresolved_or_redacted_content():
    payload = _payload("eligible_for_annotation")
    payload["checks"]["coordinates_or_sensitive_location"] = {
        "status": "present", "action": "restrict", "notes": "precise site coordinate",
    }
    with pytest.raises(ValueError, match="unresolved disclosure checks"):
        build_page_review(payload, _item(), 1)
    payload = _payload("eligible_for_annotation")
    payload["redactions_required"] = True
    with pytest.raises(ValueError, match="cannot retain required redactions"):
        build_page_review(payload, _item(), 1)


def test_revisioned_review_save_archives_prior(tmp_path: Path):
    first = build_page_review(_payload(), _item(), 1)
    save_page_review(first, tmp_path)
    second = build_page_review(_payload("exclude"), _item(), 2)
    save_page_review(second, tmp_path)
    assert json.loads((tmp_path / "CANDIDATE_001.json").read_text())["revision"] == 2
    assert (tmp_path / "history/CANDIDATE_001/revision_0001.json").is_file()


def test_page_review_api_verifies_image_and_revision(tmp_path: Path):
    manifest = _content_manifest(tmp_path)
    pack = tmp_path / "pack"
    build_page_review_pack([manifest], pack, dpi=72)
    static = tmp_path / "static"
    static.mkdir()
    for name in ("index.html", "app.js", "style.css"):
        (static / name).write_text("ok")
    app = create_page_review_app(
        pack, tmp_path / "reviews", static,
        ROOT / "schemas/page_content_review_v001.schema.json",
    )
    from fastapi.testclient import TestClient
    client = TestClient(app)
    assert client.get("/api/items").json()[0]["review"] is None
    payload = _payload()
    payload["base_revision"] = 0
    assert client.put("/api/items/CANDIDATE_001/review", json=payload).status_code == 200
    assert client.put("/api/items/CANDIDATE_001/review", json=payload).status_code == 409
    (pack / "images/CANDIDATE_001.png").write_bytes(b"tampered")
    assert client.get("/api/items/CANDIDATE_001/image").status_code == 409


def test_page_review_api_rejects_tampered_stored_review(tmp_path: Path):
    manifest = _content_manifest(tmp_path)
    pack = tmp_path / "pack"
    build_page_review_pack([manifest], pack, dpi=72)
    item = json.loads((pack / "review_pack_manifest.jsonl").read_text())
    reviews = tmp_path / "reviews"
    review = build_page_review(_payload(), item, 1)
    review["source_file_sha256"] = "f" * 64
    reviews.mkdir()
    (reviews / "CANDIDATE_001.json").write_text(json.dumps(review))
    static = tmp_path / "static"
    static.mkdir()
    for name in ("index.html", "app.js", "style.css"):
        (static / name).write_text("ok")
    app = create_page_review_app(
        pack, reviews, static, ROOT / "schemas/page_content_review_v001.schema.json",
    )
    from fastapi.testclient import TestClient
    assert TestClient(app).get("/api/items").status_code == 409


def test_review_audit_exports_only_bound_annotation_eligible_items(tmp_path: Path):
    manifest = _content_manifest(tmp_path)
    pack = tmp_path / "pack"
    build_page_review_pack([manifest], pack, dpi=72)
    item = json.loads((pack / "review_pack_manifest.jsonl").read_text())
    review = build_page_review(_payload("eligible_for_annotation"), item, 1)
    reviews = tmp_path / "reviews"
    save_page_review(review, reviews)
    eligible = tmp_path / "eligible.jsonl"
    result = audit_page_reviews(
        pack, reviews, ROOT / "schemas/page_content_review_v001.schema.json",
        eligible_manifest=eligible,
    )
    row = json.loads(eligible.read_text())
    assert result["review_complete"] is True
    assert result["annotation_eligible_count"] == 1
    assert result["human_ground_truth_count"] == 0
    assert row["human_content_review"] is True
    assert row["benchmark_eligible"] is False
    assert len(row["content_review_sha256"]) == 64


def test_review_audit_reports_unreviewed_without_promoting(tmp_path: Path):
    manifest = _content_manifest(tmp_path)
    pack = tmp_path / "pack"
    build_page_review_pack([manifest], pack, dpi=72)
    result = audit_page_reviews(
        pack, tmp_path / "reviews", ROOT / "schemas/page_content_review_v001.schema.json",
    )
    assert result["reviewed_item_count"] == 0
    assert result["unreviewed_item_count"] == 1
    assert result["review_complete"] is False
    assert result["annotation_eligible_count"] == 0
    with pytest.raises(ValueError, match="while 1 items are unreviewed"):
        audit_page_reviews(
            pack, tmp_path / "reviews",
            ROOT / "schemas/page_content_review_v001.schema.json",
            eligible_manifest=tmp_path / "partial.jsonl",
        )
