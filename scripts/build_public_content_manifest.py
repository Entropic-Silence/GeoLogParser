#!/usr/bin/env python3
"""Build a page-level content manifest from frozen acquisition evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from geologparser.datasets.content_manifest import build_content_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--output-directory", type=Path)
    arguments = parser.parse_args()
    config = yaml.safe_load(arguments.config.read_text(encoding="utf-8"))
    result = build_content_manifest(
        arguments.dataset_root, config, output_directory=arguments.output_directory,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

