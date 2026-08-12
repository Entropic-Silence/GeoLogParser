from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.export import write_interval_csv
from geologparser.pipeline import run_minimal_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the minimal GeoLogParser baseline")
    parser.add_argument("input", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    parser.add_argument("--csv", dest="csv_path", type=Path)
    parser.add_argument("--text", dest="text_path", type=Path)
    parser.add_argument("--ocr-language", default="chi_sim+eng")
    args = parser.parse_args()

    regions, record = run_minimal_baseline(args.input, args.ocr_language)
    args.json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.csv_path:
        write_interval_csv(record, args.csv_path)
    if args.text_path:
        args.text_path.write_text("\n".join(region.text for region in regions) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

