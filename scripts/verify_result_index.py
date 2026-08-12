#!/usr/bin/env python3
"""Verify hashes in a version-controlled immutable experiment index."""

from __future__ import annotations

import argparse
from pathlib import Path

from geologparser.result_index import verify_index


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "index", type=Path, nargs="?",
        default=ROOT / "experiments" / "paper1" / "result_index.jsonl",
    )
    arguments = parser.parse_args()
    errors = verify_index(arguments.index, ROOT)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"verified={arguments.index}")


if __name__ == "__main__":
    main()
