import importlib.util
import json
from pathlib import Path

import pymupdf
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_mendeley_sedlog_manifest",
    ROOT / "scripts/build_mendeley_sedlog_manifest.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _fixture_pdf(path: Path):
    document = pymupdf.open()
    for page_id in MODULE.EXPECTED_PAGE_IDS:
        page = document.new_page(width=510, height=1000)
        page.insert_text((20, 30), page_id)
    document.save(path)


def test_sedlog_manifest_preserves_non_gt_boundary(monkeypatch, tmp_path: Path):
    raw = tmp_path / "raw"
    raw.mkdir()
    source = raw / "SedLog_drilling_cores.pdf"
    _fixture_pdf(source)
    monkeypatch.setattr(MODULE, "EXPECTED_SIZE", source.stat().st_size)
    monkeypatch.setattr(MODULE, "EXPECTED_SHA256", MODULE.sha256_file(source))

    result = MODULE.build_manifest(tmp_path)

    rows = [json.loads(line) for line in (tmp_path / "metadata/manifest.jsonl").read_text().splitlines()]
    assert len(rows) == 18
    assert all(row["benchmark_eligible"] is False for row in rows)
    assert all(row["annotation_status"] == "unannotated" for row in rows)
    assert result["human_ground_truth_pages"] == 0
    assert result["benchmark_eligible_pages"] == 0


def test_sedlog_manifest_rejects_hash_mismatch(tmp_path: Path):
    raw = tmp_path / "raw"
    raw.mkdir()
    source = raw / "SedLog_drilling_cores.pdf"
    source.write_bytes(b"wrong")
    with pytest.raises(ValueError, match="size does not match"):
        MODULE.build_manifest(tmp_path)
