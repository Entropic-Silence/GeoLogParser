"""Neutral surface meshes and optional PyVista interoperability."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from geologparser.evaluation.error_propagation import SurfacePoint, idw_predict


@dataclass(frozen=True)
class SurfaceGrid:
    x_values: tuple[float, ...]
    y_values: tuple[float, ...]
    elevations: tuple[float, ...]
    points_xyz: tuple[tuple[float, float, float], ...]
    triangle_cells: tuple[tuple[int, int, int], ...]


def idw_surface_grid(
    points: Sequence[SurfacePoint], x_values: Sequence[float], y_values: Sequence[float],
    *, power: float = 2.0,
) -> SurfaceGrid:
    """Build a row-major regular grid and deterministic triangle topology."""
    xs = tuple(float(value) for value in x_values)
    ys = tuple(float(value) for value in y_values)
    if len(xs) < 2 or len(ys) < 2:
        raise ValueError("surface grid requires at least 2 x and 2 y coordinates")
    if any(right <= left for left, right in zip(xs, xs[1:])):
        raise ValueError("x coordinates must be strictly increasing")
    if any(upper <= lower for lower, upper in zip(ys, ys[1:])):
        raise ValueError("y coordinates must be strictly increasing")
    xyz = []
    elevations = []
    for y in ys:
        for x in xs:
            elevation = float(idw_predict(points, x, y, power))
            elevations.append(elevation)
            xyz.append((x, y, elevation))
    triangles = []
    width = len(xs)
    for row in range(len(ys) - 1):
        for column in range(width - 1):
            lower_left = row * width + column
            lower_right = lower_left + 1
            upper_left = lower_left + width
            upper_right = upper_left + 1
            triangles.extend((
                (lower_left, lower_right, upper_right),
                (lower_left, upper_right, upper_left),
            ))
    return SurfaceGrid(xs, ys, tuple(elevations), tuple(xyz), tuple(triangles))


def to_pyvista(grid: SurfaceGrid):
    """Convert a neutral grid to a triangulated ``pyvista.PolyData``."""
    try:
        import numpy as np
        import pyvista as pv
    except ImportError as exc:
        raise RuntimeError("PyVista export requires the paper3-3d optional dependencies") from exc
    points = np.asarray(grid.points_xyz, dtype=float)
    faces = np.asarray([(3, *cell) for cell in grid.triangle_cells], dtype=int).reshape(-1)
    mesh = pv.PolyData(points, faces)
    mesh.point_data["elevation_m"] = np.asarray(grid.elevations, dtype=float)
    return mesh


def write_pyvista_surface(
    grid: SurfaceGrid, mesh_path: Path, screenshot_path: Path | None = None,
) -> dict[str, Any]:
    """Write VTK PolyData and, optionally, a deterministic off-screen review PNG."""
    mesh_path = Path(mesh_path)
    if mesh_path.exists():
        raise FileExistsError(mesh_path)
    if mesh_path.suffix.lower() != ".vtp":
        raise ValueError("PyVista surface path must use .vtp")
    mesh_path.parent.mkdir(parents=True, exist_ok=True)
    mesh = to_pyvista(grid)
    mesh.save(mesh_path)
    result: dict[str, Any] = {
        "mesh_path": str(mesh_path), "point_count": mesh.n_points,
        "cell_count": mesh.n_cells, "bounds": [float(value) for value in mesh.bounds],
        "array_names": list(mesh.array_names),
    }
    if screenshot_path is not None:
        screenshot_path = Path(screenshot_path)
        if screenshot_path.exists():
            raise FileExistsError(screenshot_path)
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import pyvista as pv
            plotter = pv.Plotter(off_screen=True, window_size=(1200, 800))
            plotter.set_background("white")
            plotter.add_mesh(mesh, scalars="elevation_m", cmap="terrain", show_edges=True)
            plotter.add_axes()
            plotter.view_isometric()
            plotter.screenshot(str(screenshot_path))
            plotter.close()
        except Exception as exc:
            raise RuntimeError(f"PyVista off-screen rendering failed: {exc}") from exc
        result["screenshot_path"] = str(screenshot_path)
    return result
