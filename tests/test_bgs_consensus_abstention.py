import importlib.util
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "run_bgs_consensus_abstention",
    Path(__file__).resolve().parents[1] / "scripts/run_bgs_consensus_abstention.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
_equal, _score = MODULE._equal, MODULE._score


def test_consensus_requires_two_non_null_equal_values():
    assert _equal("BH-1", "BH-1", 1e-6)
    assert _equal(4.5, 4.5000001, 1e-6)
    assert not _equal(None, None, 1e-6)
    assert not _equal(4.5, 4.6, 1e-6)


def test_score_separates_coverage_accuracy_and_review_recall():
    rows = [
        {"expected": 1, "decision": "ACCEPT_CONSENSUS", "accepted_correct": True, "review_needed": False},
        {"expected": 2, "decision": "ACCEPT_CONSENSUS", "accepted_correct": False, "review_needed": False},
        {"expected": 3, "decision": "NEEDS_REVIEW", "accepted_correct": False, "review_needed": True},
        {"expected": None, "decision": "NEEDS_REVIEW", "accepted_correct": False, "review_needed": False},
    ]
    result = _score(rows)
    assert result["reference_count"] == 3
    assert result["accepted_count"] == 2
    assert result["coverage"] == 2 / 3
    assert result["accepted_accuracy"] == 0.5
    assert result["manual_review_recall"] == 0.5
