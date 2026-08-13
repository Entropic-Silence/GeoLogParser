import hashlib
import json
from pathlib import Path

import pytest

from geologparser.datasets.mendeley import (
    acquire_frozen_mendeley_inventory,
    verify_mendeley_acquisition,
)


def _inventory(path: Path, body: bytes, *, filename: str = "data.xlsx") -> None:
    path.write_text(json.dumps([{
        "filename": filename,
        "id": "file-id",
        "content_details": {
            "download_url": "https://data.mendeley.com/public-files/datasets/test123/files/file-id/file_downloaded",
            "sha256_hash": hashlib.sha256(body).hexdigest(),
            "size": len(body),
            "content_type": "application/test",
        },
    }]))


def test_acquire_and_verify_frozen_inventory(tmp_path: Path):
    body = b"workbook"
    inventory = tmp_path / "inventory.json"
    _inventory(inventory, body)
    destination = tmp_path / "dataset"
    result = acquire_frozen_mendeley_inventory(
        inventory,
        destination,
        dataset_id="test123",
        dataset_doi="10.17632/test123.1",
        dataset_version=1,
        license_id="CC-BY-4.0",
        access_date="2026-08-13",
        downloader=lambda url, timeout: body,
    )
    assert result["file_count"] == 1
    assert (destination / "raw/data.xlsx").read_bytes() == body
    assert verify_mendeley_acquisition(destination)["verified"] is True


def test_acquisition_rejects_hash_mismatch_without_partial_output(tmp_path: Path):
    inventory = tmp_path / "inventory.json"
    _inventory(inventory, b"expected")
    destination = tmp_path / "dataset"
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        acquire_frozen_mendeley_inventory(
            inventory,
            destination,
            dataset_id="test123",
            dataset_doi="10.17632/test123.1",
            dataset_version=1,
            license_id="CC-BY-4.0",
            downloader=lambda url, timeout: b"tampered",
        )
    assert not destination.exists()


def test_acquisition_rejects_unsafe_filename(tmp_path: Path):
    inventory = tmp_path / "inventory.json"
    _inventory(inventory, b"x", filename="../escape.xlsx")
    with pytest.raises(ValueError, match="unsafe Mendeley filename"):
        acquire_frozen_mendeley_inventory(
            inventory,
            tmp_path / "dataset",
            dataset_id="test123",
            dataset_doi="10.17632/test123.1",
            dataset_version=1,
            license_id="CC-BY-4.0",
            downloader=lambda url, timeout: b"x",
        )


def test_acquisition_refuses_overwrite(tmp_path: Path):
    inventory = tmp_path / "inventory.json"
    _inventory(inventory, b"x")
    destination = tmp_path / "dataset"
    destination.mkdir()
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        acquire_frozen_mendeley_inventory(
            inventory,
            destination,
            dataset_id="test123",
            dataset_doi="10.17632/test123.1",
            dataset_version=1,
            license_id="CC-BY-4.0",
        )
