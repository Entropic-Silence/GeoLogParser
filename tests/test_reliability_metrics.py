import pytest

from geologparser.evaluation import (
    critical_numerical_error_rate, hierarchical_classification_metrics,
)


def test_critical_numerical_error_counts_missing_and_over_threshold():
    metric = critical_numerical_error_rate(
        [1.0, 2.0, 3.0, None], [1.01, 2.2, None, 99.0], threshold=0.05,
    )
    assert metric.value == 2 / 3
    assert metric.details["missing_prediction_count"] == 1
    assert metric.details["over_threshold_count"] == 1
    assert metric.details["missing_reference_count"] == 1


def test_critical_numerical_threshold_is_inclusive():
    metric = critical_numerical_error_rate([1.0], [1.05], threshold=0.05)
    assert metric.value == 0
    with pytest.raises(ValueError, match="non-negative"):
        critical_numerical_error_rate([1.0], [1.0], threshold=-0.1)


def test_hierarchical_metrics_reward_shared_ancestors_but_keep_exact_separate():
    values = hierarchical_classification_metrics(
        [["Rock", "Sedimentary", "Sandstone", "Fine sandstone"]],
        [["Rock", "Sedimentary", "Sandstone"]],
    )
    assert values["hierarchical_precision"].value == 1
    assert values["hierarchical_recall"].value == 0.75
    assert values["hierarchical_path_exact_match"].value == 0


def test_hierarchical_paths_reject_cycles_or_duplicate_nodes():
    with pytest.raises(ValueError, match="repeat"):
        hierarchical_classification_metrics([["Soil", "Soil"]], [["Soil"]])


def test_hierarchical_metrics_do_not_reward_missing_reference_paths():
    values = hierarchical_classification_metrics(
        [None, ["Soil", "Fine-grained soil"]], [None, None],
    )
    assert values["hierarchical_path_exact_match"].denominator == 1
    assert values["hierarchical_path_exact_match"].value == 0
    assert values["hierarchical_prediction_coverage"].value == 0
