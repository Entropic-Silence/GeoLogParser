from geologparser.constraints import (
    ContinuityConstraint,
    DepthValidityConstraint,
    FinalDepthConsistencyConstraint,
    MonotonicityConstraint,
    ThicknessConsistencyConstraint,
    default_engine,
    engine_from_config,
    load_engine_config,
)
from pathlib import Path

import pytest
import yaml


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
    assert all(
        result.score == 1.0 if result.evaluated_count else result.score is None
        for result in results
    )


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
    with pytest.raises(ValueError, match="non-negative"):
        ThicknessConsistencyConstraint("-0.01")


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
    assert mismatch.status == "violated"
    assert mismatch.violations[0].code == "FINAL_DEPTH_MISMATCH"
    assert missing.passed is True
    assert missing.status == "not_evaluated"
    assert missing.evaluated_count == 0
    assert "missing" in missing.reason


def test_default_yaml_really_builds_all_configured_constraints():
    root = Path(__file__).resolve().parents[1]
    engine = load_engine_config(root / "configs/constraints/default_v001.yaml")
    assert [constraint.name for constraint in engine.constraints] == [
        constraint.name for constraint in default_engine().constraints
    ]
    assert engine.constraints[1].tolerance_m.as_tuple() == ThicknessConsistencyConstraint("0.05").tolerance_m.as_tuple()
    assert engine.constraints[6].field_names == ("rqd_percent", "core_recovery_percent")
    assert engine.constraints[7].confusables == ("O/0", "I/1", "l/1")


def test_constraint_config_disables_exactly_one_module_and_applies_parameters():
    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "configs/constraints/default_v001.yaml").read_text())
    config["continuity"]["enabled"] = False
    config["thickness_consistency"]["tolerance_m"] = "0.10"
    config["thickness_consistency"]["severity"] = "custom_warning"
    engine = engine_from_config(config)
    assert "C3_interval_continuity" not in [constraint.name for constraint in engine.constraints]
    assert len(engine.constraints) == 9
    thickness = next(item for item in engine.constraints if item.name == "C2_thickness_consistency")
    assert str(thickness.tolerance_m) == "0.10"
    assert thickness.severity == "custom_warning"


def test_constraint_config_rejects_unknown_section_key_and_version():
    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "configs/constraints/default_v001.yaml").read_text())
    config["continuity"]["tolrance_m"] = "0.1"
    with pytest.raises(ValueError, match="unknown keys"):
        engine_from_config(config)
    del config["continuity"]["tolrance_m"]
    config["version"] = "v999"
    with pytest.raises(ValueError, match="version"):
        engine_from_config(config)


def test_non_interval_directional_source_is_explicitly_not_evaluated():
    source_record = {
        "borehole": {"final_depth_m": {"value": 50.0}},
        "source_fields": {"coal_roof_depth_m": 45.0, "coal_seam_thickness_m": 8.0},
        "intervals": [],
    }
    results = default_engine().evaluate(source_record)
    assert all(result.status == "not_evaluated" for result in results)
    assert all(result.evaluated_count == 0 for result in results)
    assert all(result.score is None for result in results)
    assert all(result.passed is True for result in results)  # compatibility only
