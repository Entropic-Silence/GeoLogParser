"""Versioned page- and group-disjoint dataset splitting."""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from typing import Any, Mapping, Sequence


def stable_manifest_hash(records: Sequence[Mapping[str, Any]]) -> str:
    payload = "\n".join(json.dumps(dict(record), ensure_ascii=False, sort_keys=True) for record in records)
    return hashlib.sha256((payload + ("\n" if records else "")).encode("utf-8")).hexdigest()


def assign_split(
    records: Sequence[Mapping[str, Any]],
    group_key: str | None,
    ratios: Mapping[str, float] | None = None,
    seed: int = 42,
) -> dict[str, list[dict[str, Any]]]:
    ratios = ratios or {"train": 0.7, "validation": 0.1, "test": 0.2}
    if not ratios or any(value < 0 for value in ratios.values()) or abs(sum(ratios.values()) - 1) > 1e-9:
        raise ValueError("split ratios must be non-negative and sum to 1")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, record in enumerate(records):
        group = str(record.get(group_key)) if group_key else f"__page_{index}"
        if group_key and (group_key not in record or record.get(group_key) in (None, "")):
            raise ValueError(f"record is missing required split group: {group_key}")
        groups[group].append(dict(record))
    names = list(ratios)
    targets = {name: len(records) * ratios[name] for name in names}
    result = {name: [] for name in names}
    counts = {name: 0 for name in names}
    group_items = list(groups.items())
    random.Random(seed).shuffle(group_items)
    # Largest groups first after seeded tie shuffle limits size imbalance.
    group_items.sort(key=lambda item: len(item[1]), reverse=True)
    for _, items in group_items:
        destination = min(names, key=lambda name: (counts[name] - targets[name], counts[name]))
        result[destination].extend(items)
        counts[destination] += len(items)
    return result


def assert_group_disjoint(splits: Mapping[str, Sequence[Mapping[str, Any]]], group_key: str) -> None:
    seen: dict[str, str] = {}
    for split_name, records in splits.items():
        for record in records:
            group = str(record[group_key])
            if group in seen and seen[group] != split_name:
                raise ValueError(f"group leakage: {group_key}={group} in {seen[group]} and {split_name}")
            seen[group] = split_name


def split_manifest(
    records: Sequence[Mapping[str, Any]],
    split_type: str,
    group_key: str | None,
    ratios: Mapping[str, float],
    seed: int,
) -> dict[str, Any]:
    splits = assign_split(records, group_key, ratios, seed)
    if group_key:
        assert_group_disjoint(splits, group_key)
    return {
        "split_type": split_type,
        "group_key": group_key,
        "ratios": dict(ratios),
        "seed": seed,
        "source_manifest_sha256": stable_manifest_hash(records),
        "counts": {name: len(items) for name, items in splits.items()},
        "assignments": {
            str(record["record_id"]): name
            for name, items in splits.items() for record in items
        },
    }
