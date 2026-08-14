from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_swissgeol_constraint_reread.py"
SPEC = spec_from_file_location("run_swissgeol_constraint_reread", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_v2_accepts_peer_sequence_with_repeated_exact_highres_support():
    first = [(0.0, 2.0), (2.0, 88.0), (88.0, 200.0)]
    peer = [(0.0, 88.0), (88.0, 200.0)]
    accepted, reason = MODULE.select_v2_candidate(first, peer, Counter({tuple(peer): 6}))
    assert accepted == tuple(peer)
    assert reason == "peer_exact_highres_consensus"


def test_v2_accepts_complementary_shallow_and_deep_evidence():
    first = [(0.0, 12.0)]
    peer = [(0.0, 12.0), (12.0, 170.0)]
    highres = ((12.0, 170.0),)
    accepted, reason = MODULE.select_v2_candidate(first, peer, Counter({highres: 6}))
    assert accepted == tuple(peer)
    assert reason == "peer_complementary_highres_consensus"


def test_v2_rejects_nonzero_start_and_uncorroborated_peer():
    accepted, _ = MODULE.select_v2_candidate([], [(42.0, 200.0)], Counter({((42.0, 200.0),): 5}))
    assert accepted is None
    accepted, _ = MODULE.select_v2_candidate(
        [(0.0, 14.0), (14.0, 200.0)],
        [(0.0, 1.0)],
        Counter({((0.0, 44.0), (44.0, 200.0)): 3}),
    )
    assert accepted is None


def test_v2_rejects_peer_that_splits_a_supported_first_pass_interval():
    first = [(0.0, 3.0), (3.0, 18.0), (18.0, 170.0)]
    peer = [(0.0, 2.0), (2.0, 3.0), (3.0, 18.0), (18.0, 170.0)]
    accepted, reason = MODULE.select_v2_candidate(first, peer, Counter({tuple(first): 7}))
    assert accepted is None
    assert reason == "first_pass_conflicts_with_peer"
