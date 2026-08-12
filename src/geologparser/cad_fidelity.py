"""Conservative source-DWG to derivative-DXF inventory reconciliation.

Inventory agreement is evidence that decoded entities were retained.  It is
not proof of pixel fidelity, correct font rendering, privacy clearance, or
benchmark eligibility.  Those decisions remain human-gated.
"""

from __future__ import annotations

from collections import Counter
import hashlib
from typing import Any, Iterable, Mapping, Sequence


NON_CONTENT_ENTITIES = {"BLOCK", "ENDBLK"}
TEXT_ENTITIES = {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}


def _handle(value: Any) -> str | None:
    """Return a comparable uppercase hexadecimal handle.

    LibreDWG minJSON represents handles as arrays whose final item is the
    absolute handle value.  DXF readers generally expose the hexadecimal
    string directly.
    """
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and value:
        value = value[-1]
    if isinstance(value, int) and not isinstance(value, bool):
        return format(value, "X")
    if isinstance(value, str) and value:
        return value.upper().removeprefix("0X")
    return None


def _text_value(entity: Mapping[str, Any]) -> str:
    value = entity.get("text")
    if value is None:
        value = entity.get("text_value", "")
    return str(value)


def inventory_from_entities(entities: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build an order-preserving, hashable entity inventory."""
    retained = []
    for entity in entities:
        raw_type = entity.get("entity") or entity.get("type") or ""
        if not isinstance(raw_type, str):
            continue
        entity_type = raw_type.upper()
        if not entity_type or entity_type in NON_CONTENT_ENTITIES:
            continue
        retained.append((entity_type, _handle(entity.get("handle")), entity))
    counts = Counter(entity_type for entity_type, _, _ in retained)
    handles = [handle for _, handle, _ in retained if handle is not None]
    texts = [
        _text_value(entity) for entity_type, _, entity in retained
        if entity_type in TEXT_ENTITIES
    ]
    text_payload = "\n".join(texts).encode("utf-8")
    return {
        "entity_count": len(retained),
        "entity_type_counts": dict(sorted(counts.items())),
        "handle_count": len(handles),
        "unique_handle_count": len(set(handles)),
        "handles": handles,
        "text_entity_count": len(texts),
        "ordered_text_sha256": hashlib.sha256(text_payload).hexdigest(),
        "texts": texts,
    }


def compare_inventories(source: Mapping[str, Any], derivative: Mapping[str, Any]) -> dict[str, Any]:
    """Compare source and derivative inventories without declaring fidelity."""
    source_handles = set(source.get("handles", ()))
    derivative_handles = set(derivative.get("handles", ()))
    shared_handles = source_handles & derivative_handles
    source_count = int(source.get("entity_count", 0))
    derivative_count = int(derivative.get("entity_count", 0))
    type_counts_match = source.get("entity_type_counts") == derivative.get("entity_type_counts")
    text_count_match = source.get("text_entity_count") == derivative.get("text_entity_count")
    text_hash_match = source.get("ordered_text_sha256") == derivative.get("ordered_text_sha256")
    exact_handle_set_match = source_handles == derivative_handles
    structural_inventory_match = (
        source_count == derivative_count
        and type_counts_match
        and text_count_match
        and text_hash_match
        and exact_handle_set_match
        and int(source.get("unique_handle_count", 0)) == source_count
        and int(derivative.get("unique_handle_count", 0)) == derivative_count
    )
    return {
        "status": (
            "structural_inventory_match"
            if structural_inventory_match else "structural_inventory_mismatch"
        ),
        "structural_inventory_match": structural_inventory_match,
        "source_entity_count": source_count,
        "derivative_entity_count": derivative_count,
        "entity_type_counts_match": type_counts_match,
        "source_entity_type_counts": dict(source.get("entity_type_counts", {})),
        "derivative_entity_type_counts": dict(derivative.get("entity_type_counts", {})),
        "source_unique_handle_count": len(source_handles),
        "derivative_unique_handle_count": len(derivative_handles),
        "shared_handle_count": len(shared_handles),
        "source_handle_coverage": len(shared_handles) / len(source_handles) if source_handles else None,
        "derivative_handle_coverage": (
            len(shared_handles) / len(derivative_handles) if derivative_handles else None
        ),
        "missing_source_handles": sorted(source_handles - derivative_handles),
        "extra_derivative_handles": sorted(derivative_handles - source_handles),
        "source_text_entity_count": int(source.get("text_entity_count", 0)),
        "derivative_text_entity_count": int(derivative.get("text_entity_count", 0)),
        "text_count_match": text_count_match,
        "ordered_text_sha256_match": text_hash_match,
        "source_ordered_text_sha256": source.get("ordered_text_sha256"),
        "derivative_ordered_text_sha256": derivative.get("ordered_text_sha256"),
        "interpretation": (
            "Automated structural/text inventory reconciliation only; not pixel-fidelity, "
            "privacy, rights, human-review, annotation, or benchmark evidence."
        ),
    }


def public_inventory(inventory: Mapping[str, Any]) -> dict[str, Any]:
    """Remove raw handles/text while retaining reproducible aggregate evidence."""
    return {
        key: value for key, value in inventory.items()
        if key not in {"handles", "texts"}
    }
