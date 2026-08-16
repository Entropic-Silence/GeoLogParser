#!/usr/bin/env python3
"""Render a manifest of paired PDFs and serialize reference-blind OCR regions.

This utility is intentionally source-agnostic.  It produces the page images and
Tesseract TSV regions required by the layout/routing experiments without
loading interval references during OCR generation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def tsv_regions(image: Path, language: str, psm: int) -> list[dict]:
    completed = subprocess.run(
        ["tesseract", str(image), "stdout", "-l", language, "--psm", str(psm), "tsv"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"tesseract failed for {image}: {completed.stderr.strip()}")
    lines = completed.stdout.splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    rows: list[dict] = []
    for raw in lines[1:]:
        values = raw.split("\t")
        if len(values) != len(header):
            continue
        row = dict(zip(header, values))
        text = row.get("text", "").strip()
        if not text:
            continue
        try:
            confidence = max(0.0, min(1.0, float(row.get("conf", "-1")) / 100.0))
            x1 = float(row["left"])
            y1 = float(row["top"])
            x2 = x1 + float(row["width"])
            y2 = y1 + float(row["height"])
        except (KeyError, ValueError):
            continue
        rows.append({
            "text": text,
            "confidence": confidence,
            "bbox": [x1, y1, x2, y2],
            "level": int(row.get("level", 5) or 5),
        })
    return rows


def natural_page_key(path: Path) -> tuple[int, str]:
    stem = path.stem
    try:
        return int(stem.rsplit("-", 1)[1]), stem
    except (IndexError, ValueError):
        return 0, stem


def render_pdf(pdf: Path, output: Path, dpi: int) -> list[Path]:
    prefix = output / "rendered"
    completed = subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)],
        text=True,
        capture_output=True,
        check=False,
    )
    pages = sorted(output.glob("rendered-*.png"), key=natural_page_key)
    if completed.returncode != 0 or not pages:
        raise RuntimeError(f"pdftoppm failed for {pdf}: {completed.stderr.strip()}")
    return pages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=250)
    parser.add_argument("--language", default="eng")
    parser.add_argument("--psm", type=int, default=3)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    rows = load_jsonl(args.manifest)
    records: list[dict] = []
    for source in rows:
        record_id = str(source["record_id"])
        record_root = args.output / "_render" / record_id
        record_root.mkdir(parents=True, exist_ok=True)
        pages = render_pdf(Path(source["pdf_path"]), record_root, args.dpi)
        page_ids: list[int] = []
        for page_number, rendered in enumerate(pages, 1):
            destination = args.output / f"{record_id}_page-{page_number}.png"
            shutil.copyfile(rendered, destination)
            regions = tsv_regions(destination, args.language, args.psm)
            region_path = args.output / f"{record_id}_page-{page_number}_regions.jsonl"
            region_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in regions),
                encoding="utf-8",
            )
            page_ids.append(page_number)
        records.append({
            "record_id": record_id,
            "pdf_sha256": source.get("pdf_sha256") or sha256(Path(source["pdf_path"])),
            "page_count": len(page_ids),
            "region_count": sum(
                len(load_jsonl(args.output / f"{record_id}_page-{page}_regions.jsonl"))
                for page in page_ids
            ),
        })
    (args.output / "source_run_manifest.json").write_text(
        json.dumps({
            "manifest": str(args.manifest),
            "manifest_sha256": sha256(args.manifest),
            "dpi": args.dpi,
            "language": args.language,
            "psm": args.psm,
            "record_count": len(records),
            "records": records,
            "wall_time_seconds": time.perf_counter() - started,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    shutil.rmtree(args.output / "_render")
    print(json.dumps({"record_count": len(records), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()

