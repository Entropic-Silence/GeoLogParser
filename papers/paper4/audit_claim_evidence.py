#!/usr/bin/env python3
"""Audit the integrated manuscript's claim-to-evidence map.

This is intentionally a small, publication-facing gate: every C4 claim must
have a declared evidence tier and every listed artifact must exist locally.
The audit does not upgrade source-agreement or synthetic evidence to Gold.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "papers/paper4/claim_evidence_map.md"
OUT = ROOT / "papers/paper4/claim_evidence_audit.json"
EXPECTED = {f"C4-{i:02d}" for i in range(1, 15)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    text = MAP.read_text(encoding="utf-8")
    rows = {}
    for line in text.splitlines():
        if not line.startswith("| C4-"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5:
            continue
        claim_id, claim, evidence, tier, artifacts = cells
        paths = [item.strip().strip("`") for item in artifacts.split(";")]
        rows[claim_id] = {
            "claim": claim,
            "evidence": evidence,
            "tier": tier,
            "artifacts": paths,
        }
    errors: list[str] = []
    missing_ids = sorted(EXPECTED - set(rows))
    extra_ids = sorted(set(rows) - EXPECTED)
    if missing_ids:
        errors.append(f"missing claim IDs: {', '.join(missing_ids)}")
    if extra_ids:
        errors.append(f"unexpected claim IDs: {', '.join(extra_ids)}")
    artifacts = {}
    for claim_id, row in rows.items():
        if "Source-agreement" in row["tier"] and "Gold" in row["tier"]:
            errors.append(f"{claim_id}: source-agreement evidence labelled Gold")
        if "synthetic" in row["tier"].lower() and "human" in row["tier"].lower():
            errors.append(f"{claim_id}: synthetic evidence labelled human")
        for raw_path in row["artifacts"]:
            if raw_path in {"recomputation script", "same as C4-10"}:
                continue
            path = ROOT / raw_path
            if not path.is_file():
                errors.append(f"{claim_id}: missing artifact {raw_path}")
            else:
                artifacts[raw_path] = digest(path)
    report = {
        "audit_version": "paper4_claim_evidence_v001",
        "claim_count": len(rows),
        "expected_claim_count": len(EXPECTED),
        "artifacts": artifacts,
        "errors": errors,
        "passed": not errors and set(rows) == EXPECTED,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        raise SystemExit("\n".join(errors))


if __name__ == "__main__":
    main()
