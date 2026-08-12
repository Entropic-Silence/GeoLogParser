#!/usr/bin/env python3
"""Generate traceable publication-readiness JSON/Markdown from live evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from geologparser.readiness import project_readiness, readiness_markdown


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANNOTATIONS = Path(
    "/data/GeoLogParser/artifacts/annotation/unipd_levee_geotech_b6_v001/annotations"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation-root", type=Path, action="append", default=[])
    parser.add_argument("--output-json", type=Path, default=ROOT / "docs/generated/publication_readiness.json")
    parser.add_argument("--output-markdown", type=Path, default=ROOT / "docs/generated/publication_readiness.md")
    arguments = parser.parse_args()
    report = project_readiness(
        arguments.annotation_root or [DEFAULT_ANNOTATIONS],
        {paper: ROOT / "experiments" / paper / "result_index.jsonl" for paper in ("paper1", "paper2", "paper3")},
    )
    report["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    arguments.output_json.parent.mkdir(parents=True, exist_ok=True)
    arguments.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    arguments.output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    arguments.output_markdown.write_text(readiness_markdown(report), encoding="utf-8")
    print(arguments.output_json)
    print(arguments.output_markdown)


if __name__ == "__main__":
    main()
