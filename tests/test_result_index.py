from pathlib import Path

from geologparser.result_index import (
    artifact_manifest_errors, file_sha256, formal_evidence_errors, verify_index,
    write_artifact_manifest,
)


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


def test_formal_benchmark_requires_ground_truth_hash_and_human_scope():
    entry = {"paper_eligibility": "formal_benchmark"}
    errors = formal_evidence_errors(
        entry, {"config": {}, "split_version": "engineering_no_ground_truth"},
        {"scope": "audit", "document_count": 0},
    )
    assert any("ground_truth_sha256" in error for error in errors)
    assert any("human-GT" in error for error in errors)
    assert any("positive document_count" in error for error in errors)


def test_formal_paper_specific_protocol_gates():
    run = {"config": {"ground_truth_sha256": "a" * 64}, "split_version": "project_disjoint_v001"}
    assert formal_evidence_errors(
        {"paper_eligibility": "formal_method"}, run,
        {"protocol": "paper2_one_module_ablation_matrix_v001", "complete_expected_matrix": True},
    ) == []
    assert formal_evidence_errors(
        {"paper_eligibility": "formal_downstream"}, run,
        {"data_status": "human_verified_real_site", "comparison": "raw_vs_qc_vs_ground_truth"},
    ) == []
    assert formal_evidence_errors(
        {"paper_eligibility": "formal_downstream"}, run, {"data_status": "synthetic"},
    )


def test_formal_authoritative_metadata_method_requires_narrow_scope():
    run = {"config": {"ground_truth_sha256": "a" * 64}, "split_version": "same_source_v001"}
    assert formal_evidence_errors(
        {"paper_eligibility": "formal_authoritative_metadata_method"}, run,
        {
            "scope": "authoritative-metadata consensus/abstention evaluation",
            "reference_ground_truth_tier": "AUTHORITATIVE_METADATA",
            "document_count": 31,
            "interval_ground_truth_available": False,
        },
    ) == []
    assert formal_evidence_errors(
        {"paper_eligibility": "formal_authoritative_metadata_method"}, run,
        {"scope": "human-GT benchmark evaluation", "document_count": 31},
    )


def test_formal_authoritative_interval_requires_source_agreement_scope():
    run = {
        "config": {"ground_truth_sha256": "a" * 64},
        "split_version": "source_agreement_explicit_table_v001",
    }
    assert formal_evidence_errors(
        {"paper_eligibility": "formal_authoritative_interval"}, run,
        {
            "scope": "authoritative-interval benchmark evaluation",
            "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
            "document_count": 9,
            "reference_interval_count": 21,
            "prediction_reference_conditioning": "none",
        },
    ) == []
    errors = formal_evidence_errors(
        {"paper_eligibility": "formal_authoritative_interval"}, run,
        {
            "scope": "human-GT benchmark evaluation",
            "reference_ground_truth_tier": "GOLD",
            "document_count": 0,
            "reference_interval_count": 0,
            "prediction_reference_conditioning": "official_final_depth",
        },
    )
    assert any("authoritative interval scope" in error for error in errors)
    assert any("GOLD_AUTHORITATIVE_SOURCE_AGREEMENT" in error for error in errors)
    assert any("positive document_count" in error for error in errors)
    assert any("positive reference_interval_count" in error for error in errors)
    assert any("prediction_reference_conditioning=none" in error for error in errors)


def test_formal_authoritative_metadata_robustness_requires_narrow_scope():
    run = {"config": {"ground_truth_sha256": "a" * 64}, "split_version": "controlled_v001"}
    assert formal_evidence_errors(
        {"paper_eligibility": "formal_authoritative_metadata_robustness"}, run,
        {
            "scope": "authoritative-metadata controlled-degradation evaluation",
            "reference_ground_truth_tier": "AUTHORITATIVE_METADATA",
            "document_count": 31,
            "profile_count": 7,
            "interval_ground_truth_available": False,
            "final_depth_ground_truth_evaluated": False,
        },
    ) == []
    assert formal_evidence_errors(
        {"paper_eligibility": "formal_authoritative_metadata_robustness"}, run,
        {"scope": "audit", "document_count": 31, "profile_count": 1},
    )


def test_formal_source_controlled_downstream_requires_explicit_boundary():
    run = {"config": {"ground_truth_sha256": "a" * 64}, "split_version": "controlled_v001"}
    assert formal_evidence_errors(
        {"paper_eligibility": "formal_source_controlled_downstream"}, run,
        {
            "data_status": "real_structured_source_controlled_error_injection",
            "comparison": "raw_vs_consensus_qc_vs_source_reference",
            "human_ground_truth_evidence": False,
        },
    ) == []


def test_nonformal_labels_do_not_require_ground_truth_evidence():
    assert formal_evidence_errors(
        {"paper_eligibility": "audit_only"}, {"config": {}}, {},
    ) == []


def test_result_index_verifies_recursive_artifact_manifest(tmp_path: Path):
    import json

    result = tmp_path / "run"
    nested = result / "case_artifacts/case-1"
    nested.mkdir(parents=True)
    for name in ("run.json", "metrics.json", "predictions.jsonl", "errors.jsonl", "run.log"):
        (result / name).write_text("{}\n" if name.endswith(".json") else "")
    (result / "input_manifest.json").write_text('{"case": 1}\n')
    (nested / "roi.png").write_bytes(b"pixels")
    manifest_path = write_artifact_manifest(result)
    assert artifact_manifest_errors(result, manifest_path) == []
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text("{}\n")
    entry = {
        "experiment_id": "ARTIFACT_001", "result_path": "run",
        "dataset_manifest_path": str(dataset), "dataset_manifest_sha256": file_sha256(dataset),
        **{key: file_sha256(result / filename) for key, filename in {
            "run_sha256": "run.json", "metrics_sha256": "metrics.json",
            "predictions_sha256": "predictions.jsonl", "errors_sha256": "errors.jsonl",
            "run_log_sha256": "run.log",
        }.items()},
        "artifact_manifest_sha256": file_sha256(manifest_path),
    }
    index = tmp_path / "index.jsonl"
    index.write_text(json.dumps(entry) + "\n")
    assert verify_index(index, tmp_path) == []
    (nested / "roi.png").write_bytes(b"changed")
    assert any("artifact" in error and "roi.png" in error for error in verify_index(index, tmp_path))


def test_artifact_manifest_rejects_path_escape(tmp_path: Path):
    import json

    result = tmp_path / "run"
    result.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("private")
    manifest = result / "artifact_manifest.json"
    manifest.write_text(json.dumps({
        "artifact_manifest_schema_version": "experiment_artifacts_v001",
        "artifacts": [{
            "path": "../outside.txt", "size_bytes": outside.stat().st_size,
            "sha256": file_sha256(outside),
        }],
    }))
    assert artifact_manifest_errors(result, manifest) == [
        "artifact path escapes result directory: ../outside.txt"
    ]


def test_artifact_manifest_rejects_unlisted_extra_file(tmp_path: Path):
    result = tmp_path / "run"
    result.mkdir()
    (result / "listed.txt").write_text("listed")
    manifest = write_artifact_manifest(result)
    (result / "unlisted.txt").write_text("unlisted")
    assert artifact_manifest_errors(result, manifest) == ["unlisted artifact: unlisted.txt"]
