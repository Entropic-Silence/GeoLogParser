#!/usr/bin/env python3
"""Reject CRLF and non-UTF-8 drift in committed publication artifacts.

The publication package hashes generated JSON and Markdown byte-for-byte.  Git
attributes normalize checked-out text, but Python's text-mode writes would still
emit CRLF on Windows.  This guard runs after all generators in both CI jobs.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED = (
    "docs/generated/manuscript_metric_audit.json",
    "papers/claim_registry.json",
    "papers/package_manifest.json",
    "papers/paper1/generated/package/evidence_audit.json",
    "papers/paper2/generated/package/evidence_audit.json",
    "papers/paper3/generated/package/evidence_audit.json",
    "papers/paper4/metric_audit.json",
    "papers/paper4/claim_evidence_audit.json",
    "papers/paper4/figure_manifest.json",
    "papers/paper4/submission_gate.json",
    "publication_evidence/manifest.json",
)


def main() -> None:
    errors: list[str] = []
    for relative in GENERATED:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing generated artifact: {relative}")
            continue
        payload = path.read_bytes()
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            errors.append(f"non-UTF-8 artifact: {relative}: {error}")
            continue
        if b"\r" in payload:
            errors.append(f"CRLF/CR byte found: {relative}")
        if not text.endswith("\n"):
            errors.append(f"missing terminal LF: {relative}")
        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as error:
                errors.append(f"invalid JSON: {relative}: {error}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"UTF-8/LF generated artifacts verified: {len(GENERATED)}")


if __name__ == "__main__":
    main()
