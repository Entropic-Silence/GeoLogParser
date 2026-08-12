from pathlib import Path

import pytest

from geologparser.evaluation import SurfacePoint
from geologparser.visualization import idw_surface_grid, to_pyvista, write_pyvista_surface


def points():
    return [
        SurfacePoint(0, 0, 10, "A"), SurfacePoint(10, 0, 20, "B"),
        SurfacePoint(0, 10, 30, "C"), SurfacePoint(10, 10, 40, "D"),
    ]


def test_neutral_surface_grid_has_deterministic_topology():
    grid = idw_surface_grid(points(), [0, 5, 10], [0, 10])
    assert len(grid.points_xyz) == 6
    assert grid.points_xyz[0] == (0.0, 0.0, 10.0)
    assert grid.points_xyz[-1] == (10.0, 10.0, 40.0)
    assert grid.triangle_cells == ((0, 1, 4), (0, 4, 3), (1, 2, 5), (1, 5, 4))


def test_neutral_grid_rejects_degenerate_coordinates():
    with pytest.raises(ValueError, match="strictly increasing"):
        idw_surface_grid(points(), [0, 0], [0, 10])


def test_pyvista_mesh_export_round_trip(tmp_path: Path):
    pv = pytest.importorskip("pyvista")
    grid = idw_surface_grid(points(), [0, 5, 10], [0, 5, 10])
    mesh = to_pyvista(grid)
    assert mesh.n_points == 9
    assert mesh.n_cells == 8
    assert "elevation_m" in mesh.array_names
    path = tmp_path / "surface.vtp"
    result = write_pyvista_surface(grid, path)
    loaded = pv.read(path)
    assert loaded.n_points == result["point_count"] == 9
    assert loaded.n_cells == result["cell_count"] == 8
    assert loaded["elevation_m"].tolist() == pytest.approx(list(grid.elevations))
