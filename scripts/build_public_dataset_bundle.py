#!/usr/bin/env python3
"""Build the versioned public-data release bundle.

The repository stores the bundle manifest and release instructions.  The
source files themselves are assembled from the controlled data root and are
published as a GitHub Release asset so a normal git clone stays lightweight.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


DATA_ROOT = Path("/data/GeoLogParser/datasets")

DATASETS = (
    ("public/california_wcr_gold_v001", "datasets/public/california_wcr_gold_v001", "CC0 / published USGS manual transcription; retain USGS citation"),
    ("public/california_wcr_gold_v002", "datasets/public/california_wcr_gold_v002", "CC0 / published USGS manual transcription; retain USGS citation"),
    ("public/california_wcr_gold_v003", "datasets/public/california_wcr_gold_v003", "CC0 / published USGS manual transcription; retain USGS citation"),
    ("public/california_wcr_gold_v004", "datasets/public/california_wcr_gold_v004", "CC0 / published USGS manual transcription; retain USGS citation"),
    ("public/california_wcr_gold_v005", "datasets/public/california_wcr_gold_v005", "CC0 / published USGS manual transcription; retain USGS citation"),
    ("public/bgs_offshore_paired_v001", "datasets/public/bgs_offshore_paired_v001", "BGS OGL v3 stated in official record; preserve BGS acknowledgement and legacy-footer caveat"),
    ("public/bgs_offshore_validation_v002r2", "datasets/public/bgs_offshore_validation_v002r2", "BGS OGL v3 stated in official record; preserve BGS acknowledgement and legacy-footer caveat"),
    ("public/bgs_offshore_paired_v003", "datasets/public/bgs_offshore_paired_v003", "BGS OGL v3 stated in official record; preserve BGS acknowledgement and legacy-footer caveat"),
    ("public/bgs_v001", "datasets/public/bgs_v001", "BGS OGL v3; preserve BGS acknowledgement and source terms"),
    ("public/swissgeol_thurgau_paired_v003", "datasets/public/swissgeol_thurgau_paired_v003", "Public source pairing; publication authorization asserted by project owner; source terms remain flagged for final verification"),
    ("public/usgs_raft_river_12_v001", "datasets/public/usgs_raft_river_12_v001", "USGS public-domain release; preserve USGS citation and embedded-form caveat"),
    ("public/mendeley_coal_boreholes_602_v001", "datasets/public/mendeley_coal_boreholes_602_v001", "CC BY 4.0; retain DOI/creator attribution; transformed spatial outputs remain separately governed"),
    ("synthetic_borehole_logs_v002", "datasets/synthetic_borehole_logs_v002", "Project-generated synthetic data; known programmatic ground truth"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(f"missing dataset directory: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)


def build_manifest(stage: Path) -> dict:
    records = []
    total_bytes = 0
    total_files = 0
    for source_rel, archive_rel, rights_note in DATASETS:
        source = DATA_ROOT / source_rel
        destination = stage / archive_rel
        copy_tree(source, destination)
        files = []
        for path in sorted(p for p in destination.rglob("*") if p.is_file()):
            relative = path.relative_to(stage).as_posix()
            size = path.stat().st_size
            files.append({"path": relative, "bytes": size, "sha256": sha256(path)})
            total_bytes += size
            total_files += 1
        records.append(
            {
                "source_path": source_rel,
                "archive_path": archive_rel,
                "file_count": len(files),
                "bytes": sum(row["bytes"] for row in files),
                "rights_note": rights_note,
                "files": files,
            }
        )
    return {
        "bundle_id": "GeoLogParser-public-data-v001",
        "created_utc": "2026-08-18",
        "project": "GeoLogParser",
        "archive_layout": "repository-relative paths; extract at repository root",
        "publication_status": "project_owner_authorized_public_release_pending_final_source_terms_check",
        "total_files": total_files,
        "total_bytes": total_bytes,
        "datasets": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    stage = args.stage or Path(tempfile.mkdtemp(prefix="geologparser-public-data-v001-"))
    stage.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(stage)
    manifest_path = stage / "datasets/public/dataset_bundle_v001/manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    repository_readme = Path(__file__).resolve().parent.parent / "datasets/public/dataset_bundle_v001/README.md"
    if repository_readme.is_file():
        shutil.copyfile(repository_readme, manifest_path.parent / "README.md")
    if args.archive:
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["tar", "--zstd", "--sort=name", "--mtime=2026-08-18T00:00:00Z", "--owner=0", "--group=0", "--numeric-owner", "-cf", str(args.archive), "-C", str(stage), "datasets"],
            check=True,
        )
    print(json.dumps({"stage": str(stage), "archive": str(args.archive) if args.archive else None, "manifest": str(manifest_path), "total_files": manifest["total_files"], "total_bytes": manifest["total_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
