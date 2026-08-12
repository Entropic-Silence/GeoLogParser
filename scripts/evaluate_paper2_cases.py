#!/usr/bin/env python3
"""Evaluate a human-verified Paper II case file; never synthesizes missing GT."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.evaluation.paper2 import evaluate_paper2_cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--bins", type=int, default=10)
    arguments = parser.parse_args()
    cases = [json.loads(line) for line in arguments.cases.read_text(encoding="utf-8").splitlines() if line]
    metrics = evaluate_paper2_cases(cases, bins=arguments.bins)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(arguments.output)


if __name__ == "__main__":
    main()
