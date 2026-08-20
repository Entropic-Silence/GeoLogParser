from __future__ import annotations

import json
from pathlib import Path

from scripts.build_public_dataset_bundle import (
    RELEASE_RIGHTS_STATUS,
    audit_stage,
    normalize_release_metadata,
    sha256,
)


def test_release_metadata_is_portable_and_version_consistent(tmp_path: Path) -> None:
    dataset = tmp_path / "datasets" / "synthetic_borehole_logs_v002"
    dataset.mkdir(parents=True)
    manifest = dataset / "manifest.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "image_path": "/data/GeoLogParser/datasets/synthetic_borehole_logs_v002/images/SYN-0001.png",
                "label_path": "/root/GeoLogParser/datasets/synthetic_borehole_logs_v002/labels/SYN-0001.json",
                "source_id": "SYNTHETIC_V001",
                "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    old_manifest_hash = sha256(manifest)
    summary = dataset / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "dataset_version": "synthetic_borehole_logs_v001",
                "manifest_sha256": old_manifest_hash,
            }
        ),
        encoding="utf-8",
    )

    stats = normalize_release_metadata(tmp_path)
    audit = audit_stage(tmp_path)

    record = json.loads(manifest.read_text(encoding="utf-8"))
    summary_record = json.loads(summary.read_text(encoding="utf-8"))
    assert record["image_path"].startswith("datasets/")
    assert record["label_path"].startswith("datasets/")
    assert record["source_id"] == "SYNTHETIC_V002"
    assert record["rights_review"] == RELEASE_RIGHTS_STATUS
    assert summary_record["dataset_version"] == "synthetic_borehole_logs_v002"
    assert summary_record["manifest_sha256"] == sha256(manifest)
    assert stats["normalized_files"] == 2
    assert stats["checksum_reference_rewrites"] == 1
    assert audit["absolute_path_files"] == 0
    assert audit["legacy_synthetic_identity_files"] == 0
    assert audit["pending_rights_files"] == 0
