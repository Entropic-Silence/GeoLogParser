#!/usr/bin/env python3
"""Build the portable, versioned public-data companion release.

The source payload is copied from a controlled data root. Release metadata and
machine-readable paths are normalized in the staged copy; the controlled source
files are never edited. Scientific values, labels, evidence tiers, and binary
source assets are preserved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path("/data/GeoLogParser/datasets")
BUNDLE_ID = "GeoLogParser-public-data-v002"
BUNDLE_DIRECTORY = "dataset_bundle_v002"
RELEASE_TAG = "data-v002"
RELEASE_DATE = "2026-08-20"
RELEASE_RIGHTS_STATUS = "AUTHOR_VERIFIED_FOR_PUBLIC_RELEASE_2026-08-20"
PAPER4_RELEASE_METADATA = json.loads(
    (ROOT / "papers" / "paper4" / "release_metadata.json").read_text(encoding="utf-8")
)
PAPER4_PACKAGE_TAG = PAPER4_RELEASE_METADATA["release_tag"]
ABSOLUTE_PREFIXES = ("/data/GeoLogParser/", "/root/GeoLogParser/")
TEXT_SUFFIXES = {".json", ".jsonl", ".yaml", ".yml", ".md", ".txt", ".csv"}


DATASETS = (
    ("public/california_wcr_gold_v001", "datasets/public/california_wcr_gold_v001", "CC0 published USGS manual transcription and author-reviewed public report pairing; retain USGS citation and source linkage"),
    ("public/california_wcr_gold_v002", "datasets/public/california_wcr_gold_v002", "CC0 published USGS manual transcription and author-reviewed public report pairing; retain USGS citation and source linkage"),
    ("public/california_wcr_gold_v003", "datasets/public/california_wcr_gold_v003", "CC0 published USGS manual transcription and author-reviewed public report pairing; retain USGS citation and source linkage"),
    ("public/california_wcr_gold_v004", "datasets/public/california_wcr_gold_v004", "CC0 published USGS manual transcription and author-reviewed public report pairing; retain USGS citation and source linkage"),
    ("public/california_wcr_gold_v005", "datasets/public/california_wcr_gold_v005", "CC0 published USGS manual transcription and author-reviewed public report pairing; retain USGS citation and source linkage"),
    ("public/bgs_offshore_paired_v001", "datasets/public/bgs_offshore_paired_v001", "BGS OGL v3 is stated in the official record; author reviewed the selected item scope for public release; preserve BGS acknowledgement and embedded legacy-footer caveat"),
    ("public/bgs_offshore_validation_v002r2", "datasets/public/bgs_offshore_validation_v002r2", "BGS OGL v3 is stated in the official record; author reviewed the selected item scope for public release; preserve BGS acknowledgement and embedded legacy-footer caveat"),
    ("public/bgs_offshore_paired_v003", "datasets/public/bgs_offshore_paired_v003", "BGS OGL v3 is stated in the official record; author reviewed the selected item scope for public release; preserve BGS acknowledgement and embedded legacy-footer caveat"),
    ("public/bgs_v001", "datasets/public/bgs_v001", "BGS OGL v3; author-reviewed public release scope; preserve BGS acknowledgement and source terms"),
    ("public/swissgeol_thurgau_paired_v003", "datasets/public/swissgeol_thurgau_paired_v003", "No standardized licence is asserted by this project; the project owner manually reviewed and approved the selected public-source item scope, attribution, linkage, privacy, sensitive-location, and embedded-content considerations for data-v002"),
    ("public/usgs_raft_river_12_v001", "datasets/public/usgs_raft_river_12_v001", "USGS public-domain release; author reviewed the included records and embedded IDWR-form scope; preserve USGS/IDWR attribution"),
    ("public/mendeley_coal_boreholes_602_v001", "datasets/public/mendeley_coal_boreholes_602_v001", "CC BY 4.0; author reviewed the included item and spatial fields; retain DOI, creator attribution, licence, and modification notice"),
    ("synthetic_borehole_logs_v002", "datasets/synthetic_borehole_logs_v002", "Project-generated synthetic data; project-owner-authorized for public research distribution; no standardized dataset licence is asserted"),
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
    if os.name == "nt":
        source_native = "\\\\?\\" + str(source.resolve())
        destination_native = "\\\\?\\" + str(destination.resolve())
        shutil.copytree(source_native, destination_native, dirs_exist_ok=True)
    else:
        shutil.copytree(source, destination, dirs_exist_ok=True)


def normalize_string(value: str) -> str:
    for prefix in ABSOLUTE_PREFIXES:
        value = value.replace(prefix, "")
    value = value.replace("synthetic_borehole_logs_v001", "synthetic_borehole_logs_v002")
    value = value.replace("SYNTHETIC_V001", "SYNTHETIC_V002")
    if value == "PENDING_MANUAL_PRE_SUBMISSION_REVIEW":
        value = RELEASE_RIGHTS_STATUS
    return value


def normalize_json(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_string(value)
    if isinstance(value, list):
        return [normalize_json(item) for item in value]
    if isinstance(value, dict):
        return {normalize_string(str(key)): normalize_json(item) for key, item in value.items()}
    return value


def structured_paths(stage: Path) -> list[Path]:
    return sorted(
        path for path in (stage / "datasets").rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
    )


def normalize_structured_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = normalize_json(json.loads(original))
        normalized = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    elif suffix == ".jsonl":
        rows = [
            json.dumps(normalize_json(json.loads(line)), ensure_ascii=False, sort_keys=True)
            for line in original.splitlines() if line.strip()
        ]
        normalized = "\n".join(rows) + ("\n" if rows else "")
    else:
        normalized = normalize_string(original)
    if normalized == original:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def replace_hashes(path: Path, replacements: dict[str, str]) -> bool:
    original = path.read_text(encoding="utf-8")
    normalized = original
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    if normalized == original:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def normalize_release_metadata(stage: Path) -> dict[str, int]:
    """Normalize staged metadata and repair checksums that reference changed files."""
    paths = structured_paths(stage)
    previous_hashes = {path: sha256(path) for path in paths}
    normalized_count = sum(normalize_structured_file(path) for path in paths)
    hash_rewrite_count = 0

    for _ in range(12):
        current_hashes = {path: sha256(path) for path in paths}
        replacements = {
            previous_hashes[path]: current_hashes[path]
            for path in paths if previous_hashes[path] != current_hashes[path]
        }
        if not replacements:
            break
        changed = sum(replace_hashes(path, replacements) for path in paths)
        hash_rewrite_count += changed
        previous_hashes = current_hashes
        if not changed:
            break
    else:
        raise RuntimeError("structured checksum references did not converge")

    return {
        "normalized_files": normalized_count,
        "checksum_reference_rewrites": hash_rewrite_count,
    }


def copy_release_metadata(stage: Path) -> Path:
    source = ROOT / "datasets" / "public" / BUNDLE_DIRECTORY
    destination = stage / "datasets" / "public" / BUNDLE_DIRECTORY
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("README.md", "CITATION.cff", "DATA_LICENSES.md", "release_metadata.json"):
        shutil.copyfile(source / name, destination / name)
    return destination


def iter_dataset_files(stage: Path, archive_rel: str) -> Iterable[Path]:
    destination = stage / archive_rel
    return sorted(path for path in destination.rglob("*") if path.is_file())


def build_manifest(stage: Path, normalization: dict[str, int]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    total_bytes = 0
    total_files = 0
    for source_rel, archive_rel, rights_note in DATASETS:
        files = []
        for path in iter_dataset_files(stage, archive_rel):
            relative = path.relative_to(stage).as_posix()
            size = path.stat().st_size
            files.append({"path": relative, "bytes": size, "sha256": sha256(path)})
            total_bytes += size
            total_files += 1
        records.append({
            "source_path": source_rel,
            "archive_path": archive_rel,
            "file_count": len(files),
            "bytes": sum(row["bytes"] for row in files),
            "rights_note": rights_note,
            "files": files,
        })
    return {
        "bundle_id": BUNDLE_ID,
        "release_tag": RELEASE_TAG,
        "created_utc": RELEASE_DATE,
        "project": "GeoLogParser",
        "release_role": "data companion; not the complete Paper 4 reproducibility package",
        "paper4_package_tag": "paper4-cageo-v1.0.1",
        "paper4_current_package_tag": PAPER4_PACKAGE_TAG,
        "paper4_package_relationship": (
            "data-v002 was originally paired with paper4-cageo-v1.0.1 and is reused "
            "unchanged by later Paper 4 releases"
        ),
        "archive_layout": "repository-relative paths; extract at repository root",
        "publication_status": "author_verified_public_release",
        "author_rights_review": {
            "reviewer": "Yifan Du",
            "reviewed_on": RELEASE_DATE,
            "scope": "source terms, selected item scope, privacy, sensitive locations, embedded third-party content, attribution, and linkage",
        },
        "path_normalization": normalization,
        "total_files": total_files,
        "total_bytes": total_bytes,
        "datasets": records,
    }


def write_payload_checksums(manifest: dict[str, Any], destination: Path) -> None:
    lines = [
        f"{row['sha256']}  {row['path']}"
        for dataset in manifest["datasets"] for row in dataset["files"]
    ]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def audit_stage(stage: Path) -> dict[str, Any]:
    errors: list[str] = []
    absolute_hits: list[str] = []
    legacy_synthetic_hits: list[str] = []
    pending_rights_hits: list[str] = []
    for path in structured_paths(stage):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(stage).as_posix()
        if any(prefix in text for prefix in ABSOLUTE_PREFIXES):
            absolute_hits.append(relative)
        if "synthetic_borehole_logs_v001" in text or "SYNTHETIC_V001" in text:
            legacy_synthetic_hits.append(relative)
        if "PENDING_MANUAL_PRE_SUBMISSION_REVIEW" in text:
            pending_rights_hits.append(relative)
    if absolute_hits:
        errors.append(f"absolute GeoLogParser paths remain in {len(absolute_hits)} files")
    if legacy_synthetic_hits:
        errors.append(f"legacy synthetic v001 identity remains in {len(legacy_synthetic_hits)} files")
    if pending_rights_hits:
        errors.append(f"pending release-rights status remains in {len(pending_rights_hits)} files")

    synthetic = stage / "datasets" / "synthetic_borehole_logs_v002"
    summary = json.loads((synthetic / "summary.json").read_text(encoding="utf-8"))
    if summary.get("dataset_version") != "synthetic_borehole_logs_v002":
        errors.append("synthetic summary dataset_version is not v002")
    source_ids = {
        json.loads(line)["source_id"]
        for line in (synthetic / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    if source_ids != {"SYNTHETIC_V002"}:
        errors.append(f"unexpected synthetic source IDs: {sorted(source_ids)}")
    if errors:
        raise RuntimeError("; ".join(errors))
    return {
        "absolute_path_files": len(absolute_hits),
        "legacy_synthetic_identity_files": len(legacy_synthetic_hits),
        "pending_rights_files": len(pending_rights_hits),
        "synthetic_source_ids": sorted(source_ids),
    }


def create_archive(stage: Path, archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    gnu_command = [
        "tar", "--zstd", "--sort=name", f"--mtime={RELEASE_DATE}T00:00:00Z",
        "--owner=0", "--group=0", "--numeric-owner", "-cf", str(archive),
        "-C", str(stage), "datasets",
    ]
    portable_command = ["tar", "-a", "-cf", str(archive), "-C", str(stage), "datasets"]
    result = subprocess.run(gnu_command, capture_output=True, text=True)
    if result.returncode:
        archive.unlink(missing_ok=True)
        subprocess.run(portable_command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument(
        "--sync-repository-metadata",
        action="store_true",
        help="copy the generated manifest and payload checksums into datasets/public/dataset_bundle_v002",
    )
    args = parser.parse_args()
    stage = args.stage or Path(tempfile.mkdtemp(prefix="geologparser-public-data-v002-"))
    stage.mkdir(parents=True, exist_ok=True)

    for source_rel, archive_rel, _ in DATASETS:
        copy_tree(args.data_root / source_rel, stage / archive_rel)

    normalization = normalize_release_metadata(stage)
    metadata_dir = copy_release_metadata(stage)
    manifest = build_manifest(stage, normalization)
    manifest_path = metadata_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    sums_path = metadata_dir / "SHA256SUMS"
    write_payload_checksums(manifest, sums_path)
    audit = audit_stage(stage)

    if args.sync_repository_metadata:
        repository_metadata = ROOT / "datasets" / "public" / BUNDLE_DIRECTORY
        shutil.copyfile(manifest_path, repository_metadata / "manifest.json")
        shutil.copyfile(sums_path, repository_metadata / "SHA256SUMS")

    archive_sha256_path = None
    if args.archive:
        create_archive(stage, args.archive)
        archive_digest = sha256(args.archive)
        archive_sha256_path = Path(str(args.archive) + ".sha256")
        archive_sha256_path.write_text(
            f"{archive_digest}  {args.archive.name}\n", encoding="utf-8", newline="\n"
        )

    print(json.dumps({
        "stage": str(stage),
        "archive": str(args.archive) if args.archive else None,
        "archive_sha256_file": str(archive_sha256_path) if archive_sha256_path else None,
        "manifest": str(manifest_path),
        "total_files": manifest["total_files"],
        "total_bytes": manifest["total_bytes"],
        "normalization": normalization,
        "audit": audit,
    }, indent=2))


if __name__ == "__main__":
    main()
