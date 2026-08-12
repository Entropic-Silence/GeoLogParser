"""XLSX and Parquet projections with provenance retained in separate tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def _value(envelope: Any) -> Any:
    return envelope.get("value") if isinstance(envelope, Mapping) else envelope


BOREHOLE_COLUMNS = (
    "document_id", "source_file", "source_sha256", "borehole_id", "project_name",
    "x_coordinate", "y_coordinate", "coordinate_system", "collar_elevation_m",
    "final_depth_m", "groundwater_depth_m", "groundwater_elevation_m", "drilling_date",
)
INTERVAL_COLUMNS = (
    "document_id", "interval_id", "sequence_index", "top_depth_m", "bottom_depth_m",
    "thickness_m", "stratum_code_raw", "stratum_code_normalized", "lithology_raw",
    "lithology_normalized", "description_raw", "description_normalized", "weathering",
    "color", "consistency_or_density", "moisture", "structure", "inclusions",
)
PROVENANCE_COLUMNS = (
    "document_id", "field_path", "value_json", "source_page", "source_bbox_json",
    "display_bbox_json", "source_text", "extraction_method", "confidence",
    "validation_status", "warning_codes_json", "raw_unit",
)


def tabular_rows(records: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    boreholes: list[dict[str, Any]] = []
    intervals: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for record in records:
        document = record["document"]
        borehole = record["borehole"]
        document_id = document["document_id"]
        boreholes.append({
            "document_id": document_id,
            "source_file": document["source_file"],
            "source_sha256": document.get("source_sha256"),
            **{name: _value(borehole[name]) for name in BOREHOLE_COLUMNS[3:]},
        })
        field_envelopes = [(f"borehole.{name}", envelope) for name, envelope in borehole.items()]
        for index, interval in enumerate(record.get("intervals", ())):
            intervals.append({
                "document_id": document_id,
                "interval_id": interval["interval_id"],
                "sequence_index": index,
                **{name: _value(interval[name]) for name in INTERVAL_COLUMNS[3:]},
            })
            field_envelopes.extend(
                (f"intervals[{index}].{name}", envelope)
                for name, envelope in interval.items() if name != "interval_id"
            )
        for field_path, envelope in field_envelopes:
            provenance.append({
                "document_id": document_id,
                "field_path": field_path,
                "value_json": json.dumps(envelope.get("value"), ensure_ascii=False),
                "source_page": envelope.get("source_page"),
                "source_bbox_json": json.dumps(envelope.get("source_bbox")),
                "display_bbox_json": json.dumps(envelope.get("display_bbox")),
                "source_text": envelope.get("source_text"),
                "extraction_method": envelope.get("extraction_method", "unknown"),
                "confidence": envelope.get("confidence"),
                "validation_status": envelope.get("validation_status", "not_validated"),
                "warning_codes_json": json.dumps(envelope.get("warning_codes", []), ensure_ascii=False),
                "raw_unit": envelope.get("raw_unit"),
            })
    return {"boreholes": boreholes, "intervals": intervals, "provenance": provenance}


def write_xlsx(records: Iterable[Mapping[str, Any]], path: Path) -> None:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError as exc:
        raise RuntimeError("XLSX export requires openpyxl; install geologparser[export]") from exc
    rows = tabular_rows(records)
    columns = {"boreholes": BOREHOLE_COLUMNS, "intervals": INTERVAL_COLUMNS, "provenance": PROVENANCE_COLUMNS}
    workbook = Workbook()
    workbook.remove(workbook.active)
    for sheet_name in ("boreholes", "intervals", "provenance"):
        sheet = workbook.create_sheet(sheet_name)
        sheet.append(list(columns[sheet_name]))
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for row in rows[sheet_name]:
            sheet.append([row.get(column) for column in columns[sheet_name]])
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def write_parquet_dataset(records: Iterable[Mapping[str, Any]], directory: Path) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Parquet export requires pyarrow; install geologparser[export]") from exc
    rows = tabular_rows(records)
    columns = {"boreholes": BOREHOLE_COLUMNS, "intervals": INTERVAL_COLUMNS, "provenance": PROVENANCE_COLUMNS}
    directory.mkdir(parents=True, exist_ok=True)
    for table_name, table_rows in rows.items():
        # Explicit all-string fallback schema for an empty table prevents an
        # empty struct with unusable/no columns.
        if table_rows:
            table = pa.Table.from_pylist(table_rows)
        else:
            table = pa.table({name: pa.array([], type=pa.string()) for name in columns[table_name]})
        pq.write_table(table, directory / f"{table_name}.parquet", compression="zstd")
    metadata = {
        "format": "GeoLogParser tabular projection v001",
        "tables": {name: list(value) for name, value in columns.items()},
        "note": "canonical lossless record remains JSON; provenance values are JSON strings",
    }
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
