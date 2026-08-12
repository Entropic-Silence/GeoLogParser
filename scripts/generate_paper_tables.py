#!/usr/bin/env python3
"""Generate paper-facing Markdown tables from immutable indexed metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.paper_artifacts import paper1_table, paper2_table, paper3_table
from geologparser.result_index import verify_index


ROOT = Path(__file__).resolve().parents[1]


def load_index(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "papers")
    arguments = parser.parse_args()
    for paper, generator in (("paper1", paper1_table), ("paper2", paper2_table), ("paper3", paper3_table)):
        index = ROOT / "experiments" / paper / "result_index.jsonl"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.touch(exist_ok=True)
        errors = verify_index(index, ROOT)
        if errors:
            raise SystemExit("\n".join(errors))
        destination = arguments.output_root / paper / "generated" / "current_results.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(generator(load_index(index), ROOT), encoding="utf-8")
        print(destination)
if __name__ == "__main__":
    main()
