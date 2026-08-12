"""Small CSV projections; JSON remains the lossless canonical output."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping


def value(item: Any) -> Any:
    return item.get("value") if isinstance(item, Mapping) else item


def write_interval_csv(record: Mapping[str, Any], path: Path) -> None:
    fields = (
        "interval_id", "top_depth_m", "bottom_depth_m", "thickness_m",
        "stratum_code_raw", "stratum_code_normalized", "lithology_raw",
        "lithology_normalized", "description_raw", "description_normalized",
    )
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for interval in record.get("intervals", []):
            writer.writerow({name: value(interval.get(name)) for name in fields})

