#!/usr/bin/env python3
"""Generate a versioned synthetic borehole-log dataset with known labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.synthetic import generate_synthetic_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--count", type=int, default=32)
    parser.add_argument("--seed", type=int, default=20260813)
    parser.add_argument("--templates", type=int, default=8)
    parser.add_argument("--dpi", type=int, default=180)
    args = parser.parse_args()
    print(json.dumps(generate_synthetic_dataset(args.output_root, count=args.count, seed=args.seed, templates=args.templates, dpi=args.dpi), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
