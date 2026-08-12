from geologparser.evaluation import correction_safety_metrics, review_detection_metrics


def decision(status, value=None):
    return {"status": status, "accepted_value": value}


def test_correction_safety_separates_improvement_and_false_correction():
    metrics = correction_safety_metrics(
        references=[1.2, 2.0, 3.0],
        originals=[1.5, 2.0, 4.0],
        decisions=[decision("ACCEPT_PROPOSAL", 1.2), decision("ACCEPT_PROPOSAL", 2.2), decision("NEEDS_REVIEW")],
    )
    assert metrics["automatic_correction_rate"].value == 2 / 3
    assert metrics["correction_success_rate"].value == 0.5
    assert metrics["false_correction_rate"].value == 0.5
    assert metrics["incorrect_correction_rate"].value == 0.5


def test_no_corrections_yields_undefined_safety_not_zero():
    metrics = correction_safety_metrics([1], [2], [decision("NEEDS_REVIEW")])
    assert metrics["false_correction_rate"].value is None
    assert metrics["false_correction_rate"].denominator == 0


def test_review_detection_reports_recall_and_rate():
    metrics = review_detection_metrics(
        [True, True, False],
        [decision("NEEDS_REVIEW"), decision("ACCEPT_PROPOSAL", 1), decision("NEEDS_REVIEW")],
    )
    assert metrics["manual_review_recall"].value == 0.5
    assert metrics["manual_review_precision"].value == 0.5
    assert metrics["review_rate"].value == 2 / 3
    assert metrics["auto_accept_rate"].value == 1 / 3
    assert metrics["auto_accept_error_rate"].value == 1
