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
