#!/usr/bin/env python3
"""Render panel crops from a JSONL panel manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.annotation import PanelSpec, render_panel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    arguments = parser.parse_args()
    records = []
    for line in arguments.manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        item["normalized_bbox"] = tuple(item["normalized_bbox"])
        spec = PanelSpec(**item)
        output = arguments.output_root / "images" / f"{spec.panel_id}.png"
        records.append(render_panel(spec, output, arguments.dpi))
    output_manifest = arguments.output_root / "panel_manifest.jsonl"
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    print(output_manifest)


if __name__ == "__main__":
    main()
