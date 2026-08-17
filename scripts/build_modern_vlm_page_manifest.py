#!/usr/bin/env python3
"""Render declared evaluation pages into a source-neutral VLM page manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pymupdf


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--record-ids", type=Path)
    parser.add_argument("--split", type=Path)
    parser.add_argument("--partition", choices=("development", "test"), default="test")
    args = parser.parse_args()
    if args.dpi < 72:
        raise ValueError("dpi must be at least 72")
    selected: set[str] | None = None
    if args.record_ids:
        selected = {line.strip() for line in args.record_ids.read_text(encoding="utf-8").splitlines() if line.strip()}
    if args.split:
        split = json.loads(args.split.read_text(encoding="utf-8"))
        selected = {str(record_id) for record_id in split[args.partition]}
    args.image_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for source in load_jsonl(args.source_manifest):
        record_id = str(source["record_id"])
        if selected is not None and record_id not in selected:
            continue
        pdf = Path(str(source["pdf_path"]))
        if not pdf.is_file():
            raise FileNotFoundError(pdf)
        requested_pages = source.get("evaluation_pages")
        with pymupdf.open(pdf) as document:
            page_numbers = requested_pages or list(range(1, len(document) + 1))
            for page_number in page_numbers:
                page_index = int(page_number)
                if page_index < 1 or page_index > len(document):
                    raise ValueError(f"{record_id} declares unavailable page {page_index}")
                image = args.image_root / f"{record_id}_p{page_index:03d}.png"
                if not image.is_file():
                    document[page_index - 1].get_pixmap(dpi=args.dpi, alpha=False).save(image)
                rows.append({
                    "record_id": record_id,
                    "image_path": str(image),
                    "rendered_path": str(image),
                    "rendered_sha256": sha256(image),
                    "render_dpi": args.dpi,
                    "page_index": page_index,
                    "source_pdf_path": str(pdf),
                    "source_pdf_sha256": source.get("pdf_sha256"),
                    "source_group": source.get("source_title") or source.get("canton") or source.get("county"),
                    "template_id": source.get("template_id") or args.source_manifest.stem,
                })
    if not rows:
        raise ValueError("selected source manifest produced no pages")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
