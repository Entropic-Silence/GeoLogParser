"""Schema loading and optional standards-compliant validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_schema(version: str = "v001") -> dict[str, Any]:
    path = repository_root() / "schemas" / f"borehole_{version}.schema.json"
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def validate_record(record: Mapping[str, Any], version: str = "v001") -> None:
    try:
        from jsonschema import Draft202012Validator
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(
            "Schema validation requires jsonschema>=4.18; install geologparser[schema]."
        ) from exc
    validator = Draft202012Validator(load_schema(version))
    validator.validate(record)

