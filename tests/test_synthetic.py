import json
from pathlib import Path

from geologparser.schema import validate_record
from geologparser.synthetic import generate_synthetic_dataset, make_synthetic_record
import random


def test_synthetic_record_is_schema_valid_and_known_gt():
    record = make_synthetic_record(1, random.Random(4), template_id="SYN-T01A")
    validate_record(record)
    assert record["document"]["metadata"]["source_id"] == "SYNTHETIC_V001"
    assert all(item["top_depth_m"]["validation_status"] == "synthetic_verified" for item in record["intervals"])


def test_synthetic_dataset_is_immutable_and_traceable(tmp_path: Path):
    output = tmp_path / "synthetic"
    summary = generate_synthetic_dataset(output, count=4, seed=7, templates=2)
    assert summary["ground_truth_tier"] == "SYNTHETIC"
    assert summary["human_ground_truth_count"] == 0
    rows = [json.loads(line) for line in (output / "manifest.jsonl").read_text().splitlines()]
    assert len(rows) == 4
    assert {row["ground_truth_tier"] for row in rows} == {"SYNTHETIC"}
    assert all(Path(row["image_path"]).is_file() for row in rows)
    assert all(Path(row["label_path"]).is_file() for row in rows)
    try:
        generate_synthetic_dataset(output, count=1)
    except FileExistsError:
        pass
    else:
        raise AssertionError("existing synthetic output must not be overwritten")
