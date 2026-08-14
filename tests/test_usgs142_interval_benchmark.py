import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_usgs142_interval_benchmark.py"
SPEC = importlib.util.spec_from_file_location("run_usgs142_interval_benchmark", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_parse_usgs142_explicit_legend_intervals():
    text = """
    506 to 561 ft - Basalt
    561 to 574 ft - Sediment
    574 to 674 ft - Basalt
    674 to 680 ft - Sediment
    680 to 687 ft - Basalt
    687 to 691 ft - Sediment
    691 to 739 ft - Basalt
    739 to 794 - Sediment
    794 to 805 ft - Basalt
    805 to 816 ft - Sediment
    816 to 836 ft - Basalt
    836 to bottom - Sediment
    """
    intervals = MODULE.parse_intervals(text, 844.0)
    assert len(intervals) == 12
    assert intervals[0]["top_depth_m"] == 506 * MODULE.FT_TO_M
    assert intervals[-1]["bottom_depth_m"] == 844 * MODULE.FT_TO_M
    assert intervals[1]["lithology_normalized"] == "sediment"
