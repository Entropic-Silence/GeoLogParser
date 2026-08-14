#!/usr/bin/env python3
"""Freeze all acquired non-Thurgau Swissgeol pairs for transfer evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


DATA_ROOT = Path("/data/GeoLogParser/datasets/public")
OUTPUT = DATA_ROOT / "swissgeol_cross_canton_transfer_v001"
SOURCES = {
    "St. Gallen": DATA_ROOT / "swissgeol_stgallen_paired_v001",
    "Bern": DATA_ROOT / "swissgeol_bern_paired_v001",
    "Solothurn": DATA_ROOT / "swissgeol_solothurn_paired_v001",
    "Vaud": DATA_ROOT / "swissgeol_vaud_paired_v001",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = []
    source_hashes = {}
    for canton, root in SOURCES.items():
        manifest = root / "manifest.jsonl"
        source_hashes[canton] = sha256(manifest)
        dataset = json.loads((root / "dataset.json").read_text(encoding="utf-8"))
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append({
                **row,
                "canton": canton,
                "source_family": f"swissgeol_{canton.lower().replace(' ', '_').replace('.', '')}",
                "source_dataset_version": dataset["dataset_version"],
                "human_reviewed": False,
                "reference_tier": "AUTHORITATIVE_STRUCTURED_SOURCE",
                "page_database_interval_agreement_verified": False,
                "evaluation_role": "source_disjoint_transfer_from_thurgau_development",
            })
    rows.sort(key=lambda row: (row["canton"], row["record_id"]))
    if len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate record ID across canton sources")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = OUTPUT / "manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "dataset_version": "swissgeol_cross_canton_transfer_v001",
        "source": "four acquired non-Thurgau Swissgeol canton collections",
        "source_cantons": sorted(SOURCES),
        "source_count": len(SOURCES),
        "frozen_documents": len(rows),
        "frozen_intervals": sum(int(row["interval_count"]) for row in rows),
        "manifest_sha256": sha256(manifest),
        "source_manifest_sha256": source_hashes,
        "selection_policy": "all acquired paired documents; no content, prediction, or reference-value filtering",
        "development_source": "Thurgau",
        "development_evaluation_record_overlap": 0,
        "reference_type": "official_database_derived_structured_source",
        "page_database_interval_agreement_verified": False,
        "human_reviewed": False,
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
    }
    (OUTPUT / "dataset.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(f"{manifest}\ndocuments={len(rows)}\nintervals={summary['frozen_intervals']}")


if __name__ == "__main__":
    main()
