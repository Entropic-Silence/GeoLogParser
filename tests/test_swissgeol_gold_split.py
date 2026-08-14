import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "split_swissgeol_gold.py"
SPEC = spec_from_file_location("split_swissgeol_gold", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def write_manifest(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def rows() -> list[dict]:
    return [
        {"record_id": "A", "pdf_sha256": "hash-a", "interval_count": 2},
        {"record_id": "B", "pdf_sha256": "hash-b", "interval_count": 3},
        {"record_id": "C", "pdf_sha256": "hash-c", "interval_count": 4},
        {"record_id": "D", "pdf_sha256": "hash-d", "interval_count": 5},
    ]


def test_split_is_disjoint_deterministic_and_immutable(tmp_path: Path):
    source = tmp_path / "gold.jsonl"
    write_manifest(source, rows())
    first = MODULE.freeze_split(source, tmp_path / "one", version="v003")
    second = MODULE.freeze_split(source, tmp_path / "two", version="v003")
    assert first["development_documents"] == 2
    assert first["heldout_documents"] == 2
    assert first["development_manifest_sha256"] == second["development_manifest_sha256"]
    assert first["heldout_manifest_sha256"] == second["heldout_manifest_sha256"]
    with pytest.raises(FileExistsError):
        MODULE.freeze_split(source, tmp_path / "one", version="v003")


def test_duplicate_pdf_hashes_never_cross_partitions(tmp_path: Path):
    source_rows = rows() + [
        {"record_id": "A_COPY", "pdf_sha256": "hash-a", "interval_count": 2},
    ]
    source = tmp_path / "gold.jsonl"
    write_manifest(source, source_rows)
    summary = MODULE.freeze_split(source, tmp_path / "split", version="v003")
    development = MODULE.load_jsonl(Path(summary["development_manifest"]))
    heldout = MODULE.load_jsonl(Path(summary["heldout_manifest"]))
    development_hashes = {row["pdf_sha256"] for row in development}
    heldout_hashes = {row["pdf_sha256"] for row in heldout}
    assert development_hashes.isdisjoint(heldout_hashes)
    assert summary["duplicate_pdf_document_count"] == 1


def test_split_rejects_record_or_pdf_overlap_with_prior_freeze(tmp_path: Path):
    source = tmp_path / "gold.jsonl"
    excluded = tmp_path / "excluded.jsonl"
    write_manifest(source, rows())
    write_manifest(excluded, [{"record_id": "OLD", "pdf_sha256": "hash-c", "interval_count": 1}])
    with pytest.raises(ValueError, match="overlaps excluded"):
        MODULE.freeze_split(
            source,
            tmp_path / "split",
            version="v003",
            excluded_manifests=[excluded],
        )
