#!/usr/bin/env python3
"""Generate paper figures from immutable manifests and indexed results."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geologparser.paper_figures import (
    save_audit_coverage, save_authoritative_interval_pilot, save_degradation_profiles,
    save_error_propagation, save_method_schematic, save_padova_locations,
    save_source_field_propagation, save_image_boundary_surface,
)
from geologparser.result_index import verify_index


ROOT = Path(__file__).resolve().parents[1]


def read_index(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "papers")
    parser.add_argument("--degradation-manifest", type=Path, default=Path("/data/GeoLogParser/artifacts/robustness/unipd_degradation_v001/degradation_manifest.jsonl"))
    parser.add_argument("--location-manifest", type=Path, default=Path("/data/GeoLogParser/datasets/public/unipd_levee_geotech_v001/metadata/location_v001/borehole_locations.jsonl"))
    arguments = parser.parse_args()
    indexes = {}
    for paper in ("paper1", "paper2", "paper3"):
        path = ROOT / "experiments" / paper / "result_index.jsonl"
        errors = verify_index(path, ROOT)
        if errors:
            raise SystemExit("\n".join(errors))
        indexes[paper] = read_index(path)
    outputs = []
    paper1 = arguments.output_root / "paper1/generated/figures"
    save_audit_coverage(indexes["paper1"], ROOT, paper1 / "audit_coverage.png")
    outputs.append(paper1 / "audit_coverage.png")
    save_degradation_profiles(arguments.degradation_manifest, paper1 / "degradation_inputs.png")
    outputs.append(paper1 / "degradation_inputs.png")
    save_authoritative_interval_pilot(
        indexes["paper1"], ROOT, paper1 / "authoritative_interval_pilot.png",
    )
    outputs.append(paper1 / "authoritative_interval_pilot.png")
    paper2 = arguments.output_root / "paper2/generated/figures"
    save_method_schematic(paper2 / "method_schematic.png")
    outputs.append(paper2 / "method_schematic.png")
    paper3 = arguments.output_root / "paper3/generated/figures"
    save_padova_locations(arguments.location_manifest, paper3 / "padova_locations.png")
    outputs.append(paper3 / "padova_locations.png")
    save_error_propagation(indexes["paper3"], ROOT, paper3 / "synthetic_error_propagation.png")
    outputs.append(paper3 / "synthetic_error_propagation.png")
    save_source_field_propagation(indexes["paper3"], ROOT, paper3 / "coal602_source_proxy.png")
    outputs.append(paper3 / "coal602_source_proxy.png")
    save_image_boundary_surface(indexes["paper3"], ROOT, paper3 / "image_boundary_surface.png")
    outputs.append(paper3 / "image_boundary_surface.png")
    manifest = {
        "scope": "auto-generated traceable figures; individual captions retain audit/protocol/design limits",
        "source_manifests": {
            "degradation": {"path": str(arguments.degradation_manifest), "sha256": digest(arguments.degradation_manifest)},
            "locations": {"path": str(arguments.location_manifest), "sha256": digest(arguments.location_manifest)},
        },
        "outputs": [{"path": str(path.relative_to(arguments.output_root)), "sha256": digest(path)} for path in outputs],
    }
    destination = arguments.output_root / "figure_manifest.json"
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
