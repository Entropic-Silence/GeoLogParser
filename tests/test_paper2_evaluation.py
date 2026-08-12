import pytest

from geologparser.evaluation.paper2 import evaluate_paper2_ablation_matrix, evaluate_paper2_cases


def case(case_id, partition, reference, original, status, accepted, confidence, correct, review):
    return {
        "case_id": case_id,
        "reference": reference,
        "original": original,
        "decision": {"status": status, "accepted_value": accepted},
        "needs_review_label": review,
        "confidence": confidence,
        "correctness_label": correct,
        "calibration_partition": partition,
        "ground_truth_status": "double_verified",
    }


def test_paper2_evaluation_uses_held_out_test_and_reports_safety():
    cases = [
        case("fit1", "calibration", 1, 1, "ACCEPT_PROPOSAL", 1, 0.9, 1, False),
        case("fit2", "calibration", 2, 3, "NEEDS_REVIEW", None, 0.8, 0, True),
        case("test1", "test", 4.5, 4.8, "ACCEPT_PROPOSAL", 4.5, 0.8, 1, False),
        case("test2", "test", 6.0, 6.0, "NEEDS_REVIEW", None, 0.4, 0, True),
    ]
    result = evaluate_paper2_cases(cases, bins=2)
    assert result["calibration_case_count"] == 2
    assert result["test_case_count"] == 2
    assert result["correction"]["correction_success_rate"]["value"] == 1.0
    assert result["review"]["manual_review_recall"]["value"] == 1.0


def test_paper2_evaluation_rejects_auto_ground_truth():
    cases = [
        case("fit", "calibration", 1, 1, "NEEDS_REVIEW", None, 0.5, 1, False),
        case("test", "test", 1, 1, "NEEDS_REVIEW", None, 0.5, 1, False),
    ]
    cases[0]["ground_truth_status"] = "auto"
    with pytest.raises(ValueError, match="not human-verified"):
        evaluate_paper2_cases(cases)


def test_ablation_matrix_requires_identical_cases_and_one_module_removal():
    cases = [
        case("fit", "calibration", 1, 2, "NEEDS_REVIEW", None, .5, 0, True),
        case("test", "test", 1, 2, "ACCEPT_PROPOSAL", 1, .8, 1, False),
    ]
    result = evaluate_paper2_ablation_matrix({
        "full": {"disabled_modules": [], "cases": cases},
        "minus_constraints": {"disabled_modules": ["constraints"], "cases": cases},
    })
    assert result["variant_count"] == 2
    assert result["complete_expected_matrix"] is False
    with pytest.raises(ValueError, match="disable exactly"):
        evaluate_paper2_ablation_matrix({
            "full": {"disabled_modules": [], "cases": cases},
            "minus_constraints": {"disabled_modules": ["constraints", "rereading"], "cases": cases},
        })


def test_ablation_matrix_rejects_case_set_drift():
    cases = [
        case("fit", "calibration", 1, 2, "NEEDS_REVIEW", None, .5, 0, True),
        case("test", "test", 1, 2, "ACCEPT_PROPOSAL", 1, .8, 1, False),
    ]
    changed = [dict(item) for item in cases]
    changed[1]["reference"] = 9
    with pytest.raises(ValueError, match="identical GT case set"):
        evaluate_paper2_ablation_matrix({
            "full": {"disabled_modules": [], "cases": cases},
            "minus_vlm": {"disabled_modules": ["vlm"], "cases": changed},
        })
