from geologparser.evaluation import SurfacePoint
import importlib.util
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "run_coal602_consensus_downstream",
    Path(__file__).resolve().parents[1] / "scripts/run_coal602_consensus_downstream.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_consensus_rejects_disagreement_and_keeps_matching_values():
    left = (SurfacePoint(0, 0, 1.0, "a"), SurfacePoint(1, 0, 2.0, "b"))
    right = (SurfacePoint(0, 0, 1.0, "a"), SurfacePoint(1, 0, 3.0, "b"))
    accepted, rejected = MODULE.consensus_points(left, right)
    assert [point.elevation for point in accepted] == [1.0]
    assert rejected == (1,)


def test_corruption_is_reproducible():
    points = tuple(SurfacePoint(float(i), 0, 10.0, str(i)) for i in range(20))
    first = MODULE.corrupt_channel(points, 0.5, 0.2, 7)
    second = MODULE.corrupt_channel(points, 0.5, 0.2, 7)
    assert first == second


def test_mean_fusion_preserves_support_and_averages_values():
    left = (SurfacePoint(0, 0, 1.0, "a"), SurfacePoint(1, 0, 3.0, "b"))
    right = (SurfacePoint(0, 0, 3.0, "a"), SurfacePoint(1, 0, 5.0, "b"))
    fused = MODULE.mean_fusion_points(left, right)
    assert [(point.x, point.y, point.elevation) for point in fused] == [
        (0, 0, 2.0), (1, 0, 4.0),
    ]


def test_paired_summary_reports_direction_and_exact_sign_test():
    raw = [{"mae_m": value} for value in (3.0, 4.0, 5.0, 6.0)]
    fused = [{"mae_m": value} for value in (2.0, 3.0, 4.0, 7.0)]
    summary = MODULE.paired_improvement_summary(raw, fused)
    assert summary["fusion_better_count"] == 3
    assert summary["fusion_worse_count"] == 1
    assert summary["two_sided_exact_sign_test_p"] == 0.625
