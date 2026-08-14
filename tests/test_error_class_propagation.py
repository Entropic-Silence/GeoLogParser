from geologparser.evaluation.error_class_propagation import (
    OrderedBoundaryRecord,
    evaluate_error_propagation,
    inject_error_class,
    prepare_reference_surfaces,
)


def records():
    return [
        OrderedBoundaryRecord("A", 0, 0, 100, (10.0, 20.0, 30.0)),
        OrderedBoundaryRecord("B", 10, 0, 101, (11.0, 21.0, 31.0)),
        OrderedBoundaryRecord("C", 0, 10, 102, (12.0, 22.0, 32.0)),
        OrderedBoundaryRecord("D", 10, 10, 103, (13.0, 23.0, 33.0)),
    ]


def test_clean_reference_has_zero_error_and_complete_support():
    reference = records()
    prepared = prepare_reference_surfaces(reference, 5)
    metrics = evaluate_error_propagation(reference, reference, prepared)
    assert metrics["spatial_support_coverage"] == 1
    assert metrics["boundary_mae_m"] == 0
    assert metrics["surface_error"]["mae_m"] == 0
    assert metrics["topology"]["mismatched_document_count"] == 0


def test_boundary_and_coordinate_errors_are_separated():
    reference = records()
    prepared = prepare_reference_surfaces(reference, 5)
    shifted, audit = inject_error_class(
        reference, "boundary_shift", 1.0, 3, affected_fraction=0.25,
    )
    metrics = evaluate_error_propagation(reference, shifted, prepared)
    assert audit
    assert metrics["boundary_mae_m"] > 0
    assert metrics["spatial_support_coverage"] == 1
    assert metrics["topology"]["mismatched_document_count"] == 0

    moved, audit = inject_error_class(
        reference, "coordinate_shift", 5.0, 3, affected_fraction=0.25,
    )
    metrics = evaluate_error_propagation(reference, moved, prepared)
    assert audit
    assert metrics["boundary_mae_m"] == 0
    assert metrics["surface_error"]["mae_m"] > 0
    assert metrics["topology"]["mismatched_document_count"] == 0


def test_missing_boundary_reduces_support_without_position_shift():
    reference = records()
    changed, audit = inject_error_class(reference, "missing_boundary", 0.25, 9)
    metrics = evaluate_error_propagation(
        reference, changed, prepare_reference_surfaces(reference, 5),
    )
    assert len(audit) == 1
    assert metrics["spatial_support_coverage"] < 1
    assert metrics["topology"]["missing_slot_count"] == 1
    assert metrics["topology"]["mismatched_document_count"] == 1


def test_sequence_error_classes_change_boundary_topology():
    reference = records()
    prepared = prepare_reference_surfaces(reference, 5)
    for error_type in ("merged_layer", "split_layer", "duplicate_boundary"):
        changed, audit = inject_error_class(reference, error_type, 0.25, 11)
        metrics = evaluate_error_propagation(reference, changed, prepared)
        assert len(audit) == 1
        assert metrics["topology"]["mismatched_document_count"] == 1
        assert metrics["topology"]["boundary_count_absolute_difference"] == 1


def test_injection_is_seed_reproducible():
    first, first_audit = inject_error_class(records(), "split_layer", 0.5, 42)
    second, second_audit = inject_error_class(records(), "split_layer", 0.5, 42)
    assert first == second
    assert first_audit == second_audit
