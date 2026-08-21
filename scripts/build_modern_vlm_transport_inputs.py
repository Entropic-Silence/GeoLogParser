#!/usr/bin/env python3
"""Materialise page manifests for the fixed modern-VLM transport panel.

The source runs already contain the frozen rendered page paths used by the
Qwen3.8 reference evaluation.  This utility exposes only those paths and page
metadata to the additional model runners; it never reads predictions or Gold
intervals when constructing an input manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build(source_manifest: Path, source_page_run: Path, output: Path) -> None:
    pages = load_jsonl(source_page_run / "page_predictions.jsonl")
    if not pages:
        raise ValueError(f"no pages found in {source_page_run}")
    rows: list[dict[str, Any]] = []
    for page in pages:
        image_path = Path(str(page["image_path"]))
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        rows.append({
            "record_id": str(page["record_id"]),
            "page_index": page.get("page_index"),
            "image_path": str(image_path),
            "render_dpi": 200,
            "image_sha256": sha256(image_path),
        })
    source_ids = {str(row["record_id"]) for row in load_jsonl(source_manifest)}
    if not {row["record_id"] for row in rows} <= source_ids:
        raise ValueError("page source run contains a record outside the source manifest")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(output),
        "page_count": len(rows),
        "document_count": len({row["record_id"] for row in rows}),
        "source_manifest_sha256": sha256(source_manifest),
        "source_page_run": str(source_page_run),
    }, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-page-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source_manifest, args.source_page_run, args.output)


if __name__ == "__main__":
    main()
