#!/usr/bin/env python3
"""Measure record-linkage risk in the pseudonymized publication inputs.

The output contains aggregate counts only.  It never writes a mapping from a
public record key to a source identifier or coordinate.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
P3_MANIFEST = Path(
    "/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v003/"
    "gold_interval_manifest_heldout_v003.jsonl"
)


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def interval_signature(intervals: list[dict], *, feet: bool = False) -> tuple[tuple[float, float], ...]:
    factor = 0.3048 if feet else 1.0
    top_key = "top_depth_ft" if feet else "top_depth_m"
    bottom_key = "bottom_depth_ft" if feet else "bottom_depth_m"
    return tuple(
        (round(float(row[top_key]) * factor, 6), round(float(row[bottom_key]) * factor, 6))
        for row in intervals
    )


def paper2_linkage(public_path: Path) -> dict:
    public_rows = read_jsonl(public_path)
    source_rows = []
    for freeze in ("v004", "v005"):
        source_rows.extend(read_jsonl(ROOT / f"datasets/manifests/california_wcr_gold_{freeze}.jsonl"))
    public_signatures = [interval_signature(row["reference_intervals"]) for row in public_rows]
    source_counts = Counter(interval_signature(row["intervals"], feet=True) for row in source_rows)
    public_counts = Counter(public_signatures)
    match_counts = [source_counts[signature] for signature in public_signatures]
    return {
        "attack": "exact ordered reference-depth sequence lookup against the local official-transcription manifests",
        "public_record_count": len(public_rows),
        "source_candidate_count": len(source_rows),
        "records_with_at_least_one_exact_source_match": sum(count > 0 for count in match_counts),
        "records_with_unique_exact_source_match": sum(count == 1 for count in match_counts),
        "records_with_signature_unique_within_public_bundle": sum(public_counts[value] == 1 for value in public_signatures),
        "mapping_released": False,
    }


def distance_fingerprint(point: tuple[float, float], points: list[tuple[float, float]]) -> tuple[float, ...]:
    return tuple(sorted(round(math.dist(point, other), 5) for other in points))


def paper3_linkage(public_path: Path, manifest_path: Path) -> dict:
    public_rows = read_jsonl(public_path)
    manifest = read_jsonl(manifest_path)
    private_points = []
    for row in manifest:
        reference = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))
        borehole = reference["borehole"]
        private_points.append((float(borehole["x_coordinate"]), float(borehole["y_coordinate"])))
    public_points = [
        (float(row["x_relative_m"]), float(row["y_relative_m"]))
        for row in public_rows
    ]
    public_fingerprints = [distance_fingerprint(point, public_points) for point in public_points]
    private_counts = Counter(distance_fingerprint(point, private_points) for point in private_points)
    match_counts = [private_counts[fingerprint] for fingerprint in public_fingerprints]
    return {
        "attack": "rigid-transform-invariant pairwise-distance fingerprint lookup against the original point set",
        "public_record_count": len(public_rows),
        "source_candidate_count": len(private_points),
        "records_with_at_least_one_exact_distance_fingerprint_match": sum(count > 0 for count in match_counts),
        "records_with_unique_exact_distance_fingerprint_match": sum(count == 1 for count in match_counts),
        "distance_rounding_decimals": 5,
        "mapping_released": False,
    }


def markdown(payload: dict) -> str:
    p2 = payload["paper2_candidate_pool"]
    p3 = payload["paper3_spatial_input"]
    return "\n".join([
        "# Publication-input linkage risk",
        "",
        "These diagnostics test linkability; they are not anonymity certificates. No record mapping is released.",
        "",
        "| Input | Attack | Linked records | Unique links | Conclusion |",
        "|---|---|---:|---:|---|",
        f"| Paper II candidate pool | Exact ordered depth sequence | {p2['records_with_at_least_one_exact_source_match']}/{p2['public_record_count']} | {p2['records_with_unique_exact_source_match']}/{p2['public_record_count']} | Pseudonymized and linkable |",
        f"| Paper III spatial input | Pairwise-distance fingerprint | {p3['records_with_at_least_one_exact_distance_fingerprint_match']}/{p3['public_record_count']} | {p3['records_with_unique_exact_distance_fingerprint_match']}/{p3['public_record_count']} | Transformed but linkable |",
        "",
        "The release gate must therefore assess source rights, precise-location sensitivity, and linkage disclosure. Removing identifiers or an absolute coordinate origin does not establish non-reidentifiability.",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--paper2-input",
        type=Path,
        default=ROOT / "experiments/paper2/public/candidate_pool_v001.jsonl",
    )
    parser.add_argument(
        "--paper3-input",
        type=Path,
        default=ROOT / "experiments/paper3/public/spatial_input_v001.jsonl",
    )
    parser.add_argument("--paper3-manifest", type=Path, default=P3_MANIFEST)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "docs/generated/publication_linkage_risk.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "docs/publication_linkage_risk.md",
    )
    arguments = parser.parse_args()
    payload = {
        "analysis_version": "publication_linkage_risk_v001",
        "classification": "pseudonymized_or_transformed_not_anonymous",
        "paper2_candidate_pool": paper2_linkage(arguments.paper2_input),
        "paper3_spatial_input": paper3_linkage(arguments.paper3_input, arguments.paper3_manifest),
        "limitations": [
            "The Paper II attack searches the two released cohort manifests, not every possible external table.",
            "The Paper III attack assumes access to the same complete public point set.",
            "Successful aggregate linkage demonstrates risk; failed linkage would not prove anonymity.",
        ],
    }
    arguments.output_json.parent.mkdir(parents=True, exist_ok=True)
    arguments.output_md.parent.mkdir(parents=True, exist_ok=True)
    arguments.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    arguments.output_md.write_text(markdown(payload), encoding="utf-8")
    print(arguments.output_json)
    print(arguments.output_md)


if __name__ == "__main__":
    main()
