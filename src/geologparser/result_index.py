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
        if not manifest.is_file():
            errors.append(f"{experiment_id}: missing {manifest}")
        elif file_sha256(manifest) != entry["dataset_manifest_sha256"]:
            errors.append(f"{experiment_id}: hash mismatch for {manifest}")
    return errors
