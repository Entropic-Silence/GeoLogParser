"""Hash verification for version-controlled immutable experiment indexes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HASH_PATHS = {
    "run_sha256": "run.json",
    "metrics_sha256": "metrics.json",
    "predictions_sha256": "predictions.jsonl",
    "errors_sha256": "errors.jsonl",
    "run_log_sha256": "run.log",
}
ARTIFACT_MANIFEST = "artifact_manifest.json"
FORMAL_ELIGIBILITY = {"formal_benchmark", "formal_silver_benchmark", "formal_method", "formal_synthetic_method", "formal_downstream"}


def formal_evidence_errors(entry: dict, run: dict, metrics: dict) -> list[str]:
    """Reject formal labels without frozen GT and paper-specific evidence."""
    eligibility = entry.get("paper_eligibility")
    if eligibility not in FORMAL_ELIGIBILITY:
        return []
    errors = []
    config = run.get("config", {})
    ground_truth_sha256 = config.get("ground_truth_sha256")
    if not isinstance(ground_truth_sha256, str) or len(ground_truth_sha256) != 64:
        errors.append("formal result requires config.ground_truth_sha256")
    if "no_ground_truth" in str(run.get("split_version", "")).lower():
        errors.append("formal result split_version declares no Ground Truth")
    if eligibility == "formal_silver_benchmark":
        if metrics.get("scope") != "machine-adjudicated-silver-agreement evaluation":
            errors.append("formal_silver_benchmark requires Silver agreement metrics scope")
        if metrics.get("reference_ground_truth_tier") != "SILVER":
            errors.append("formal_silver_benchmark requires SILVER reference tier")
        if not isinstance(metrics.get("document_count"), int) or metrics.get("document_count", 0) <= 0:
            errors.append("formal_silver_benchmark requires a positive document_count")
    elif eligibility == "formal_benchmark":
        if metrics.get("scope") != "human-GT benchmark evaluation":
            errors.append("formal_benchmark requires human-GT benchmark metrics scope")
        if not isinstance(metrics.get("document_count"), int) or metrics.get("document_count", 0) <= 0:
            errors.append("formal_benchmark requires a positive document_count")
    elif eligibility in {"formal_method", "formal_synthetic_method"}:
        if metrics.get("protocol") != "paper2_one_module_ablation_matrix_v001":
            errors.append("formal_method requires Paper II ablation protocol")
        if metrics.get("complete_expected_matrix") is not True:
            errors.append("formal_method requires the complete expected ablation matrix")
        if eligibility == "formal_synthetic_method" and metrics.get("ground_truth_policy") != "synthetic":
            errors.append("formal_synthetic_method requires synthetic reference policy")
    elif eligibility == "formal_downstream":
        if metrics.get("data_status") != "human_verified_real_site":
            errors.append("formal_downstream requires human_verified_real_site data_status")
        if metrics.get("comparison") != "raw_vs_qc_vs_ground_truth":
            errors.append("formal_downstream requires raw_vs_qc_vs_ground_truth comparison")
    return errors


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_artifact_manifest(result_path: Path) -> Path:
    """Hash non-core run artifacts recursively using result-relative paths."""
    result_path = result_path.resolve()
    excluded = set(HASH_PATHS.values()) | {ARTIFACT_MANIFEST}
    artifacts = []
    for path in sorted(candidate for candidate in result_path.rglob("*") if candidate.is_file()):
        relative = path.relative_to(result_path)
        if str(relative) in excluded:
            continue
        artifacts.append({
            "path": relative.as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        })
    manifest = {
        "artifact_manifest_schema_version": "experiment_artifacts_v001",
        "scope": "recursive non-core experiment artifacts; core files are hashed by result index",
        "artifacts": artifacts,
    }
    destination = result_path / ARTIFACT_MANIFEST
    destination.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def artifact_manifest_errors(result_path: Path, manifest_path: Path) -> list[str]:
    errors = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"invalid artifact manifest JSON: {exc}"]
    if manifest.get("artifact_manifest_schema_version") != "experiment_artifacts_v001":
        errors.append("unsupported artifact manifest schema")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return errors + ["artifact manifest artifacts must be an array"]
    seen = set()
    result_path = result_path.resolve()
    for item in artifacts:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            errors.append("artifact manifest entry is invalid")
            continue
        relative = Path(item["path"])
        target = (result_path / relative).resolve()
        if relative.is_absolute() or result_path not in target.parents:
            errors.append(f"artifact path escapes result directory: {item['path']}")
            continue
        if item["path"] in seen:
            errors.append(f"duplicate artifact path: {item['path']}")
            continue
        seen.add(item["path"])
        if not target.is_file():
            errors.append(f"missing artifact: {item['path']}")
            continue
        if target.stat().st_size != item.get("size_bytes"):
            errors.append(f"artifact size mismatch: {item['path']}")
        if file_sha256(target) != item.get("sha256"):
            errors.append(f"artifact hash mismatch: {item['path']}")
    excluded = set(HASH_PATHS.values()) | {ARTIFACT_MANIFEST}
    actual = {
        path.relative_to(result_path).as_posix()
        for path in result_path.rglob("*")
        if path.is_file() and path.relative_to(result_path).as_posix() not in excluded
    }
    for unlisted in sorted(actual - seen):
        errors.append(f"unlisted artifact: {unlisted}")
    return errors


def verify_index(index_path: Path, repository_root: Path) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(index_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        entry = json.loads(line)
        experiment_id = entry.get("experiment_id", f"line-{line_number}")
        result_path = repository_root / entry["result_path"]
        for hash_key, filename in HASH_PATHS.items():
            target = result_path / filename
            if not target.is_file():
                errors.append(f"{experiment_id}: missing {target}")
            elif file_sha256(target) != entry[hash_key]:
                errors.append(f"{experiment_id}: hash mismatch for {target}")
        if "artifact_manifest_sha256" in entry:
            artifact_manifest = result_path / ARTIFACT_MANIFEST
            if not artifact_manifest.is_file():
                errors.append(f"{experiment_id}: missing {artifact_manifest}")
            elif file_sha256(artifact_manifest) != entry["artifact_manifest_sha256"]:
                errors.append(f"{experiment_id}: hash mismatch for {artifact_manifest}")
            else:
                errors.extend(
                    f"{experiment_id}: {message}"
                    for message in artifact_manifest_errors(result_path, artifact_manifest)
                )
        manifest = Path(entry["dataset_manifest_path"])
        if not manifest.is_absolute():
            manifest = repository_root / manifest
        if not manifest.is_file():
            errors.append(f"{experiment_id}: missing {manifest}")
        elif file_sha256(manifest) != entry["dataset_manifest_sha256"]:
            errors.append(f"{experiment_id}: hash mismatch for {manifest}")
        run_path, metrics_path = result_path / "run.json", result_path / "metrics.json"
        if entry.get("paper_eligibility") in FORMAL_ELIGIBILITY and run_path.is_file() and metrics_path.is_file():
            try:
                run = json.loads(run_path.read_text(encoding="utf-8"))
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                errors.append(f"{experiment_id}: invalid formal-evidence JSON: {exc}")
            else:
                errors.extend(
                    f"{experiment_id}: {message}"
                    for message in formal_evidence_errors(entry, run, metrics)
                )
    return errors
