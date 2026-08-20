from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_paper4_outer_artifact_manifest_matches_committed_files() -> None:
    root = Path(__file__).resolve().parents[1]
    cageo = root / "papers/paper4/submission/cageo"
    manifest_path = cageo / "CAGEO_ARTIFACT_MANIFEST.json"
    delivery_path = root / "papers/paper4/submission_bundle/Paper4_Final_Delivery_SHA256.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    delivery = json.loads(delivery_path.read_text(encoding="utf-8"))

    assert manifest["release_tag"] == "paper4-cageo-v1.0.7"
    assert manifest["branch"]
    assert re.fullmatch(r"[0-9a-f]{40}", str(manifest["source_git_commit"]))
    assert manifest["source_git_commit_scope"]
    assert manifest["files"]

    for entry in manifest["files"]:
        path = root / entry["file"]
        assert path.is_file(), entry["file"]
        assert path.stat().st_size == entry["bytes"], entry["file"]
        assert sha256(path) == entry["sha256"], entry["file"]

    for entry in delivery["files"]:
        path = root / "papers/paper4/submission_bundle" / entry["name"]
        assert path.is_file(), entry["name"]
        assert path.stat().st_size == entry["bytes"], entry["name"]
        assert sha256(path) == entry["sha256"], entry["name"]
