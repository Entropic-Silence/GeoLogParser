"""Reference-blind semantic roles for adjacent borehole-log columns.

Historical composite logs often place several narrow columns next to one
another (stratigraphy, drilled depth, graphic log, core, casing, electrical
logs).  Texture-only column detection cannot distinguish them.  This module
uses OCR header anchors and column geometry to attach a semantic role before
graphical boundary generation.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ColumnRoleAnchor:
    role: str
    center_x: float
    center_y: float
    confidence: float
    texts: tuple[str, ...]


@dataclass(frozen=True)
class ColumnRoleAssignment:
    left: int
    right: int
    center_x: float
    role: str
    score: float
    anchor_x: float | None
    evidence: tuple[str, ...]


_ROLE_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "graphic_log": (re.compile(r"graphic", re.I), re.compile(r"\blog\b", re.I)),
    "stratigraphy": (re.compile(r"\bstratigraph(y|ic)\b", re.I), re.compile(r"\blitholog(y|ical)\b", re.I)),
    "depth_drilled": (re.compile(r"\bdepth\b", re.I), re.compile(r"\bdrilled\b", re.I), re.compile(r"\bbelow\b", re.I)),
    "core": (re.compile(r"\bcore\b", re.I),),
    "casing": (re.compile(r"\bcasing\b", re.I),),
    "electrical_log": (re.compile(r"\belectrical\b", re.I),),
    "description": (re.compile(r"\b(description|descriptions)\b", re.I),),
    "remarks": (re.compile(r"\b(remarks?|comments?)\b", re.I),),
}


def _bbox(row: Mapping[str, object]) -> tuple[float, float, float, float] | None:
    value = row.get("bbox")
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        return tuple(float(item) for item in value)  # type: ignore[return-value]
    except (TypeError, ValueError):
        return None


def _center(row: Mapping[str, object]) -> tuple[float, float] | None:
    box = _bbox(row)
    if box is None:
        return None
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def infer_column_role_anchors(
    rows: Sequence[Mapping[str, object]], *, width: int, height: int,
    header_y: float | None = None,
) -> tuple[ColumnRoleAnchor, ...]:
    """Infer role anchors from OCR header text without reference labels.

    Multi-word headers are allowed to be split into separate OCR regions.  A
    role receives the best matching region(s) in the header band; for
    ``graphic_log`` and ``depth_drilled`` the nearby words are merged by x/y
    proximity.
    """
    if width <= 0 or height <= 0:
        raise ValueError("page dimensions must be positive")
    centers = []
    for row in rows:
        center = _center(row)
        text = str(row.get("text") or "").strip()
        if center is None or not text:
            continue
        _, cy = center
        normalized_y = cy / height
        if header_y is not None and abs(normalized_y - header_y) > 0.06:
            continue
        confidence = max(0.0, min(1.0, float(row.get("confidence") or 0.0)))
        centers.append((row, center, confidence, text))

    anchors: list[ColumnRoleAnchor] = []
    for role, patterns in _ROLE_PATTERNS.items():
        matched = []
        for row, center, confidence, text in centers:
            if any(pattern.search(text) for pattern in patterns):
                matched.append((row, center, confidence, text))
        if not matched:
            continue
        # For composite roles, prefer a compact same-row grouping.  For
        # single-word roles this naturally selects the highest-confidence OCR
        # region if duplicates are present.
        if role == "graphic_log":
            graphic_words = [item for item in matched if re.search(r"graphic", item[3], re.I)]
            if graphic_words:
                pivot = max(graphic_words, key=lambda item: item[2])
                px, py = pivot[1]
                matched = [item for item in matched if abs(item[1][1] - py) <= height * 0.035 and abs(item[1][0] - px) <= width * 0.10]
        elif role == "depth_drilled" and len(matched) > 1:
            best_group = None
            for pivot in matched:
                px, py = pivot[1]
                group = [item for item in matched if abs(item[1][1] - py) <= height * 0.035 and abs(item[1][0] - px) <= width * 0.10]
                score = sum(item[2] for item in group) + 0.05 * len(group)
                if best_group is None or score > best_group[0]:
                    best_group = (score, group)
            matched = best_group[1] if best_group else matched
        total = sum(item[2] for item in matched)
        center_x = sum(item[1][0] * max(item[2], 0.1) for item in matched) / sum(max(item[2], 0.1) for item in matched)
        center_y = sum(item[1][1] * max(item[2], 0.1) for item in matched) / sum(max(item[2], 0.1) for item in matched)
        anchors.append(ColumnRoleAnchor(
            role=role,
            center_x=center_x / width,
            center_y=center_y / height,
            confidence=min(1.0, total / max(1, len(matched))),
            texts=tuple(item[3] for item in matched),
        ))
    return tuple(anchors)


def assign_column_roles(
    columns: Sequence[tuple[int, int, float]],
    anchors: Sequence[ColumnRoleAnchor], *, width: int,
) -> tuple[ColumnRoleAssignment, ...]:
    """Assign semantic roles to detected vertical-rule intervals.

    The returned score is a role-specific evidence score, not a probability.
    It combines anchor proximity, anchor confidence and interval overlap with
    the header's inferred x position.  Columns without a reliable semantic
    anchor remain ``unknown`` and can be conservatively rejected by callers.
    """
    if width <= 0:
        raise ValueError("width must be positive")
    by_role = {anchor.role: anchor for anchor in anchors}
    output: list[ColumnRoleAssignment] = []
    for left, right, activity in columns:
        center = ((float(left) + float(right)) / 2.0) / width
        candidates = []
        for role, anchor in by_role.items():
            distance = abs(center - anchor.center_x)
            # Adjacent historical columns can be narrow; a 3% normalized
            # distance is already a meaningful mismatch on a 2500px page.
            proximity = max(0.0, 1.0 - distance / 0.055)
            score = proximity * (0.55 + 0.45 * anchor.confidence)
            candidates.append((score, role, anchor))
        if candidates:
            score, role, anchor = max(candidates, key=lambda item: (item[0], item[2].confidence))
            evidence = (f"anchor:{role}", f"anchor_distance:{abs(center-anchor.center_x):.5f}", f"activity:{float(activity):.4f}")
            output.append(ColumnRoleAssignment(left, right, center, role if score >= 0.28 else "unknown", score, anchor.center_x, evidence))
        else:
            output.append(ColumnRoleAssignment(left, right, center, "unknown", 0.0, None, (f"activity:{float(activity):.4f}",)))
    return tuple(output)


def select_graphical_roles(
    assignments: Sequence[ColumnRoleAssignment], *, minimum_score: float = 0.28,
) -> tuple[ColumnRoleAssignment, ...]:
    """Select primary graphic evidence while retaining a narrow core role.

    Stratigraphy/depth/description/electrical columns are explicitly excluded
    even when their texture activity is high.  If a page has no graphic-log
    anchor, the function returns an empty tuple rather than silently reverting
    to texture-only selection.
    """
    accepted = [
        item for item in assignments
        if item.role == "graphic_log" and item.score >= max(minimum_score, 0.45)
        or item.role == "core" and item.score >= minimum_score
    ]
    primary = [item for item in accepted if item.role == "graphic_log"]
    if primary:
        return tuple(sorted(primary + [item for item in accepted if item.role == "core"], key=lambda item: item.left))
    return tuple()
