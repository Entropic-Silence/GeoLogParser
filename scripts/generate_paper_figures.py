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
    save_image_multiboundary_surface,
    save_controlled_error_class_propagation,
    save_page_spatial_surface,
    save_source_disjoint_transfer,
    save_california_replication,
    save_california_cohort_forest,
    save_paper2_sequence_risk,
    save_paper3_spatial_support,
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
    parser.add_argument("--california-replication", type=Path, default=ROOT / "experiments/paper1/analysis/california_replication_statistics_v001.json")
    parser.add_argument("--paper2-ablation", type=Path, default=ROOT / "experiments/paper2/analysis/california_candidate_pool_ablation_v001.json")
    parser.add_argument("--paper2-risk", type=Path, default=ROOT / "experiments/paper2/analysis/california_document_risk_v001.json")
    parser.add_argument("--paper3-spatial", type=Path, default=ROOT / "experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json")
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
    save_source_disjoint_transfer(
        indexes["paper1"], ROOT, paper1 / "source_disjoint_transfer.png",
    )
    outputs.append(paper1 / "source_disjoint_transfer.png")
    save_california_replication(
        arguments.california_replication, paper1 / "california_replication.png",
    )
    outputs.append(paper1 / "california_replication.png")
    save_california_cohort_forest(
        arguments.california_replication, paper1 / "california_cohort_forest.png",
    )
    outputs.append(paper1 / "california_cohort_forest.png")
    paper2 = arguments.output_root / "paper2/generated/figures"
    save_method_schematic(paper2 / "method_schematic.png")
    outputs.append(paper2 / "method_schematic.png")
    save_california_replication(
        arguments.california_replication, paper2 / "california_replication.png",
    )
    outputs.append(paper2 / "california_replication.png")
    save_paper2_sequence_risk(
        arguments.paper2_ablation, arguments.paper2_risk,
        paper2 / "sequence_risk_frontier.png",
    )
    outputs.append(paper2 / "sequence_risk_frontier.png")
    paper3 = arguments.output_root / "paper3/generated/figures"
    save_padova_locations(arguments.location_manifest, paper3 / "padova_locations.png")
    outputs.append(paper3 / "padova_locations.png")
    save_error_propagation(indexes["paper3"], ROOT, paper3 / "synthetic_error_propagation.png")
    outputs.append(paper3 / "synthetic_error_propagation.png")
    save_source_field_propagation(indexes["paper3"], ROOT, paper3 / "coal602_source_proxy.png")
    outputs.append(paper3 / "coal602_source_proxy.png")
    save_image_boundary_surface(indexes["paper3"], ROOT, paper3 / "image_boundary_surface.png")
    outputs.append(paper3 / "image_boundary_surface.png")
    save_image_multiboundary_surface(indexes["paper3"], ROOT, paper3 / "image_multiboundary_surface.png")
    outputs.append(paper3 / "image_multiboundary_surface.png")
    save_controlled_error_class_propagation(indexes["paper3"], ROOT, paper3 / "controlled_error_classes.png")
    outputs.append(paper3 / "controlled_error_classes.png")
    save_page_spatial_surface(indexes["paper3"], ROOT, paper3 / "page_spatial_surface.png")
    outputs.append(paper3 / "page_spatial_surface.png")
    save_paper3_spatial_support(
        arguments.paper3_spatial, paper3 / "spatial_support_sensitivity.png",
    )
    outputs.append(paper3 / "spatial_support_sensitivity.png")
    manifest = {
        "scope": "auto-generated traceable figures; individual captions retain audit/protocol/design limits",
        "source_manifests": {
            "degradation": {"path": str(arguments.degradation_manifest), "sha256": digest(arguments.degradation_manifest)},
            "locations": {"path": str(arguments.location_manifest), "sha256": digest(arguments.location_manifest)},
            "california_replication": {"path": str(arguments.california_replication), "sha256": digest(arguments.california_replication)},
            "paper2_candidate_pool_ablation": {"path": str(arguments.paper2_ablation), "sha256": digest(arguments.paper2_ablation)},
            "paper2_document_risk": {"path": str(arguments.paper2_risk), "sha256": digest(arguments.paper2_risk)},
            "paper3_spatial_sensitivity": {"path": str(arguments.paper3_spatial), "sha256": digest(arguments.paper3_spatial)},
        },
        "outputs": [{"path": str(path.relative_to(arguments.output_root)), "sha256": digest(path)} for path in outputs],
    }
    destination = arguments.output_root / "figure_manifest.json"
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
