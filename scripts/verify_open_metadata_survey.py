#!/usr/bin/env python3
"""Verify a frozen open-metadata survey artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.datasets.source_survey import verify_open_metadata_survey


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("survey_root", type=Path)
    arguments = parser.parse_args()
    result = verify_open_metadata_survey(arguments.survey_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
