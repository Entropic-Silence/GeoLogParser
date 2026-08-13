import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_swissgeol_audit_rejects_mismatched_layer_fixture(tmp_path: Path):
    path = ROOT / "scripts/audit_swissgeol_example_groundtruth.py"
    spec = importlib.util.spec_from_file_location("swissgeol_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    source = Path("/data/GeoLogParser/candidates/swissgeol-boreholes-dataextraction")
    result = module.audit(source)
    assert result["metadata_groundtruth_matches_pdf"] is True
    assert result["layers_groundtruth_matches_pdf"] is False
    assert result["layer_fixture_decision"] == "EXCLUDE_MISMATCHED_FROM_GOLD"
