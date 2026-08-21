import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_candidate_pool_is_pseudonymized_and_recomputable() -> None:
    source = ROOT / "experiments/paper2/public/candidate_pool_v001.jsonl"
    recomputed = ROOT / "experiments/paper2/public/candidate_pool_recomputed_v001.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    outputs = [json.loads(line) for line in recomputed.read_text(encoding="utf-8").splitlines() if line]
    assert len(rows) == len(outputs) == 200
    assert sum(len(row["candidate_pool"]) for row in rows) == 2225
    serialized = source.read_text(encoding="utf-8")
    for forbidden in ("record_id", "pdf_path", "source_text", '"bbox"', '"text"', "ocr_regions_path", "county"):
        assert forbidden not in serialized
    assert all(row["record_key"].startswith("rec_") for row in rows)
    assert all("variants" in row for row in outputs)
