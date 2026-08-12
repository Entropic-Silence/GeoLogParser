"""Traceable file-manifest primitives."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class DatasetFile:
    dataset_id: str
    source_record_id: str
    source_url: str
    local_path: str
    sha256: str
    size_bytes: int
    media_type: str
    access_date: str
    license_id: str
    redistribution: str
    metadata: dict[str, Any]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_jsonl(records: Iterable[DatasetFile], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )

