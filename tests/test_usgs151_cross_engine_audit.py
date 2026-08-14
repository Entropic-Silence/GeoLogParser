import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_usgs151_cross_engine.py"
SPEC = importlib.util.spec_from_file_location("audit_usgs151_cross_engine", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

def test_parse_rapidocr_compact_lithology_line():
    row = MODULE.parse_region("LITHOLOGY:Basalt139.2-167.4ft", page=10, confidence=0.99)
    assert row is not None
    assert row["lithology_normalized"] == "basalt"
    assert row["top_depth_ft"] == 139.2
    assert row["bottom_depth_ft"] == 167.4

def test_parse_rejects_inverted_interval():
    assert MODULE.parse_region("LITHOLOGY:Sediment170-169ft", page=1, confidence=0.9) is None
