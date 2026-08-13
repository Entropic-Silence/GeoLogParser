from pathlib import Path

from geologparser.datasets.compliance import review_registry_entry, review_registry


def test_open_structured_source_is_eligible_with_explicit_automated_scope(tmp_path: Path):
    entry = {
        "id": "open-pdf", "url": "https://example.test/data", "source_organization": "Example",
        "license": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "allowed_usage": "share and adapt", "downloadable": True, "format": "PDF borehole logs",
        "status": "acquired_verified",
    }
    result = review_registry_entry(entry, dataset_root=tmp_path)
    assert result["decision"] == "ELIGIBLE"
    assert result["review_type"] == "automated_compliance_review"
    assert result["human_reviewed"] is False


def test_contact_signal_is_excluded(tmp_path: Path):
    (tmp_path / "notes.txt").write_text("contact test@example.org", encoding="utf-8")
    entry = {
        "id": "contact", "url": "https://example.test/data", "source_organization": "Example",
        "license": "CC BY 4.0", "allowed_usage": "share", "downloadable": True,
        "format": "structured XLSX", "status": "acquired_verified",
    }
    assert review_registry_entry(entry, dataset_root=tmp_path)["decision"] == "EXCLUDE"


def test_ambiguous_license_is_quarantined():
    entry = {"id": "unknown", "url": "https://example.test", "source_organization": "Example", "license": "unclear", "status": "metadata_only"}
    assert review_registry_entry(entry)["decision"] == "AMBIGUOUS"


def test_registry_report_is_not_human_review():
    result = review_registry({"datasets": [{"id": "x", "url": "https://x", "source_organization": "X", "license": "CC0", "downloadable": True, "format": "structured CSV", "status": "verified"}]})
    assert result["human_reviewed"] is False
    assert result["reviews"][0]["decision"] == "ELIGIBLE"
