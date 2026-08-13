import json
from pathlib import Path

import pytest

from geologparser.rereading import Candidate, decide_reread, rank_candidates


ROOT = Path(__file__).resolve().parents[1]


def record():
    return json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))


def test_reread_accepts_only_constraint_reducing_clear_candidate_without_mutation():
    source = record()
    source["intervals"][1]["top_depth_m"]["value"] = 1.5
    original = json.dumps(source, sort_keys=True)
    decision = decide_reread(source, "intervals[1].top_depth_m", [
        Candidate(1.2, "ocr", "1.20", 0.95, 0.95, 0.9),
        Candidate(1.2, "vlm", "1.20", 0.9, 0.9, 0.9),
        Candidate(1.5, "ocr_alt", "1.50", 0.6, 0.5, 0.9),
    ])
    assert decision.status == "ACCEPT_PROPOSAL"
    assert decision.accepted_value == 1.2
    assert decision.proposed_record["intervals"][1]["top_depth_m"]["value"] == 1.2
    assert decision.proposed_record["intervals"][1]["top_depth_m"]["validation_status"] == "needs_review"
    assert json.dumps(source, sort_keys=True) == original


def test_reread_abstains_when_candidate_does_not_reduce_violation():
    source = record()
    decision = decide_reread(source, "intervals[1].top_depth_m", [
        Candidate(1.2, "ocr", "1.20", 0.99, 0.99, 0.99),
    ])
    assert decision.status == "NEEDS_REVIEW"
    assert decision.reason == "best_candidate_does_not_reduce_target_constraint_violations"


def test_reread_abstains_on_ambiguous_top_candidates():
    source = record()
    source["intervals"][1]["top_depth_m"]["value"] = 1.5
    decision = decide_reread(source, "intervals[1].top_depth_m", [
        Candidate(1.2, "ocr", "1.20", 0.9, 0.9, 0.9),
        Candidate(1.19, "vlm", "1.19", 0.9, 0.9, 0.9),
    ], minimum_margin=0.1)
    assert decision.status == "NEEDS_REVIEW"
    assert decision.reason == "top_candidates_ambiguous"


def test_same_value_from_multiple_models_is_agreement_not_ambiguity():
    source = record()
    source["intervals"][1]["top_depth_m"]["value"] = 1.5
    decision = decide_reread(source, "intervals[1].top_depth_m", [
        Candidate(1.2, "ocr", "1.20", 0.9, 0.9, 0.9),
        Candidate(1.2, "vlm", "1.20", 0.9, 0.9, 0.9),
    ], minimum_margin=0.5)
    assert decision.status == "ACCEPT_PROPOSAL"


def test_ranking_rejects_invalid_weights_and_evidence():
    with pytest.raises(ValueError, match="sum"):
        rank_candidates(record(), "borehole.final_depth_m", [Candidate(4.5, "ocr")], {"evidence": 1, "agreement": 1, "constraint": 1})
    with pytest.raises(ValueError, match="within"):
        rank_candidates(record(), "borehole.final_depth_m", [Candidate(4.5, "ocr", model_confidence=1.2)])


def test_reread_without_candidates_abstains():
    decision = decide_reread(record(), "borehole.final_depth_m", [])
    assert decision.status == "NEEDS_REVIEW"
    assert decision.reason == "no_candidates"


def test_reread_forces_review_when_one_reader_sees_multiple_values():
    source = record()
    source["intervals"][1]["top_depth_m"]["value"] = 1.5
    decision = decide_reread(source, "intervals[1].top_depth_m", [
        Candidate(1.2, "wide_roi_ocr", "1.20", 0.99, 0.99, 0.99),
        Candidate(15.0, "wide_roi_ocr", "15.00", 0.40, 0.40, 0.99),
        Candidate(1.2, "vlm", "1.20"),
    ])
    assert decision.status == "NEEDS_REVIEW"
    assert decision.reason == "reader_emitted_multiple_distinct_values"
    assert decision.accepted_value is None


def test_candidate_constraint_score_ignores_unrelated_borehole_warning():
    source = record()
    source["borehole"]["groundwater_depth_m"]["value"] = -1.0
    score = rank_candidates(source, "borehole.collar_elevation_m", [
        Candidate(100.0, "ocr", "100.0", 0.9, 0.9, 0.9),
    ])[0]
    assert score.violations_before == 0
    assert score.violations_after == 0
    assert score.constraint_score == 0.5
