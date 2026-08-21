import hashlib
import json
from pathlib import Path

from openpyxl import Workbook
import pytest

from geologparser.datasets.structured_audit import (
    build_structured_dataset_audit,
    verify_structured_dataset_audit,
)


def _write_acquisition(root: Path, *, dataset_id: str) -> None:
    files = []
    for path in sorted((root / "raw").iterdir()):
        if not path.is_file():
            continue
        body = path.read_bytes()
        files.append({
            "filename": path.name,
            "size_bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "content_type": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                if path.suffix == ".xlsx"
                else "text/plain"
            ),
        })
    metadata = root / "metadata"
    metadata.mkdir()
    (metadata / "acquisition.json").write_text(json.dumps({
        "dataset_id": dataset_id,
        "dataset_doi": f"10.17632/{dataset_id}.1",
        "dataset_version": 1,
        "license_id": "CC-BY-4.0",
        "files": files,
    }))


def _binhai_dataset(root: Path) -> None:
    raw = root / "raw"
    raw.mkdir(parents=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Name", "X", "Y", "Depth", "qt", "fs", "u2"])
    sheet.append(["A1", "*", "*", 0.02, 1.0, 0.1, 0.01])
    sheet.append(["A1", "*", "*", 0.04, 1.1, 0.2, 0.02])
    workbook.save(raw / "A1_update.xlsx")
    _write_acquisition(root, dataset_id="binhai")


def _coal_dataset(root: Path) -> None:
    raw = root / "raw"
    raw.mkdir(parents=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.append([
        "Gas Drainage Borehole Number", "Y", "X", "Z", "Drilling Registration",
        None, None, "Drilling Measurement", None, "Drilling, coal seam parameters",
        None, None, None,
    ])
    sheet.append([
        None, None, None, None, "Final hole depth(m)", "3 Coal Roof Depth(m)",
        "3 Coal seam thickness(m)", "Borehole Zenith Angle (°)",
        "Drilling azimuth (°)", "borehole inclina-tion (°)",
        "borehole azimuth (°)", "coal seam dip angle (°)",
        "coal seam dip direction (°)",
    ])
    sheet.append(["BH-1", 10, 20, 30, 50, 45, 3, 120, 120, 30, 120, 4, 3.5])
    workbook.save(raw / "minimum_reproducible_borehole_dataset_602.xlsx")
    (raw / "run_all.py").write_text(
        'root / "scripts" / "01_preprocess_qc.py"\n', encoding="utf-8"
    )
    (raw / "README.md").write_text("Contact: author@example.org\n", encoding="utf-8")
    _write_acquisition(root, dataset_id="coal")


def test_binhai_audit_classifies_redacted_cptu_data(tmp_path: Path):
    dataset = tmp_path / "binhai"
    _binhai_dataset(dataset)
    audit = tmp_path / "audit"
    result = build_structured_dataset_audit(
        dataset,
        audit,
        profile="binhai_cptu_v001",
        audited_at_utc="2026-08-13T00:00:00Z",
    )
    assert result["verified"] is True
    payload = json.loads((audit / "structured_content_audit.json").read_text(encoding="utf-8"))
    content = payload["content_audit"]
    assert content["workbook_count"] == 1
    assert content["total_measurement_rows"] == 2
    assert content["coordinates_redacted"] is True
    assert content["non_increasing_depth_steps"] == 0
    assert content["eligibility"]["paper3_spatial_error_propagation"] is False


def test_coal_audit_records_source_consistency_and_missing_code(tmp_path: Path):
    dataset = tmp_path / "coal"
    _coal_dataset(dataset)
    audit = tmp_path / "audit"
    build_structured_dataset_audit(
        dataset,
        audit,
        profile="coal_boreholes_602_v001",
        audited_at_utc="2026-08-13T00:00:00Z",
    )
    payload = json.loads((audit / "structured_content_audit.json").read_text(encoding="utf-8"))
    content = payload["content_audit"]
    assert content["record_count"] == 1
    assert content["workbook"]["headers_match_profile"] is True
    assert content["source_field_observations"][
        "roof_depth_plus_seam_thickness_greater_than_final_depth_count"
    ] == 0
    assert content["source_field_observations"][
        "maximum_abs_zenith_minus_inclination_minus_90_degrees"
    ] == 0
    assert content["released_code_audit"]["entrypoint_runnable_as_released"] is False
    assert content["released_code_audit"]["missing_entrypoint_script_references"] == [
        "scripts/01_preprocess_qc.py"
    ]
    assert payload["automated_privacy_screen"]["text_findings"] == [{
        "category": "email_address", "file": "README.md", "match_count": 1,
    }]


def test_structured_audit_is_immutable_and_detects_artifact_tampering(tmp_path: Path):
    dataset = tmp_path / "binhai"
    _binhai_dataset(dataset)
    audit = tmp_path / "audit"
    build_structured_dataset_audit(dataset, audit, profile="binhai_cptu_v001")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        build_structured_dataset_audit(dataset, audit, profile="binhai_cptu_v001")
    (audit / "structured_content_audit.json").write_text("{}")
    with pytest.raises(ValueError, match="artifact mismatch"):
        verify_structured_dataset_audit(dataset, audit)


def test_structured_audit_rejects_source_mutation(tmp_path: Path):
    dataset = tmp_path / "binhai"
    _binhai_dataset(dataset)
    audit = tmp_path / "audit"
    build_structured_dataset_audit(dataset, audit, profile="binhai_cptu_v001")
    (dataset / "raw/A1_update.xlsx").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="does not match evidence"):
        verify_structured_dataset_audit(dataset, audit)
