"""Ground-Truth-gated batch evaluation for Paper II correction experiments."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from geologparser.confidence import TemperatureScaler

from .correction import correction_safety_metrics, review_detection_metrics
from .metrics import brier_score, expected_calibration_error


REQUIRED_CASE_KEYS = {
    "case_id", "reference", "original", "decision", "needs_review_label",
    "confidence", "correctness_label", "calibration_partition",
}


def evaluate_paper2_cases(
    cases: Sequence[Mapping[str, Any]], *, bins: int = 10,
) -> dict[str, Any]:
    """Evaluate correction, triage, and held-out confidence calibration.

    The calibration partition is used only to fit temperature. Metrics are
    computed only on the disjoint ``test`` partition. This API deliberately
    rejects auto labels and unknown GT status.
    """
    if not cases:
        raise ValueError("Paper II evaluation requires cases")
    seen: set[str] = set()
    for case in cases:
        missing = REQUIRED_CASE_KEYS - case.keys()
        if missing:
            raise ValueError(f"case lacks required keys: {', '.join(sorted(missing))}")
        case_id = str(case["case_id"])
        if case_id in seen:
            raise ValueError(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        if case.get("ground_truth_status") not in {"single_verified", "double_verified", "expert_verified"}:
            raise ValueError(f"case {case_id} is not human-verified Ground Truth")
        if case["calibration_partition"] not in {"calibration", "test"}:
            raise ValueError("calibration_partition must be calibration or test")
        if not isinstance(case["decision"], Mapping):
            raise ValueError("decision must be an object")
        if case["correctness_label"] not in (0, 1) or not isinstance(case["needs_review_label"], bool):
            raise ValueError("correctness_label must be binary and needs_review_label boolean")
        confidence = case["confidence"]
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be within [0, 1]")
    fit_cases = [case for case in cases if case["calibration_partition"] == "calibration"]
    test_cases = [case for case in cases if case["calibration_partition"] == "test"]
    if not fit_cases or not test_cases:
        raise ValueError("disjoint non-empty calibration and test partitions are required")
    scaler = TemperatureScaler.fit(
        [int(case["correctness_label"]) for case in fit_cases],
        [float(case["confidence"]) for case in fit_cases],
    )
    references = [case["reference"] for case in test_cases]
    originals = [case["original"] for case in test_cases]
    decisions = [case["decision"] for case in test_cases]
    labels = [int(case["correctness_label"]) for case in test_cases]
    raw_confidences = [float(case["confidence"]) for case in test_cases]
    calibrated = scaler.transform(raw_confidences)
    safety = correction_safety_metrics(references, originals, decisions)
    review = review_detection_metrics(
        [bool(case["needs_review_label"]) for case in test_cases], decisions,
    )
    raw_brier = brier_score(labels, raw_confidences)
    raw_ece = expected_calibration_error(labels, raw_confidences, bins=bins)
    calibrated_brier = brier_score(labels, calibrated)
    calibrated_ece = expected_calibration_error(labels, calibrated, bins=bins)
    return {
        "protocol": "paper2_ground_truth_gated_v001",
        "calibration_case_count": len(fit_cases),
        "test_case_count": len(test_cases),
        "temperature": scaler.temperature,
        "correction": {name: result.to_dict() for name, result in safety.items()},
        "review": {name: result.to_dict() for name, result in review.items()},
        "confidence": {
            "raw_brier_score": raw_brier.to_dict(),
            "raw_expected_calibration_error": raw_ece.to_dict(),
            "calibrated_brier_score": calibrated_brier.to_dict(),
            "calibrated_expected_calibration_error": calibrated_ece.to_dict(),
        },
    }
