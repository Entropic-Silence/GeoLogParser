from pathlib import Path

from geologparser.result_index import file_sha256, verify_index


def test_result_index_verifies_complete_run(tmp_path: Path):
    result = tmp_path / "results" / "2026-08-12" / "TEST_001"
    result.mkdir(parents=True)
    files = {
        "run.json": "{}\n", "metrics.json": "{}\n", "predictions.jsonl": "",
        "errors.jsonl": "", "run.log": "status=completed\n",
    }
    for name, content in files.items():
        (result / name).write_text(content, encoding="utf-8")
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("{}\n", encoding="utf-8")
    entry = {
        "experiment_id": "TEST_001",
        "result_path": "results/2026-08-12/TEST_001",
        "dataset_manifest_path": str(manifest),
        "dataset_manifest_sha256": file_sha256(manifest),
        "run_sha256": file_sha256(result / "run.json"),
        "metrics_sha256": file_sha256(result / "metrics.json"),
        "predictions_sha256": file_sha256(result / "predictions.jsonl"),
        "errors_sha256": file_sha256(result / "errors.jsonl"),
        "run_log_sha256": file_sha256(result / "run.log"),
    }
    import json
    index = tmp_path / "index.jsonl"
    index.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    assert verify_index(index, tmp_path) == []


def test_result_index_detects_modified_output(tmp_path: Path):
    result = tmp_path / "run"
    result.mkdir()
    for name in ("run.json", "metrics.json", "predictions.jsonl", "errors.jsonl", "run.log"):
        (result / name).write_text("original", encoding="utf-8")
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("manifest", encoding="utf-8")
    import json
    entry = {
        "experiment_id": "TEST_002", "result_path": "run",
        "dataset_manifest_path": str(manifest), "dataset_manifest_sha256": file_sha256(manifest),
        "run_sha256": file_sha256(result / "run.json"),
        "metrics_sha256": file_sha256(result / "metrics.json"),
        "predictions_sha256": file_sha256(result / "predictions.jsonl"),
        "errors_sha256": file_sha256(result / "errors.jsonl"),
        "run_log_sha256": file_sha256(result / "run.log"),
    }
    index = tmp_path / "index.jsonl"
    index.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    (result / "metrics.json").write_text("modified", encoding="utf-8")
    assert any("metrics.json" in error for error in verify_index(index, tmp_path))


def test_result_index_resolves_relative_manifest_from_repository_root(tmp_path: Path):
    result = tmp_path / "run"
    result.mkdir()
    for name in ("run.json", "metrics.json", "predictions.jsonl", "errors.jsonl", "run.log"):
        (result / name).write_text("x", encoding="utf-8")
    manifest = tmp_path / "fixtures/manifest.json"
    manifest.parent.mkdir()
    manifest.write_text("fixture", encoding="utf-8")
    import json
    entry = {
        "experiment_id": "TEST_003", "result_path": "run",
        "dataset_manifest_path": "fixtures/manifest.json", "dataset_manifest_sha256": file_sha256(manifest),
        **{key: file_sha256(result / filename) for key, filename in {
            "run_sha256": "run.json", "metrics_sha256": "metrics.json",
            "predictions_sha256": "predictions.jsonl", "errors_sha256": "errors.jsonl",
            "run_log_sha256": "run.log",
        }.items()},
    }
    index = tmp_path / "index.jsonl"
    index.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    assert verify_index(index, tmp_path) == []
