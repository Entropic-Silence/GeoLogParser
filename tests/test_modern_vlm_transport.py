import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_transport_protocol_separates_source_units_and_excludes_bgs():
    protocol = load_json("configs/experiments/paper1_modern_vlm_transport_v001.json")
    assert protocol["panels"]["california_v003_page20"]["metres_per_printed_unit"] == 0.3048
    assert protocol["panels"]["swissgeol_heldout"]["metres_per_printed_unit"] == 1.0
    assert all("BGS" not in json.dumps(panel) for panel in protocol["panels"].values())
    assert any("BGS v003" in item for item in protocol["exclusions"])


def test_transport_aggregate_has_completed_evidence_only():
    aggregate = load_json("experiments/paper1/analysis/modern_vlm_transport_comparison_v001.json")
    assert aggregate["status"] == "COMPLETED_EXPLORATORY_TRANSPORT_EVIDENCE"
    assert aggregate["anti_leakage"]["bgs_v003_used"] is False
    assert aggregate["anti_leakage"]["interrupted_runs_included"] is False
    model_ids = {entry["model_id"] for entry in aggregate["models"]}
    assert "Qwen/Qwen3-VL-4B-Instruct" in model_ids
    assert "PaddlePaddle/PaddleOCR-VL-1.6" in model_ids
    assert "opendatalab/MinerU2.5-Pro-2604-1.2B" in model_ids
    assert "P1_TRANSPORT_QWEN3VL4B_CALIFORNIA_V003_001" not in json.dumps(aggregate)


def test_transport_specialist_rows_are_marked_as_decoder_coverage():
    aggregate = load_json("experiments/paper1/analysis/modern_vlm_transport_comparison_v001.json")
    for entry in aggregate["models"]:
        if entry["interface"] == "direct page-to-JSON":
            continue
        result = entry["results"]["swissgeol_heldout"]
        assert result["decoded_page_rate"] == 1.0
        assert result["interval_decoder_output_rate"] == 0.0
        assert "decoder" in result["interpretation"].lower()


def test_qwen_runtime_discloses_non_reference_2080ti_path():
    config = load_json("configs/models/qwen38_fp8_modern_vlm_v002.json")
    assert "modified" in config["hardware"]
    assert "non-official" in config["runtime_provenance_note"]
    assert config["runtime_provenance"]["reconstruction_status"] == "partially_reconstructable"
