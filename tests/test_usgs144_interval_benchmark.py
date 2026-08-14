import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_usgs144_interval_benchmark.py"
SPEC = importlib.util.spec_from_file_location("run_usgs144_interval_benchmark", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

def test_parse_usgs144_explicit_descriptions():
    text = """
    0 to 5 ft. - Surficial sediment, 4.5 ft of loess
    5 - 89 ft. - Basalt
    89 - 133 ft. - Sediment
    133 - 299 ft. - Basalt
    299 - 306 ft. - Sediment layers, silt with clay between
    306 - 627 ft. - Basalt
    627 - 635 ft. - Sand, red, hard.
    635 - 639 ft. - Basalt
    """
    intervals = MODULE.parse_intervals(text)
    assert len(intervals) == 8
    assert intervals[0]["top_depth_m"] == 0.0
    assert intervals[0]["lithology_normalized"] == "surficial sediment"
    assert intervals[4]["lithology_normalized"] == "sediment"
    assert intervals[-1]["bottom_depth_m"] == 639 * MODULE.FT_TO_M
