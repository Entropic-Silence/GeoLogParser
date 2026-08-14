from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_swissgeol_thurgau_pairing.py"
SPEC = spec_from_file_location("audit_swissgeol_pairing", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_optional_final_depth_preserves_missing_values():
    assert MODULE.optional_final_depth({"borehole": {"final_depth_m": None}}) is None
    assert MODULE.optional_final_depth({"borehole": {"final_depth_m": "12.5"}}) == 12.5
