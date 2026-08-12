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
FORMAL_ELIGIBILITY = {"formal_benchmark", "formal_method", "formal_downstream"}


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
    if eligibility == "formal_benchmark":
        if metrics.get("scope") != "human-GT benchmark evaluation":
            errors.append("formal_benchmark requires human-GT benchmark metrics scope")
        if not isinstance(metrics.get("document_count"), int) or metrics.get("document_count", 0) <= 0:
            errors.append("formal_benchmark requires a positive document_count")
    elif eligibility == "formal_method":
        if metrics.get("protocol") != "paper2_one_module_ablation_matrix_v001":
            errors.append("formal_method requires Paper II ablation protocol")
        if metrics.get("complete_expected_matrix") is not True:
            errors.append("formal_method requires the complete expected ablation matrix")
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
