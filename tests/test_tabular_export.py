import json
from pathlib import Path

import openpyxl
import pyarrow.parquet as pq

from geologparser.export import tabular_rows, write_parquet_dataset, write_xlsx


ROOT = Path(__file__).resolve().parents[1]


def record():
    return json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))


def test_tabular_rows_keep_raw_normalized_and_provenance():
    source = record()
    rows = tabular_rows([source])
    assert rows["boreholes"][0]["document_id"] == source["document"]["document_id"]
    assert rows["intervals"][0]["lithology_raw"] == source["intervals"][0]["lithology_raw"]["value"]
    provenance = {row["field_path"]: row for row in rows["provenance"]}
    assert provenance["intervals[0].bottom_depth_m"]["source_text"] == source["intervals"][0]["bottom_depth_m"]["source_text"]


def test_xlsx_has_three_traceable_sheets(tmp_path):
    path = tmp_path / "boreholes.xlsx"
    write_xlsx([record()], path)
    workbook = openpyxl.load_workbook(path, read_only=True)
    assert workbook.sheetnames == ["boreholes", "intervals", "provenance"]
    assert workbook["intervals"].max_row == len(record()["intervals"]) + 1


def test_parquet_dataset_preserves_tables_and_empty_intervals(tmp_path):
    source = record()
    source["intervals"] = []
    directory = tmp_path / "parquet"
    write_parquet_dataset([source], directory)
    assert pq.read_table(directory / "boreholes.parquet").num_rows == 1
    interval_table = pq.read_table(directory / "intervals.parquet")
    assert interval_table.num_rows == 0
    assert "interval_id" in interval_table.column_names
    assert json.loads((directory / "metadata.json").read_text())["format"].endswith("v001")
