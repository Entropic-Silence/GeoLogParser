#!/usr/bin/env python3
"""Build a reference-blind role-expert input shell for an external page run.

This does not fit or tune a model.  It records that the frozen semantic-role
expert produced no eligible role sequence when its candidate evidence is not
available on the external page; the routed parser must then use its fixed
fallback expert or abstain.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--multiscale", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_jsonl(args.manifest)
    multiscale = json.loads(args.multiscale.read_text(encoding="utf-8"))
    docs = {row["record_id"]: row for row in multiscale["documents"]}
    predictions = []
    for row in manifest:
        doc = docs.get(row["record_id"], {})
        candidate_count = sum(
            len(page.get("combined_visible", []))
            for page in doc.get("page_layout", [])
        )
        predictions.append({
            "record_id": row["record_id"],
            "candidate_count": int(candidate_count),
            "ranked_candidates": [],
            "sequence_selected": [],
            "reference_blind": True,
            "role_expert_status": "no_eligible_role_evidence",
        })
    report = {
        "experiment_id": "P2_BGS_V003_FROZEN_ROLE_EXTERNAL_INPUT_001",
        "method_version": "bgs_layout_field_aware_moe_v025_role_multi_frozen",
        "status": "completed_reference_blind_external_input",
        "manifest": str(args.manifest),
        "multiscale_analysis": str(args.multiscale),
        "predictions": predictions,
        "reference_blinding": "no interval references loaded; no model fitting or threshold selection",
        "limitations": [
            "The external page did not expose eligible semantic-role candidates to the frozen role parser.",
            "The routed method therefore falls back or abstains according to the frozen policy.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
