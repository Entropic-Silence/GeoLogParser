#!/usr/bin/env python3
"""Append one immutable run to a version-controlled hash index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.result_index import (
    ARTIFACT_MANIFEST, HASH_PATHS, artifact_manifest_errors, file_sha256,
    formal_evidence_errors,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_path", type=Path)
    parser.add_argument("index_path", type=Path)
    parser.add_argument("dataset_manifest_path", type=Path)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--paper-eligibility", required=True)
    arguments = parser.parse_args()
    run = json.loads((arguments.result_path / "run.json").read_text(encoding="utf-8"))
    existing = [
        json.loads(line) for line in arguments.index_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if arguments.index_path.exists() else []
    if any(item["experiment_id"] == run["experiment_id"] for item in existing):
        raise ValueError(f"experiment already indexed: {run['experiment_id']}")
    try:
        relative_result = arguments.result_path.resolve().relative_to(ROOT)
    except ValueError as exc:
        raise ValueError("result path must be inside repository") from exc
    manifest_resolved = arguments.dataset_manifest_path.resolve()
    try:
        indexed_manifest_path = str(manifest_resolved.relative_to(ROOT))
    except ValueError:
        indexed_manifest_path = str(manifest_resolved)
    entry = {
        "experiment_id": run["experiment_id"],
        "run_date": run["date"],
        "status": "completed",
        "scope": arguments.scope,
        "result_path": str(relative_result),
        "dataset_manifest_path": indexed_manifest_path,
        "dataset_manifest_sha256": file_sha256(arguments.dataset_manifest_path),
        **{hash_key: file_sha256(arguments.result_path / filename) for hash_key, filename in HASH_PATHS.items()},
        "paper_eligibility": arguments.paper_eligibility,
    }
    artifact_manifest = arguments.result_path / ARTIFACT_MANIFEST
    if artifact_manifest.is_file():
        artifact_errors = artifact_manifest_errors(arguments.result_path, artifact_manifest)
        if artifact_errors:
            raise ValueError("artifact manifest verification failed: " + "; ".join(artifact_errors))
        entry["artifact_manifest_sha256"] = file_sha256(artifact_manifest)
    metrics = json.loads((arguments.result_path / "metrics.json").read_text(encoding="utf-8"))
    evidence_errors = formal_evidence_errors(entry, run, metrics)
    if evidence_errors:
        raise ValueError("formal evidence gate failed: " + "; ".join(evidence_errors))
    arguments.index_path.parent.mkdir(parents=True, exist_ok=True)
    with arguments.index_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(run["experiment_id"])


if __name__ == "__main__":
    main()
