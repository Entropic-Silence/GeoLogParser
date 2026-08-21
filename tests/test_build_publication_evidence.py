from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build_publication_evidence import is_external_data_origin, replace_tree


def test_external_data_origin_is_host_independent() -> None:
    assert is_external_data_origin("/data/GeoLogParser/results/run/metrics.json")
    assert is_external_data_origin(r"\data\GeoLogParser\results\run\metrics.json")
    assert not is_external_data_origin("publication_evidence/result_core/metrics.json")


def test_replace_tree_swaps_complete_staging_directory(tmp_path: Path) -> None:
    destination = tmp_path / "external"
    staging = tmp_path / ".external.staging"
    destination.mkdir()
    staging.mkdir()
    (destination / "old.json").write_text("old", encoding="utf-8")
    (staging / "new.json").write_text("new", encoding="utf-8")

    replace_tree(staging, destination)

    assert not staging.exists()
    assert not (tmp_path / ".external.previous").exists()
    assert not (destination / "old.json").exists()
    assert (destination / "new.json").read_text(encoding="utf-8") == "new"


def test_replace_tree_preserves_destination_when_staging_is_missing(tmp_path: Path) -> None:
    destination = tmp_path / "external"
    destination.mkdir()
    existing = destination / "claim_snapshot.json"
    existing.write_text("retained", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="staging directory is missing"):
        replace_tree(tmp_path / ".external.staging", destination)

    assert existing.read_text(encoding="utf-8") == "retained"
