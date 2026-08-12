"""Traceable SQLite and GeoJSON export for validated borehole records."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping


def _value(envelope: Any) -> Any:
    return envelope.get("value") if isinstance(envelope, Mapping) else envelope


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS boreholes (
        document_id TEXT PRIMARY KEY,
        source_file TEXT NOT NULL,
        source_sha256 TEXT,
        borehole_id TEXT,
        project_name TEXT,
        x_coordinate REAL,
        y_coordinate REAL,
        coordinate_system TEXT,
        collar_elevation_m REAL,
        final_depth_m REAL,
        groundwater_depth_m REAL,
        drilling_date TEXT,
        schema_version TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS intervals (
        document_id TEXT NOT NULL,
        interval_id TEXT NOT NULL,
        sequence_index INTEGER NOT NULL,
        top_depth_m REAL,
        bottom_depth_m REAL,
        thickness_m REAL,
        stratum_code_raw TEXT,
        stratum_code_normalized TEXT,
        lithology_raw TEXT,
        lithology_normalized TEXT,
        description_raw TEXT,
        description_normalized TEXT,
        PRIMARY KEY (document_id, interval_id),
        FOREIGN KEY (document_id) REFERENCES boreholes(document_id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS field_provenance (
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
        PRIMARY KEY (document_id, field_path),
        FOREIGN KEY (document_id) REFERENCES boreholes(document_id) ON DELETE CASCADE
    );
    """)


def _provenance_rows(record: Mapping[str, Any]):
    document_id = record["document"]["document_id"]
    for name, envelope in record["borehole"].items():
        yield document_id, f"borehole.{name}", envelope
    for index, interval in enumerate(record.get("intervals", ())):
        for name, envelope in interval.items():
            if name != "interval_id":
                yield document_id, f"intervals[{index}].{name}", envelope


def upsert_record(connection: sqlite3.Connection, record: Mapping[str, Any]) -> None:
    document = record["document"]
    borehole = record["borehole"]
    document_id = document["document_id"]
    connection.execute("""
        INSERT INTO boreholes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(document_id) DO UPDATE SET
          source_file=excluded.source_file, source_sha256=excluded.source_sha256,
          borehole_id=excluded.borehole_id, project_name=excluded.project_name,
          x_coordinate=excluded.x_coordinate, y_coordinate=excluded.y_coordinate,
          coordinate_system=excluded.coordinate_system,
          collar_elevation_m=excluded.collar_elevation_m,
          final_depth_m=excluded.final_depth_m,
          groundwater_depth_m=excluded.groundwater_depth_m,
          drilling_date=excluded.drilling_date, schema_version=excluded.schema_version
    """, (
        document_id, document["source_file"], document.get("source_sha256"),
        _value(borehole["borehole_id"]), _value(borehole["project_name"]),
        _value(borehole["x_coordinate"]), _value(borehole["y_coordinate"]),
        _value(borehole["coordinate_system"]), _value(borehole["collar_elevation_m"]),
        _value(borehole["final_depth_m"]), _value(borehole["groundwater_depth_m"]),
        _value(borehole["drilling_date"]), record["schema_version"],
    ))
    connection.execute("DELETE FROM intervals WHERE document_id = ?", (document_id,))
    for index, interval in enumerate(record.get("intervals", ())):
        connection.execute("""
            INSERT INTO intervals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id, interval["interval_id"], index,
            _value(interval["top_depth_m"]), _value(interval["bottom_depth_m"]),
            _value(interval["thickness_m"]), _value(interval["stratum_code_raw"]),
            _value(interval["stratum_code_normalized"]), _value(interval["lithology_raw"]),
            _value(interval["lithology_normalized"]), _value(interval["description_raw"]),
            _value(interval["description_normalized"]),
        ))
    connection.execute("DELETE FROM field_provenance WHERE document_id = ?", (document_id,))
    for row_document_id, field_path, envelope in _provenance_rows(record):
        connection.execute("""
            INSERT INTO field_provenance VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row_document_id, field_path, json.dumps(envelope.get("value"), ensure_ascii=False),
            envelope.get("source_page"), json.dumps(envelope.get("source_bbox")),
            json.dumps(envelope.get("display_bbox")), envelope.get("source_text"),
            envelope.get("extraction_method", "unknown"), envelope.get("confidence"),
            envelope.get("validation_status", "not_validated"),
            json.dumps(envelope.get("warning_codes", []), ensure_ascii=False),
            envelope.get("raw_unit"),
        ))


def write_sqlite(records: Iterable[Mapping[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        initialize_database(connection)
        with connection:
            for record in records:
                upsert_record(connection, record)


def write_geojson(records: Iterable[Mapping[str, Any]], path: Path) -> None:
    features = []
    coordinate_systems = set()
    for record in records:
        borehole = record["borehole"]
        x, y = _value(borehole["x_coordinate"]), _value(borehole["y_coordinate"])
        if x is None or y is None:
            continue
        crs = _value(borehole["coordinate_system"])
        if crs is not None:
            coordinate_systems.add(crs)
        features.append({
            "type": "Feature",
            "id": record["document"]["document_id"],
            "geometry": {"type": "Point", "coordinates": [x, y]},
            "properties": {
                "borehole_id": _value(borehole["borehole_id"]),
                "coordinate_system": crs,
                "collar_elevation_m": _value(borehole["collar_elevation_m"]),
                "final_depth_m": _value(borehole["final_depth_m"]),
                "source_sha256": record["document"].get("source_sha256"),
            },
        })
    collection = {
        "type": "FeatureCollection", "features": features,
        "metadata": {
            "coordinate_systems": sorted(coordinate_systems),
            "warning": "coordinates are not transformed; consumers must honor each feature coordinate_system",
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(collection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_geopackage(records: Iterable[Mapping[str, Any]], path: Path) -> None:
    """Write a QGIS-compatible point layer with coordinate uncertainty fields."""
    try:
        import pyarrow as pa
        import pyogrio
        from pyproj import CRS
        from shapely import to_wkb
        from shapely.geometry import Point
    except ImportError as exc:
        raise RuntimeError("GeoPackage export requires pyarrow, pyogrio, pyproj, and shapely") from exc
    if path.exists():
        raise FileExistsError(f"GeoPackage already exists: {path}")
    rows = []
    systems = set()
    for record in records:
        borehole = record["borehole"]
        x, y = _value(borehole["x_coordinate"]), _value(borehole["y_coordinate"])
        if x is None or y is None:
            continue
        system = _value(borehole["coordinate_system"])
        systems.add(system)
        rows.append({
            "document_id": record["document"]["document_id"],
            "borehole_id": _value(borehole["borehole_id"]),
            "x_coordinate": float(x), "y_coordinate": float(y),
            "coordinate_system": system,
            "coordinate_validation_status": borehole["x_coordinate"].get("validation_status"),
            "coordinate_warning_codes": json.dumps(
                sorted(set(borehole["x_coordinate"].get("warning_codes", []))
                       | set(borehole["y_coordinate"].get("warning_codes", []))),
                ensure_ascii=False,
            ),
            "collar_elevation_m": _value(borehole["collar_elevation_m"]),
            "final_depth_m": _value(borehole["final_depth_m"]),
            "source_file": record["document"]["source_file"],
            # Avoid Arrow null-only columns, which OGR cannot materialize as a
            # field when all records lack a source hash.
            "source_sha256": record["document"].get("source_sha256") or "",
            "geometry": to_wkb(Point(float(x), float(y)), hex=False),
        })
    if not rows:
        raise ValueError("GeoPackage export requires at least one located borehole")
    if len(systems) != 1 or None in systems:
        raise ValueError("GeoPackage export requires exactly one known coordinate system")
    system = next(iter(systems))
    import re
    match = re.fullmatch(r"EPSG:(\d+)", str(system), flags=re.IGNORECASE)
    if not match:
        raise ValueError("coordinate_system must use an explicit EPSG:<code> identifier")
    # Explicit types keep all-null optional numeric/text columns writable by
    # OGR (Arrow's inferred ``null`` type has no corresponding GPKG field).
    table = pa.table({
        "document_id": pa.array([row["document_id"] for row in rows], type=pa.string()),
        "borehole_id": pa.array([row["borehole_id"] for row in rows], type=pa.string()),
        "x_coordinate": pa.array([row["x_coordinate"] for row in rows], type=pa.float64()),
        "y_coordinate": pa.array([row["y_coordinate"] for row in rows], type=pa.float64()),
        "coordinate_system": pa.array([row["coordinate_system"] for row in rows], type=pa.string()),
        "coordinate_validation_status": pa.array(
            [row["coordinate_validation_status"] for row in rows], type=pa.string(),
        ),
        "coordinate_warning_codes": pa.array(
            [row["coordinate_warning_codes"] for row in rows], type=pa.string(),
        ),
        "collar_elevation_m": pa.array([row["collar_elevation_m"] for row in rows], type=pa.float64()),
        "final_depth_m": pa.array([row["final_depth_m"] for row in rows], type=pa.float64()),
        "source_file": pa.array([row["source_file"] for row in rows], type=pa.string()),
        "source_sha256": pa.array([row["source_sha256"] for row in rows], type=pa.string()),
        "geometry": pa.array([row["geometry"] for row in rows], type=pa.binary()),
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    pyogrio.write_arrow(
        table, path, layer="boreholes", driver="GPKG", geometry_name="geometry",
        geometry_type="Point", crs=CRS.from_epsg(int(match.group(1))).to_wkt(),
        dataset_metadata={
            "GEologparser_scope": "traceable point export; coordinate status is not Ground Truth",
        },
        layer_metadata={
            "coordinate_warning": "honor coordinate_validation_status and coordinate_warning_codes",
        },
    )
