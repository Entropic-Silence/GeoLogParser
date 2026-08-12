"""Minimal immutable experiment-directory management."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Mapping


REQUIRED_METADATA = (
    "experiment_id", "git_commit", "date", "dataset_version", "split_version",
    "model", "model_revision", "prompt_version", "seed", "hardware", "software", "config",
)


def create_run_directory(results_root: Path, metadata: Mapping[str, Any]) -> Path:
    missing = [name for name in REQUIRED_METADATA if name not in metadata]
    if missing:
        raise ValueError(f"missing required experiment metadata: {', '.join(missing)}")
    run_date = str(metadata["date"])
    try:
        date.fromisoformat(run_date)
    except ValueError as exc:
        raise ValueError("date must be ISO YYYY-MM-DD") from exc
    experiment_id = str(metadata["experiment_id"])
    if not experiment_id or any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for character in experiment_id):
        raise ValueError("experiment_id must contain only letters, digits, underscores, or hyphens")
    destination = results_root / run_date / experiment_id
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "run.json").write_text(json.dumps(dict(metadata), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for filename, initial in (("metrics.json", "{}\n"), ("predictions.jsonl", ""), ("errors.jsonl", ""), ("run.log", "")):
        (destination / filename).write_text(initial, encoding="utf-8")
    return destination

