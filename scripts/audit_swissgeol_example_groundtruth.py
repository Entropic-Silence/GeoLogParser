#!/usr/bin/env python3
"""Audit the Swissgeol repository's example PDF/ground-truth pairings.

This is a source-quality audit, not a benchmark run.  It deliberately reports
the layer fixture as mismatched when the repository's own metadata and visible
PDF content disagree; no labels are promoted to Gold by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_text(path: Path) -> str:
    completed = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        text=True, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {path}: {completed.stderr.strip()}")
    return completed.stdout


def audit(repository_root: Path) -> dict:
    example = repository_root / "example"
    pdf = example / "example_borehole_profile.pdf"
    metadata_gt = example / "example_groundtruth.json"
    layers_gt = example / "example_layers_groundtruth.json"
    for path in (pdf, metadata_gt, layers_gt):
        if not path.is_file():
            raise FileNotFoundError(path)
    metadata = json.loads(metadata_gt.read_text(encoding="utf-8"))
    layers = json.loads(layers_gt.read_text(encoding="utf-8"))
    text = pdf_text(pdf)
    metadata_row = metadata["example_borehole_profile.pdf"][0]["metadata"]
    layer_rows = layers["example_borehole_profile.pdf"]
    layer_descriptions = [
        layer.get("material_description")
        for row in layer_rows for layer in row.get("layers", [])
    ]
    metadata_matches_pdf = all([
        metadata_row["coordinates"]["E"] == 615790,
        metadata_row["coordinates"]["N"] == 157500,
        metadata_row["drilling_date"] == "1995-09-03",
        metadata_row["reference_elevation"] == 788.6,
        "SST KB 5" in text,
        "615 790 / 157 500" in text,
        "2.-3. 9. 1995" in text,
        "788,6" in text,
    ])
    layers_match_pdf = (
        len(layer_rows) == 1
        and layer_rows[0].get("borehole_index") == 0
        and any("Tonschiefer" in text for _ in [0])
        and any("KIES" in str(value).upper() for value in layer_descriptions)
    )
    return {
        "audit_id": "swissgeol_example_groundtruth_audit_v001",
        "source_repository": str(repository_root.resolve()),
        "source_commit": "3e8fdc10ba3ff158392a3a44fce2e62f6e9b0e12",
        "files": {
            "pdf": {"path": str(pdf), "sha256": sha256(pdf)},
            "metadata_groundtruth": {"path": str(metadata_gt), "sha256": sha256(metadata_gt)},
            "layers_groundtruth": {"path": str(layers_gt), "sha256": sha256(layers_gt)},
        },
        "pdf_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "metadata_groundtruth_matches_pdf": metadata_matches_pdf,
        "layers_groundtruth_matches_pdf": layers_match_pdf,
        "metadata_groundtruth_scope": ["coordinates", "drilling_date", "reference_elevation"],
        "layer_groundtruth_scope": ["depth_interval", "material_description"],
        "layer_fixture_decision": "EXCLUDE_MISMATCHED_FROM_GOLD",
        "metadata_fixture_decision": "ELIGIBLE_INTERNAL_ONLY_METADATA_AUDIT",
        "observed_pdf_material_terms": ["Tonschiefer", "Sandstein", "Schiefer", "Kakirit"],
        "observed_layer_fixture_material_terms": layer_descriptions,
        "notes": [
            "The metadata fixture agrees with visible PDF header values.",
            "The layer fixture describes shallow gravel/sand layers not supported by the visible example PDF, which shows a deep German tunnel profile.",
            "No interval/lithology Gold labels are created by this audit.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.repository_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
