import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_usgs151_explicit_intervals.py"
SPEC = importlib.util.spec_from_file_location("audit_usgs151_explicit_intervals", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

def test_machine_consensus_requires_exact_page_lithology_and_boundaries(tmp_path):
    a = tmp_path / "a"; b = tmp_path / "b"; a.mkdir(); b.mkdir()
    (a / "page-10.txt").write_text("LITHOLOGY: Basalt 139.2-167.4 ft\nLITHOLOGY: Sediment 170-171 ft")
    (b / "page-10.txt").write_text("noise LITHOLOGY: Basalt 139.2 - 167.4 fi\nLITHOLOGY: Sediment 170-172 ft")
    ar = MODULE.parse_directory(a, "a")
    br = MODULE.parse_directory(b, "b")
    rows, summary = MODULE.audit(ar, br)
    assert len(rows) == 1
    assert rows[0]["top_depth_ft"] == 139.2
    assert rows[0]["human_reviewed"] is False
    assert summary["reader_a_only_count"] == 1
    assert summary["reader_b_only_count"] == 1
