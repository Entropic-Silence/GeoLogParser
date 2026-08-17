#!/usr/bin/env python3
"""Bind manuscript headline numbers to immutable JSON metrics.

Evidence tags prove that a claim names an artifact; this audit additionally
checks that selected numbers printed in prose equal the artifact values at the
declared display precision.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.manuscript_metrics import audit


ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path,
        default=ROOT / "papers/manuscript_metric_bindings.json",
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "docs/generated/manuscript_metric_audit.json",
    )
    arguments = parser.parse_args()
    report = audit(arguments.config.resolve(), ROOT)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report["errors"]:
        raise SystemExit("\n".join(report["errors"]))
    print(arguments.output)


if __name__ == "__main__":
    main()
