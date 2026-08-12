import json
import sqlite3
from pathlib import Path

from geologparser.export import write_geojson, write_sqlite


ROOT = Path(__file__).resolve().parents[1]


def record():
    return json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))


def test_sqlite_export_preserves_intervals_and_provenance(tmp_path: Path):
    source = record()
    path = tmp_path / "boreholes.sqlite"
    write_sqlite([source], path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM boreholes").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM intervals").fetchone()[0] == len(source["intervals"])
        row = connection.execute(
            "SELECT source_text, extraction_method FROM field_provenance WHERE field_path = 'borehole.borehole_id'"
        ).fetchone()
        assert row == (source["borehole"]["borehole_id"]["source_text"], source["borehole"]["borehole_id"]["extraction_method"])


def test_sqlite_upsert_replaces_interval_projection_without_duplicates(tmp_path: Path):
    source = record()
    path = tmp_path / "boreholes.sqlite"
    write_sqlite([source], path)
    source["intervals"] = source["intervals"][:1]
    write_sqlite([source], path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM intervals").fetchone()[0] == 1


def test_geojson_skips_missing_coordinates_and_does_not_transform(tmp_path: Path):
    located = record()
    located["borehole"]["coordinate_system"]["value"] = "EPSG:27700"
    located["borehole"]["x_coordinate"]["value"] = 329168
    located["borehole"]["y_coordinate"]["value"] = 405889
    missing = record()
    missing["document"]["document_id"] = "missing"
    path = tmp_path / "boreholes.geojson"
    write_geojson([located, missing], path)
    collection = json.loads(path.read_text())
    assert len(collection["features"]) == 1
    assert collection["features"][0]["geometry"]["coordinates"] == [329168, 405889]
    assert collection["metadata"]["coordinate_systems"] == ["EPSG:27700"]
