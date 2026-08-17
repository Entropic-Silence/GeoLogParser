"""Bind displayed manuscript numbers to versioned JSON evidence."""

from __future__ import annotations

import json
from pathlib import Path
import re


def json_pointer(document: object, pointer: str) -> object:
    current = document
    for raw in pointer.removeprefix("/").split("/") if pointer else []:
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def as_number(value: str) -> int | float:
    return float(value) if any(character in value.lower() for character in (".", "e")) else int(value)


def audit(config_path: Path, root: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    observations = []
    errors = []
    for check in config["checks"]:
        manuscript_path = root / check["manuscript"]
        source_path = root / check["source"]
        manuscript = manuscript_path.read_text(encoding="utf-8")
        source = json.loads(source_path.read_text(encoding="utf-8"))
        matches = list(re.finditer(check["pattern"], manuscript, flags=re.DOTALL))
        if len(matches) != 1:
            errors.append(
                f"{check['id']}: pattern matched {len(matches)} times in {check['manuscript']}"
            )
            continue
        match = matches[0]
        for binding in check["bindings"]:
            observed = as_number(match.group(binding["group"]))
            expected = json_pointer(source, binding["pointer"])
            if "subtract_from" in binding:
                expected = binding["subtract_from"] - expected
            decimals = binding.get("decimals")
            if decimals is None:
                passed = observed == expected
            else:
                passed = round(float(expected), int(decimals)) == float(observed)
            observations.append({
                "check_id": check["id"],
                "group": binding["group"],
                "manuscript": check["manuscript"],
                "source": check["source"],
                "pointer": binding["pointer"],
                "observed": observed,
                "expected": expected,
                "display_decimals": decimals,
                "transform": (
                    f"{binding['subtract_from']} - source" if "subtract_from" in binding else None
                ),
                "passed": passed,
            })
            if not passed:
                errors.append(
                    f"{check['id']}/{binding['group']}: prose={observed!r}, "
                    f"source={expected!r}, decimals={decimals!r}"
                )
    return {
        "audit_version": config["audit_version"],
        "config": str(config_path.relative_to(root)),
        "observation_count": len(observations),
        "passed": not errors,
        "errors": errors,
        "observations": observations,
    }
