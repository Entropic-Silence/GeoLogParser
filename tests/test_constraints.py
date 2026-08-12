from geologparser.constraints import (
    ContinuityConstraint,
    DepthValidityConstraint,
    FinalDepthConsistencyConstraint,
    MonotonicityConstraint,
    ThicknessConsistencyConstraint,
    default_engine,
)


def record(intervals, final_depth=4.5):
    return {"borehole": {"final_depth_m": {"value": final_depth}}, "intervals": intervals}


def interval(top, bottom, thickness):
    return {
        "top_depth_m": {"value": top},
        "bottom_depth_m": {"value": bottom},
        "thickness_m": {"value": thickness},
    }


def test_valid_record_passes_all_constraints():
    results = default_engine("0.01").evaluate(record([
        interval(0.0, 1.2, 1.2), interval(1.2, 4.5, 3.3)
    ]))
    assert all(result.passed for result in results)
    assert all(result.score == 1.0 for result in results)


def test_depth_validity_flags_inversion_without_mutating():
    source = record([interval(5.3, 3.8, 1.5)], final_depth=3.8)
    result = DepthValidityConstraint().evaluate(source)
    assert not result.passed
    assert result.violations[0].code == "DEPTH_NOT_INCREASING"
    assert source["intervals"][0]["bottom_depth_m"]["value"] == 3.8


def test_thickness_tolerance_is_configurable_and_decimal_safe():
    source = record([interval(0.0, 1.0, 1.02)], final_depth=1.0)
    assert ThicknessConsistencyConstraint("0.01").evaluate(source).passed is False
    assert ThicknessConsistencyConstraint("0.02").evaluate(source).passed is True


def test_continuity_distinguishes_gap_and_overlap():
    gap = ContinuityConstraint("0.05").evaluate(record([
        interval(0, 1, 1), interval(1.2, 2, 0.8)
    ], 2))
    overlap = ContinuityConstraint("0.05").evaluate(record([
        interval(0, 1, 1), interval(0.8, 2, 1.2)
    ], 2))
    assert gap.violations[0].code == "INTERVAL_GAP"
    assert overlap.violations[0].code == "INTERVAL_OVERLAP"


def test_monotonicity_flags_reversed_sequence():
    result = MonotonicityConstraint().evaluate(record([
        interval(4, 5, 1), interval(2, 3, 1)
    ], 5))
    assert not result.passed
    assert result.violations[0].code == "DEPTH_SEQUENCE_INVERSION"


def test_final_depth_mismatch_and_missing_are_distinct():
    mismatch = FinalDepthConsistencyConstraint("0.05").evaluate(
        record([interval(0, 4.5, 4.5)], final_depth=5.0)
    )
    missing = FinalDepthConsistencyConstraint().evaluate(
        record([interval(0, None, None)], final_depth=None)
    )
    assert mismatch.passed is False
    assert mismatch.violations[0].code == "FINAL_DEPTH_MISMATCH"
    assert missing.passed is True
    assert missing.evaluated_count == 0
    assert "missing" in missing.reason

