#!/usr/bin/env python3
"""Build local image manifests for BGS and quarantine VLM audits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bgs-manifest", type=Path)
    parser.add_argument("--panel-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=150)
    arguments = parser.parse_args()
    if bool(arguments.bgs_manifest) == bool(arguments.panel_manifest):
        raise ValueError("provide exactly one of --bgs-manifest or --panel-manifest")
    rows = []
    arguments.image_root.mkdir(parents=True, exist_ok=True)
    if arguments.panel_manifest:
        for line in arguments.panel_manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            image = Path(item["rendered_path"])
            if not image.is_file():
                raise FileNotFoundError(image)
            rows.append(item | {"image_path": str(image)})
    else:
        for line in arguments.bgs_manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            pdf = Path(item["local_path"])
            record_id = str(item["source_record_id"])
            with pymupdf.open(pdf) as document:
                page = document[0]
                pixmap = page.get_pixmap(dpi=arguments.dpi, alpha=False)
                image = arguments.image_root / f"bgs_{record_id}_p001.png"
                pixmap.save(image)
            rows.append({
                "source_record_id": record_id,
                "image_path": str(image),
                "rendered_path": str(image),
                "render_dpi": arguments.dpi,
                "project_id": f"BGS_RECORD_{record_id}",
                "template_id": "BGS_UNKNOWN",
                "source_pdf_path": str(pdf),
                "source_pdf_sha256": item["sha256"],
            })
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(arguments.output)


if __name__ == "__main__":
    main()
