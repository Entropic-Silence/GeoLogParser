import json
from pathlib import Path

import pytest

from geologparser.evaluation import (
    SurfacePoint, boundary_surface_points, idw_predict, perturb_interval_boundaries,
    surface_error_metrics,
)


ROOT = Path(__file__).resolve().parents[1]


def records():
    base = json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))
    result = []
    for index, (x, y, collar) in enumerate(((0, 0, 100), (10, 0, 102), (0, 10, 98))):
        record = json.loads(json.dumps(base))
        record["document"]["document_id"] = f"D{index}"
        record["borehole"]["borehole_id"]["value"] = f"ZK{index}"
        record["borehole"]["x_coordinate"]["value"] = x
        record["borehole"]["y_coordinate"]["value"] = y
        record["borehole"]["collar_elevation_m"]["value"] = collar
        result.append(record)
    return result


def test_idw_exact_at_observation_and_weighted_between_points():
    points = [SurfacePoint(0, 0, 10, "A"), SurfacePoint(10, 0, 20, "B")]
    assert idw_predict(points, 0, 0) == 10
    assert idw_predict(points, 5, 0) == pytest.approx(15)


def test_boundary_surface_points_convert_depth_to_elevation():
    points = boundary_surface_points(records(), 0, "bottom_depth_m")
    assert [(point.x, point.y, point.elevation) for point in points] == [
        (0.0, 0.0, 98.8), (10.0, 0.0, 100.8), (0.0, 10.0, 96.8),
    ]


def test_boundary_perturbation_is_seeded_and_preserves_continuity():
    source = records()
    first = perturb_interval_boundaries(source, 0.1, seed=7)
    second = perturb_interval_boundaries(source, 0.1, seed=7)
    assert first == second
    for record in first:
        assert record["intervals"][0]["bottom_depth_m"]["value"] == record["intervals"][1]["top_depth_m"]["value"]
        for interval in record["intervals"]:
            assert interval["thickness_m"]["value"] == pytest.approx(
                interval["bottom_depth_m"]["value"] - interval["top_depth_m"]["value"]
            )
    assert source != first


def test_surface_error_metrics_and_empty_case():
    metrics = surface_error_metrics([1, 2], [1.1, 1.8])
    assert metrics["mae_m"] == pytest.approx(0.15)
    assert metrics["rmse_m"] == pytest.approx((0.05 / 2) ** 0.5)
    assert surface_error_metrics([], [])["mae_m"] is None
