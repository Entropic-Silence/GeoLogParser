import pytest

from geologparser.experiment import create_run_directory


def metadata():
    return {
        "experiment_id": "P0_SMOKE_001", "git_commit": "TBD", "date": "2026-08-12",
        "dataset_version": "synthetic_fixture_v001", "split_version": "not_applicable",
        "model": "tesseract", "model_revision": "4.1.1", "prompt_version": "not_applicable",
        "seed": None, "hardware": {"device": "cpu"}, "software": {}, "config": {},
    }


def test_run_directory_is_created_once(tmp_path):
    destination = create_run_directory(tmp_path, metadata())
    assert (destination / "run.json").exists()
    assert (destination / "predictions.jsonl").exists()
    with pytest.raises(FileExistsError):
        create_run_directory(tmp_path, metadata())


def test_missing_metadata_is_rejected(tmp_path):
    values = metadata()
    del values["model_revision"]
    with pytest.raises(ValueError):
        create_run_directory(tmp_path, values)

