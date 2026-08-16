#!/usr/bin/env python3
"""Add page lists required by the layout experiments to an existing JSONL manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def page_count(pdf: Path) -> int:
    completed = subprocess.run(["pdfinfo", str(pdf)], text=True, capture_output=True, check=True)
    for line in completed.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError(f"pdfinfo did not report page count for {pdf}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = []
    for row in load_jsonl(args.input):
        pages = page_count(Path(row["pdf_path"]))
        updated = dict(row)
        updated["evaluation_pages"] = list(range(1, pages + 1))
        if "intervals" not in updated and row.get("reference_path"):
            reference = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))
            updated["intervals"] = [
                {
                    "top_depth_m": float(item["top_depth_m"]),
                    "bottom_depth_m": float(item["bottom_depth_m"]),
                    "thickness_m": float(item["bottom_depth_m"] - item["top_depth_m"]),
                }
                for item in reference["stratigraphy"]["intervals"]
            ]
        updated["layout_manifest_source"] = str(args.input)
        rows.append(updated)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({"documents": len(rows), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
