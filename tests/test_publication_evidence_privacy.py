import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANNED_KEYS = {
    "record_id", "borehole_id", "project_name", "county", "filename",
    "source_file", "document_path", "pdf_path", "pdf_sha256",
    "reference_path", "source_text", "source_bbox", "display_bbox", "bbox",
    "regions", "ocr_regions_path",
}


def walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def test_document_outputs_are_deidentified_and_joinable():
    root = ROOT / "publication_evidence/document_outputs"
    files = sorted(root.rglob("*.jsonl"))
    assert files
    for path in files:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            row = json.loads(line)
            assert row.get("record_key"), (path, line_number)
            assert BANNED_KEYS.isdisjoint(set(walk_keys(row))), (path, line_number)


def test_public_reanalysis_inputs_are_deidentified_and_manifested():
    root = ROOT / "publication_evidence/analysis_inputs"
    manifest = json.loads((ROOT / "publication_evidence/manifest.json").read_text(encoding="utf-8"))
    assert manifest["publication_evidence_schema_version"] == "publication_evidence_v002"
    assert manifest["analysis_input_file_count"] == 6
    assert len(manifest["analysis_inputs"]) == 6

    candidate_path = root / "paper2/candidate_pool_v001.jsonl"
    spatial_path = root / "paper3/spatial_input_v001.jsonl"
    assert candidate_path.is_file()
    assert spatial_path.is_file()
    for path in (candidate_path, spatial_path):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            row = json.loads(line)
            assert row.get("record_key"), (path, line_number)
            assert BANNED_KEYS.isdisjoint(set(walk_keys(row))), (path, line_number)

    spatial_text = spatial_path.read_text(encoding="utf-8")
    for token in ("easting", "northing", "absolute_x", "absolute_y", "absolute origin"):
        assert token not in spatial_text
