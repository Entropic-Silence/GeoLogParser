from geologparser.constraints import (
    CoordinateFormatConstraint,
    FieldTypeConsistencyConstraint,
    GroundwaterReasonablenessConstraint,
    PercentageRangeConstraint,
    StratumCodeSequenceConstraint,
    default_engine,
)
from geologparser.io import field


def test_groundwater_flags_negative_and_below_final_without_correction():
    negative = {"borehole": {"groundwater_depth_m": field(-1.0), "final_depth_m": field(10.0)}, "intervals": []}
    below = {"borehole": {"groundwater_depth_m": field(12.0), "final_depth_m": field(10.0)}, "intervals": []}
    assert GroundwaterReasonablenessConstraint().evaluate(negative).violations[0].code == "GROUNDWATER_NEGATIVE_DEPTH"
    result = GroundwaterReasonablenessConstraint().evaluate(below)
    assert result.violations[0].code == "GROUNDWATER_BELOW_FINAL_DEPTH"
    assert below["borehole"]["groundwater_depth_m"]["value"] == 12.0


def test_percentage_constraint_is_configurable():
    source = {"intervals": [{"rqd_percent": field(101), "custom_pct": field(-1)}]}
    default = PercentageRangeConstraint().evaluate(source)
    custom = PercentageRangeConstraint(("custom_pct",), minimum="-2", maximum="2").evaluate(source)
    assert default.violations[0].observed == {"rqd_percent": "101"}
    assert custom.passed


def test_percentage_constraint_rejects_invalid_configured_range():
    try:
        PercentageRangeConstraint(minimum="101", maximum="100")
    except ValueError as error:
        assert "minimum" in str(error)
    else:
        raise AssertionError("invalid range must fail during configuration")


def test_coordinate_confusable_and_digit_length_are_separate_violations():
    source = {"borehole": {
        "x_coordinate": field(None, source_text="29229O"),
        "y_coordinate": field(12, source_text="12"),
        "collar_elevation_m": field(8.2, source_text="8.2"),
    }, "intervals": []}
    result = CoordinateFormatConstraint(minimum_digits=4).evaluate(source)
    codes = [violation.code for violation in result.violations]
    assert "NUMERIC_OCR_CONFUSABLE" in codes
    assert "NUMERIC_DIGIT_LENGTH_SUSPICIOUS" in codes
    assert not any("collar_elevation" in field for violation in result.violations for field in violation.affected_fields)


def test_stratum_sequence_is_weak_and_handles_circled_numbers():
    source = {"intervals": [
        {"stratum_code_raw": field("①")},
        {"stratum_code_raw": field("②")},
        {"stratum_code_raw": field("④")},
        {"stratum_code_raw": field("④")},
    ]}
    result = StratumCodeSequenceConstraint().evaluate(source)
    assert result.severity == "weak_warning"
    assert [violation.code for violation in result.violations] == ["STRATUM_CODE_JUMP", "STRATUM_CODE_DUPLICATE"]


def test_field_type_consistency_detects_both_column_swap_directions():
    source = {"intervals": [{
        "top_depth_m": field(None, source_text="粉质黏土"),
        "bottom_depth_m": field(4.5, source_text="4.50"),
        "thickness_m": field(4.5, source_text="4.50"),
        "lithology_raw": field("4.50"),
        "description_raw": field("可塑"),
    }]}
    result = FieldTypeConsistencyConstraint().evaluate(source)
    assert {violation.code for violation in result.violations} == {
        "TEXT_FIELD_CONTAINS_NUMERIC_VALUE", "NUMERIC_FIELD_CONTAINS_GEOLOGICAL_TEXT"
    }


def test_default_engine_exposes_all_ten_constraints():
    names = [constraint.name for constraint in default_engine().constraints]
    assert names == [f"C{i}_{suffix}" for i, suffix in (
        (1, "depth_validity"), (2, "thickness_consistency"), (3, "interval_continuity"),
        (4, "depth_monotonicity"), (5, "final_depth_consistency"),
        (6, "groundwater_reasonableness"), (7, "percentage_range"),
        (8, "coordinate_format"), (9, "stratum_code_sequence"),
        (10, "field_type_consistency"),
    )]
