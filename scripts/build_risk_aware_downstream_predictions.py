#!/usr/bin/env python3
"""Create a downstream prediction run with document-level risk abstention.

Acceptance decisions come from the frozen Paper II risk router artifact.  A
rejected document is retained in the run with an empty accepted interval list,
which lets the downstream model quantify the cost of abstention instead of
silently treating rejected values as correct.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction-run", type=Path, required=True)
    parser.add_argument("--risk-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    upstream = {
        row["record_id"]: row
        for row in (json.loads(line) for line in (args.prediction_run / "predictions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    }
    risk = json.loads(args.risk_report.read_text(encoding="utf-8"))["heldout"]
    accepted = {row["record_id"]: bool(row["accepted"]) for row in risk["diagnostics"]}
    if set(upstream) != set(accepted):
        raise ValueError("risk decisions and upstream prediction records must match exactly")
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    for record_id, row in upstream.items():
        keep = accepted[record_id]
        rows.append({
            **row,
            "risk_acceptance": keep,
            "risk_decision_source": str(args.risk_report),
            "risk_accepted_intervals": row.get("final_intervals", []) if keep else [],
            "risk_abstained_intervals": [] if keep else row.get("final_intervals", []),
            "risk_aware_final_intervals": row.get("final_intervals", []) if keep else [],
        })
    (args.output / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    report = {
        "experiment_id": "P3_SWISSGEOL_RISK_AWARE_DOWNSTREAM_INPUT_001",
        "status": "completed_reference_blind_risk_projection",
        "upstream_prediction_run": str(args.prediction_run),
        "upstream_prediction_sha256": sha256(args.prediction_run / "predictions.jsonl"),
        "risk_report": str(args.risk_report),
        "risk_report_sha256": sha256(args.risk_report),
        "document_count": len(rows),
        "accepted_document_count": sum(accepted.values()),
        "coverage": sum(accepted.values()) / len(rows) if rows else 0.0,
        "decision_rule": "retain final intervals only when frozen document risk probability meets the preregistered threshold; otherwise abstain",
        "reference_blinding": "no interval references loaded while projecting risk decisions",
    }
    (args.output / "run.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
