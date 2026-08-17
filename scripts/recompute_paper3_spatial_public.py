#!/usr/bin/env python3
"""Recompute the main Paper III diagnostics from transformed public inputs."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from analyze_paper3_spatial_sensitivity import compare, loocv, support_diagnostics, volume_jackknife


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        angle = math.radians(17.0)
        cosine, sine = math.cos(angle), math.sin(angle)
        # The release stays rotated.  Inverting the documented rotation in
        # memory restores the frozen grid orientation without restoring any
        # absolute easting/northing origin.
        x = cosine * row["x_relative_m"] + sine * row["y_relative_m"]
        y = -sine * row["x_relative_m"] + cosine * row["y_relative_m"]
        records.append({
            "record_id": row["record_key"],
            "x": x,
            "y": y,
            "collar": row["collar_relative_m"],
            "reference": row["reference"],
            "raw": row["raw"],
            "reread": row["reread"],
            "risk": row["risk"],
            "risk_acceptance": row["risk_acceptance"],
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "experiments/paper3/public/spatial_input_v001.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper3/public/spatial_recomputed_v001.json")
    args = parser.parse_args()
    records = load(args.input)
    accepted = [record for record in records if record["risk_acceptance"]]
    variants = ["raw", "reread", "risk"]
    payload = {
        "analysis_version": "paper3_spatial_public_recomputation_v001",
        "document_count": len(records),
        "risk_accepted_document_count": len(accepted),
        "full_support_comparison": compare(records, variants, 2, None, 25),
        "matched_subset_comparison": compare(accepted, variants, 2, None, 25),
        "first_boundary_support": {variant: support_diagnostics(records, variant, 0, 25) for variant in variants},
        "default_leave_one_borehole_out": loocv(records, ["reference", *variants], 2, None),
        "volume_jackknife": {
            "full_support": volume_jackknife(records, variants, 2, None, 25),
            "matched_accepted_subset": volume_jackknife(accepted, variants, 2, None, 25),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
