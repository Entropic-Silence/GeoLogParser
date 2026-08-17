import json

import pytest

from geologparser.datasets import bgs
from geologparser.datasets.manifest import DatasetFile, sha256_file, write_jsonl


def test_sha256_and_jsonl_are_stable(tmp_path):
    source = tmp_path / "x.pdf"
    source.write_bytes(b"%PDF-test")
    record = DatasetFile(
        dataset_id="d", source_record_id="1", source_url="https://example.test/1",
        local_path=str(source), sha256=sha256_file(source), size_bytes=9,
        media_type="application/pdf", access_date="2026-08-12", license_id="test",
        redistribution="no", metadata={"b": 2, "a": 1},
    )
    manifest = tmp_path / "manifest.jsonl"
    write_jsonl([record], manifest)
    decoded = json.loads(manifest.read_text(encoding="utf-8"))
    assert decoded["sha256"] == sha256_file(source)
    assert decoded["metadata"] == {"a": 1, "b": 2}


def test_bgs_download_requires_direct_public_api(monkeypatch, tmp_path):
    monkeypatch.setattr(bgs, "fetch_metadata", lambda ids: {
        12: {"BGS_ID": 12, "SCAN_URL": "http://shop.bgs.ac.uk/GeoRecords"}
    })
    with pytest.raises(ValueError, match="not a direct public API scan"):
        bgs.download_fixed_sample([12], tmp_path, "2026-08-12")


def test_bgs_fixed_sample_manifest_without_network(monkeypatch, tmp_path):
    monkeypatch.setattr(bgs, "fetch_metadata", lambda ids: {
        4: {"BGS_ID": 4, "REFERENCE": "SD20NE4", "SCAN_URL": bgs.SCAN_URL.format(bgs_id=4)}
    })
    monkeypatch.setattr(bgs, "_get", lambda url, timeout=120: b"%PDF-fixture")
    path = bgs.download_fixed_sample([4, 4], tmp_path, "2026-08-12")
    rows = path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    assert json.loads(rows[0])["source_record_id"] == "4"


def test_bgs_existing_pdf_is_frozen_not_redownloaded(monkeypatch, tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    existing = raw / "bgs_4.pdf"
    existing.write_bytes(b"%PDF-original")
    monkeypatch.setattr(bgs, "fetch_metadata", lambda ids: {
        4: {"BGS_ID": 4, "SCAN_URL": bgs.SCAN_URL.format(bgs_id=4)}
    })
    monkeypatch.setattr(bgs, "_get", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network should not run")))
    bgs.download_fixed_sample([4], tmp_path, "2026-08-12")
    assert existing.read_bytes() == b"%PDF-original"
