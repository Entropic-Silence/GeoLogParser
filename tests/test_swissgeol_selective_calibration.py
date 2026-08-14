from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_swissgeol_selective_calibration.py"
SPEC = spec_from_file_location("run_swissgeol_selective_calibration", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_fixed_bin_calibration_and_brier_are_exact_for_toy_values():
    labels = [1, 0]
    probabilities = [0.8, 0.2]
    ece, bins = MODULE.fixed_bin_calibration(labels, probabilities, bins=5)
    assert abs(ece - 0.2) < 1e-12
    assert abs(MODULE.brier_score(labels, probabilities) - 0.04) < 1e-12
    assert sum(row["count"] for row in bins) == 2


def test_signature_uses_only_reference_blind_decision_features():
    method = {
        "decision": "KEEP_FIRST_PASS",
        "triggers": [],
        "final_intervals": [{"top_depth_m": 0.0, "bottom_depth_m": 1.0}],
    }
    peer = {"predicted_intervals": [{"top_depth_m": 0.0, "bottom_depth_m": 1.0}]}
    assert MODULE.signature(method, peer) == "KEEP_FIRST_PASS|trigger=0|peer_exact=1"
