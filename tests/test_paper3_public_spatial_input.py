import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_transformed_spatial_input_is_deidentified_and_recomputes_headlines() -> None:
    source_path = ROOT / "experiments/paper3/public/spatial_input_v001.jsonl"
    public = json.loads((ROOT / "experiments/paper3/public/spatial_recomputed_v001.json").read_text(encoding="utf-8"))
    private = json.loads((ROOT / "experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in source_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(rows) == public["document_count"] == private["document_count"] == 35
    assert sum(row["risk_acceptance"] for row in rows) == 15
    forbidden = ("record_id", "borehole_id", "pdf_path", "source_text", "easting", "northing", "absolute_x", "absolute_y")
    serialized = source_path.read_text(encoding="utf-8")
    assert all(token not in serialized for token in forbidden)
    for variant in ("raw", "reread", "risk"):
        observed = public["full_support_comparison"][variant]["aggregate"]["relative_absolute_volume_error"]
        expected = private["full_support_comparison"][variant]["aggregate"]["relative_absolute_volume_error"]
        assert abs(observed - expected) < 1e-6
