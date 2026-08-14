#!/usr/bin/env python3
"""Freeze all acquired non-Thurgau Swissgeol pairs for transfer evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


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


def visual_content_sha256(path: Path) -> tuple[str, int]:
    """Hash a low-resolution deterministic rendering, excluding PDF metadata."""
    renderer = shutil.which("pdftoppm")
    if renderer is None:
        raise RuntimeError("pdftoppm is required")
    with tempfile.TemporaryDirectory(prefix="geologparser-visual-hash-") as temporary:
        prefix = Path(temporary) / "page"
        completed = subprocess.run(
            [renderer, "-gray", "-r", "36", str(path), str(prefix)],
            text=True,
            capture_output=True,
            check=False,
        )
        pages = sorted(prefix.parent.glob("page-*.pgm"))
        if completed.returncode != 0 or not pages:
            raise RuntimeError(f"visual hashing failed for {path}: {completed.stderr.strip()}")
        digest = hashlib.sha256()
        for page in pages:
            payload = page.read_bytes()
            digest.update(len(payload).to_bytes(8, "big"))
            digest.update(payload)
        return digest.hexdigest(), len(pages)


def main() -> None:
    rows = []
    source_hashes = {}
    visual_cache: dict[str, tuple[str, int]] = {}
    for canton, root in SOURCES.items():
        manifest = root / "manifest.jsonl"
        source_hashes[canton] = sha256(manifest)
        dataset = json.loads((root / "dataset.json").read_text(encoding="utf-8"))
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            pdf_sha256 = row["pdf_sha256"]
            if pdf_sha256 not in visual_cache:
                visual_cache[pdf_sha256] = visual_content_sha256(Path(row["pdf_path"]))
            visual_hash, page_count = visual_cache[pdf_sha256]
            rows.append({
                **row,
                "canton": canton,
                "source_family": f"swissgeol_{canton.lower().replace(' ', '_').replace('.', '')}",
                "source_dataset_version": dataset["dataset_version"],
                "human_reviewed": False,
                "reference_tier": "AUTHORITATIVE_STRUCTURED_SOURCE",
                "page_database_interval_agreement_verified": False,
                "evaluation_role": "source_disjoint_transfer_from_thurgau_development",
                "visual_content_sha256": visual_hash,
                "page_count": page_count,
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
    visual_group_sizes = {}
    for row in rows:
        key = row["visual_content_sha256"]
        visual_group_sizes[key] = visual_group_sizes.get(key, 0) + 1
    summary = {
        "dataset_version": "swissgeol_cross_canton_transfer_v001",
        "source": "four acquired non-Thurgau Swissgeol canton collections",
        "source_cantons": sorted(SOURCES),
        "source_count": len(SOURCES),
        "frozen_documents": len(rows),
        "frozen_intervals": sum(int(row["interval_count"]) for row in rows),
        "frozen_pages_record_weighted": sum(int(row["page_count"]) for row in rows),
        "unique_visual_document_count": len(visual_group_sizes),
        "duplicate_visual_record_count": len(rows) - len(visual_group_sizes),
        "maximum_records_per_visual_document": max(visual_group_sizes.values()),
        "visual_content_hash_method": "pdftoppm grayscale 36 DPI; length-delimited page bytes; SHA-256",
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
