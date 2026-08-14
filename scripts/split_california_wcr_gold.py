#!/usr/bin/env python3
"""Create the frozen development/test split for California WCR Gold v001."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "datasets/manifests/california_wcr_gold_v001.jsonl"
OUTPUT = ROOT / "datasets/splits/california_wcr_gold_split_v001.json"
INSPECTED_DEVELOPMENT = {
    "WCR1952-000069",
    "WCR1986-005860",
    "WCR1999-003522",
    "WCR2016-013592",
    "WCR2018-012057",
}
SEED = "GeoLogParser-California-WCR-split-v001"


def stable_key(value: str) -> str:
    return hashlib.sha256(f"{SEED}|{value}".encode()).hexdigest()


def main() -> None:
    rows = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = {row["record_id"] for row in rows}
    if len(rows) != 60 or not INSPECTED_DEVELOPMENT <= ids:
        raise ValueError("unexpected California WCR v001 manifest")
    remaining = sorted(ids - INSPECTED_DEVELOPMENT, key=stable_key)
    development = sorted(INSPECTED_DEVELOPMENT | set(remaining[:5]))
    test = sorted(ids - set(development))
    payload = {
        "split_version": "california_wcr_gold_split_v001",
        "dataset_manifest": str(MANIFEST.relative_to(ROOT)),
        "dataset_manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "selection_seed": SEED,
        "development": development,
        "test": test,
        "development_documents": len(development),
        "test_documents": len(test),
        "policy": "Five visually inspected documents are development-only; five additional development documents are fixed by seeded SHA-256; all remaining documents are frozen test data.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
