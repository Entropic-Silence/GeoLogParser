#!/usr/bin/env python3
"""Create isolated duplicate-annotation tracks from frozen auto proposals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.annotation_assignment import build_blinded_annotation_pack


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_annotation_root", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument(
        "--track", action="append", required=True, metavar="TRACK_ID=ANNOTATOR_ID",
        help="Repeat for each physically separate blinded reviewer track.",
    )
    arguments = parser.parse_args()
    tracks = {}
    for value in arguments.track:
        if "=" not in value:
            parser.error("--track must use TRACK_ID=ANNOTATOR_ID")
        track_id, annotator_id = value.split("=", 1)
        if track_id in tracks:
            parser.error(f"duplicate track ID: {track_id}")
        tracks[track_id] = annotator_id
    result = build_blinded_annotation_pack(
        arguments.source_annotation_root, arguments.output_root, tracks,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
