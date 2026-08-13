#!/usr/bin/env python3
"""Build a deterministic first-page BGS metadata robustness set.

The source documents are real BGS scans.  The derived image perturbations are
synthetic and must not be described as naturally occurring document damage.
Only first-page fields paired with official catalogue metadata are in scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path

from geologparser.preprocessing import DegradationConfig, degrade_image


PROFILES = {
    "clean": DegradationConfig(),
    "resolution_050": DegradationConfig(resolution_scale=0.50),
    "blur_20": DegradationConfig(blur_radius=2.0),
    "noise_16": DegradationConfig(gaussian_noise_std=16.0),
    "skew_30": DegradationConfig(rotation_degrees=3.0),
    "jpeg_30": DegradationConfig(jpeg_quality=30),
    "contrast_040": DegradationConfig(contrast=0.40),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_first_page(pdf: Path, destination: Path, dpi: int) -> None:
    renderer = shutil.which("pdftoppm")
    if renderer is None:
        raise RuntimeError("pdftoppm is required to render the BGS source PDFs")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="geologparser-bgs-render-") as temporary:
        prefix = Path(temporary) / "page"
        completed = subprocess.run(
            [
                renderer, "-f", "1", "-l", "1", "-singlefile", "-png",
                "-r", str(dpi), str(pdf), str(prefix),
            ],
            text=True, capture_output=True, check=False,
        )
        rendered = prefix.with_suffix(".png")
        if completed.returncode != 0 or not rendered.is_file():
            raise RuntimeError(
                f"pdftoppm failed for {pdf}: {completed.stderr.strip()}"
            )
        shutil.move(rendered, destination)


def build_dataset(
    source_manifest: Path,
    output_root: Path,
    *,
    render_dpi: int = 300,
    base_seed: int = 20260813,
) -> dict:
    if output_root.exists():
        raise FileExistsError(f"robustness dataset already exists: {output_root}")
    output_root.mkdir(parents=True)
    source_rows = [
        json.loads(line) for line in source_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = []
    for document_index, source_row in enumerate(source_rows):
        record_id = str(source_row["source_record_id"])
        source_pdf = Path(source_row["local_path"])
        if sha256(source_pdf) != source_row["sha256"]:
            raise ValueError(f"source PDF hash mismatch: {source_pdf}")
        rendered = output_root / "rendered_sources" / f"bgs_{record_id}_page_001.png"
        render_first_page(source_pdf, rendered, render_dpi)
        rendered_hash = sha256(rendered)
        for profile_index, (profile, base_config) in enumerate(PROFILES.items()):
            config = DegradationConfig(**{
                **asdict(base_config),
                "seed": base_seed + document_index * 1000 + profile_index,
            })
            suffix = ".jpg" if config.jpeg_quality is not None else ".png"
            destination = output_root / "images" / profile / f"bgs_{record_id}_page_001{suffix}"
            degradation = degrade_image(rendered, destination, config)
            rows.append({
                "item_id": f"bgs_{record_id}_page_001__{profile}",
                "dataset_id": "bgs_metadata_robustness_v001",
                "source_record_id": record_id,
                "source_pdf_path": str(source_pdf),
                "source_pdf_sha256": source_row["sha256"],
                "source_page": 1,
                "render_dpi": render_dpi,
                "rendered_source_path": str(rendered),
                "rendered_source_sha256": rendered_hash,
                "profile": profile,
                "derived_image_path": str(destination),
                "derived_image_sha256": degradation["destination_sha256"],
                "degradation_parameters": degradation["parameters"],
                "operation_order": degradation["operation_order"],
                "reference_ground_truth_tier": "AUTHORITATIVE_METADATA",
                "reference": {
                    "borehole_id": source_row["metadata"].get("REFERENCE"),
                    "x_coordinate": source_row["metadata"].get("EASTING"),
                    "y_coordinate": source_row["metadata"].get("NORTHING"),
                },
                "interval_ground_truth_available": False,
            })
    manifest = output_root / "degradation_manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "dataset_id": "bgs_metadata_robustness_v001",
        "source_type": "real BGS scans with synthetic controlled degradations",
        "source_document_count": len(source_rows),
        "source_page_count": len(source_rows),
        "profile_count": len(PROFILES),
        "profiles": list(PROFILES),
        "derived_image_count": len(rows),
        "render_dpi": render_dpi,
        "base_seed": base_seed,
        "evaluated_reference_fields": ["borehole_id", "x_coordinate", "y_coordinate"],
        "excluded_reference_fields": ["final_depth_m", "intervals", "lithology"],
        "source_manifest_path": str(source_manifest.resolve()),
        "source_manifest_sha256": sha256(source_manifest),
        "degradation_manifest_sha256": sha256(manifest),
        "boundary": (
            "Perturbations are controlled synthetic transformations of real first-page scans; "
            "they are not observations of naturally degraded documents."
        ),
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-manifest", type=Path,
        default=Path("/data/GeoLogParser/datasets/public/bgs_authoritative_metadata_v001/metadata/manifest.jsonl"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("/data/GeoLogParser/datasets/public/bgs_metadata_robustness_v001"),
    )
    parser.add_argument("--render-dpi", type=int, default=300)
    parser.add_argument("--base-seed", type=int, default=20260813)
    arguments = parser.parse_args()
    summary = build_dataset(
        arguments.source_manifest, arguments.output_root,
        render_dpi=arguments.render_dpi, base_seed=arguments.base_seed,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
