import pytest

from geologparser.evaluation import (
    ERROR_TAXONOMY_V001,
    character_error_rate,
    classify_field_error,
    error_distribution,
    numeric_character_error_rate,
    normalized_edit_similarity,
    word_error_rate,
)


def test_cer_is_micro_levenshtein():
    result = character_error_rate(["abc", "xy"], ["adc", "x"])
    assert result.numerator == 2
    assert result.denominator == 5
    assert result.value == pytest.approx(0.4)


def test_wer_contract_is_whitespace_tokenization():
    result = word_error_rate(["粉质 黏土", "fine sand"], ["粉质 土", "fine sand"])
    assert result.numerator == 1
    assert result.denominator == 4


def test_numeric_cer_preserves_decimal_point_errors():
    result = numeric_character_error_rate(["深度 4.50 m"], ["深度 450 m"])
    assert result.numerator == 1
    assert result.denominator == 4
    assert result.details["filtered_alphabet"] == "0-9.-+"


def test_empty_reference_insertions_are_traced_not_divided_by_zero():
    result = character_error_rate([""], ["abc"])
    assert result.value is None
    assert result.details["empty_reference_insertions"] == 3


def test_normalized_edit_similarity_is_macro_and_handles_empty_pair():
    result = normalized_edit_similarity(["abc", ""], ["ab", ""])
    assert result.value == pytest.approx(((2 / 3) + 1) / 2)
    assert result.denominator == 2


def test_error_classifier_and_distribution_preserve_unknowns():
    assert classify_field_error("final_depth_m", "4.50", "450") == "decimal_point_error"
    assert classify_field_error("lithology_raw", "粉质黏土", "细砂") == "lithology_semantic_error"
    assert classify_field_error("x", None, "invented") == "hallucination"
    distribution = error_distribution([
        {"error_type": "hallucination"}, {"error_type": "custom_unknown"},
    ])
    assert distribution["counts"]["hallucination"] == 1
    assert distribution["unknown"] == {"custom_unknown": 1}
    assert len(distribution["counts"]) == len(ERROR_TAXONOMY_V001)
