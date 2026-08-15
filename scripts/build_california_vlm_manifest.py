#!/usr/bin/env python3
"""Render first pages of a California Gold freeze for a VLM benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--record-ids", type=Path)
    parser.add_argument("--split", type=Path)
    parser.add_argument("--partition", choices=("development", "test"), default="test")
    args = parser.parse_args()
    args.image_root.mkdir(parents=True, exist_ok=True)
    selected = None
    if args.record_ids:
        selected = {
            line.strip() for line in args.record_ids.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    if args.split:
        split = json.loads(args.split.read_text(encoding="utf-8"))
        selected = set(split[args.partition])
    rows = []
    for line in args.manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if selected is not None and item["record_id"] not in selected:
            continue
        pdf = Path(item["pdf_path"])
        with pymupdf.open(pdf) as document:
            for page_index in range(len(document)):
                page = document[page_index]
                image = args.image_root / f'{item["record_id"]}_p{page_index + 1:03d}.png'
                if not image.exists():
                    page.get_pixmap(dpi=args.dpi, alpha=False).save(image)
                rows.append({
                    "source_record_id": item["record_id"],
                    "record_id": item["record_id"],
                    "image_path": str(image),
                    "rendered_path": str(image),
                    "render_dpi": args.dpi,
                    "county": item.get("county"),
                    "project_id": item.get("record_id"),
                    "template_id": "CALIFORNIA_WCR_V001",
                    "source_pdf_path": str(pdf),
                    "source_pdf_sha256": item["pdf_sha256"],
                    "page_index": page_index + 1,
                })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
