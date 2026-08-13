#!/usr/bin/env python3
"""Freeze a reproducible, metadata-only public dataset survey."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from geologparser.datasets.source_survey import run_open_metadata_survey


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--timeout", type=float, default=30.0)
    arguments = parser.parse_args()
    config = yaml.safe_load(arguments.config.read_text(encoding="utf-8"))
    result = run_open_metadata_survey(config, arguments.destination, timeout=arguments.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
