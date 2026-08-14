#!/usr/bin/env python3
"""Freeze a content-grouped development/held-out split before model evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geologparser.result_index import file_sha256


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def freeze_split(
    source_manifest: Path,
    output_root: Path,
    *,
    version: str,
    development_fraction: float = 0.5,
    salt: str = "geologparser-swissgeol-split-v001",
    excluded_manifests: list[Path] | None = None,
) -> dict:
    if not 0.0 < development_fraction < 1.0:
        raise ValueError("development_fraction must be between zero and one")
    if not version.startswith("v") or not version[1:].isdigit():
        raise ValueError("version must look like v003")
    output_root.mkdir(parents=True, exist_ok=True)
    development_path = output_root / f"gold_interval_manifest_development_{version}.jsonl"
    heldout_path = output_root / f"gold_interval_manifest_heldout_{version}.jsonl"
    summary_path = output_root / f"gold_interval_split_summary_{version}.json"
    existing = [path for path in (development_path, heldout_path, summary_path) if path.exists()]
    if existing:
        raise FileExistsError("immutable split output already exists: " + ", ".join(map(str, existing)))

    rows = load_jsonl(source_manifest)
    if not rows:
        raise ValueError("source manifest is empty")
    record_ids = [row["record_id"] for row in rows]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("source manifest contains duplicate record IDs")

    excluded_rows = [
        row
        for manifest in (excluded_manifests or [])
        for row in load_jsonl(manifest)
    ]
    excluded_ids = {row["record_id"] for row in excluded_rows}
    excluded_pdf_hashes = {row["pdf_sha256"] for row in excluded_rows}
    record_overlap = sorted(set(record_ids) & excluded_ids)
    pdf_overlap = sorted({row["pdf_sha256"] for row in rows} & excluded_pdf_hashes)
    if record_overlap or pdf_overlap:
        raise ValueError(
            f"source overlaps excluded manifests: records={record_overlap}, pdf_sha256={pdf_overlap}"
        )

    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["pdf_sha256"], []).append(row)
    ordered_groups = sorted(
        groups.items(),
        key=lambda item: hashlib.sha256(f"{salt}:{item[0]}".encode()).hexdigest(),
    )
    development_group_count = round(len(ordered_groups) * development_fraction)
    development_hashes = {key for key, _ in ordered_groups[:development_group_count]}
    development = [row for row in rows if row["pdf_sha256"] in development_hashes]
    heldout = [row for row in rows if row["pdf_sha256"] not in development_hashes]
    development.sort(key=lambda row: row["record_id"])
    heldout.sort(key=lambda row: row["record_id"])

    def write(path: Path, values: list[dict]) -> None:
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in values),
            encoding="utf-8",
        )

    write(development_path, development)
    write(heldout_path, heldout)
    summary = {
        "version": version,
        "split_method": "sha256_salted_pdf_content_group_split",
        "salt": salt,
        "development_fraction_target": development_fraction,
        "source_manifest": str(source_manifest),
        "source_manifest_sha256": file_sha256(source_manifest),
        "source_documents": len(rows),
        "source_intervals": sum(int(row["interval_count"]) for row in rows),
        "content_group_count": len(groups),
        "duplicate_pdf_document_count": len(rows) - len(groups),
        "development_manifest": str(development_path),
        "development_manifest_sha256": file_sha256(development_path),
        "development_documents": len(development),
        "development_intervals": sum(int(row["interval_count"]) for row in development),
        "heldout_manifest": str(heldout_path),
        "heldout_manifest_sha256": file_sha256(heldout_path),
        "heldout_documents": len(heldout),
        "heldout_intervals": sum(int(row["interval_count"]) for row in heldout),
        "development_heldout_record_overlap": 0,
        "development_heldout_pdf_hash_overlap": 0,
        "excluded_manifest_sha256": {
            str(path): file_sha256(path) for path in (excluded_manifests or [])
        },
        "excluded_record_overlap": 0,
        "excluded_pdf_hash_overlap": 0,
        "human_reviewed": False,
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--development-fraction", type=float, default=0.5)
    parser.add_argument("--salt", default="geologparser-swissgeol-split-v001")
    parser.add_argument("--exclude-manifest", type=Path, action="append", default=[])
    args = parser.parse_args()
    summary = freeze_split(
        args.source_manifest,
        args.output_root,
        version=args.version,
        development_fraction=args.development_fraction,
        salt=args.salt,
        excluded_manifests=args.exclude_manifest,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
