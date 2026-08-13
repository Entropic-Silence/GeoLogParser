import json
import sqlite3
from pathlib import Path

from geologparser.export import write_geojson, write_geopackage, write_sqlite


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


def test_sqlite_export_preserves_human_display_bbox_provenance_and_migrates(tmp_path: Path):
    path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE field_provenance (
                document_id TEXT NOT NULL,
                field_path TEXT NOT NULL,
                value_json TEXT,
                source_page INTEGER,
                source_bbox_json TEXT,
                display_bbox_json TEXT,
                source_text TEXT,
                extraction_method TEXT NOT NULL,
                confidence REAL,
                validation_status TEXT NOT NULL,
                warning_codes_json TEXT NOT NULL,
                raw_unit TEXT,
                PRIMARY KEY (document_id, field_path)
            )
        """)
        assert "display_bbox_source" not in {
            row[1] for row in connection.execute("PRAGMA table_info(field_provenance)")
        }
    source = record()
    envelope = source["borehole"]["final_depth_m"]
    envelope.update({
        "display_bbox": [1, 2, 30, 40], "display_bbox_source": "human_drawn",
        "display_bbox_annotator_id": "reviewer-1",
    })
    write_sqlite([source], path)
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT display_bbox_source, display_bbox_annotator_id "
            "FROM field_provenance WHERE field_path='borehole.final_depth_m'"
        ).fetchone()
        assert row == ("human_drawn", "reviewer-1")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(field_provenance)")}
        assert {"display_bbox_source", "display_bbox_annotator_id"} <= columns
        # A second initialization must preserve migrated columns and inserts.
    write_sqlite([source], path)
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT display_bbox_annotator_id FROM field_provenance "
            "WHERE field_path='borehole.final_depth_m'"
        ).fetchone()[0] == "reviewer-1"


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


def test_geopackage_writes_point_layer_with_coordinate_status(tmp_path: Path):
    pytest = __import__("pytest")
    pytest.importorskip("pyogrio")
    import pyogrio
    located = record()
    located["borehole"]["x_coordinate"].update({"value": 12.1, "validation_status": "needs_review", "warning_codes": ["SOURCE_COORDINATE_UNVERIFIED"]})
    located["borehole"]["y_coordinate"].update({"value": 45.2, "validation_status": "needs_review", "warning_codes": ["SOURCE_COORDINATE_UNVERIFIED"]})
    located["borehole"]["coordinate_system"]["value"] = "EPSG:4326"
    path = tmp_path / "boreholes.gpkg"
    write_geopackage([located], path)
    metadata, table = pyogrio.read_arrow(path, layer="boreholes")
    assert table.num_rows == 1
    assert table["coordinate_validation_status"][0].as_py() == "needs_review"
    assert metadata["crs"] == "EPSG:4326"
    with pytest.raises(FileExistsError):
        write_geopackage([located], path)
