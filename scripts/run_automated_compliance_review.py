#!/usr/bin/env python3
"""Run the conservative automated dataset-compliance gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from geologparser.datasets.compliance import review_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("datasets/data_registry.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset-root", action="append", default=[], metavar="ID=PATH")
    args = parser.parse_args()
    roots = {}
    for item in args.dataset_root:
        identifier, separator, path = item.partition("=")
        if not separator or not identifier or not path:
            raise ValueError("--dataset-root must use ID=PATH")
        roots[identifier] = Path(path)
    registry = yaml.safe_load(args.registry.read_text(encoding="utf-8"))
    result = review_registry(registry, dataset_roots=roots)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["decision_counts"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
