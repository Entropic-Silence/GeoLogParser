"""Reference-blind page-family and explicit depth-range evidence parsing.

The v023 external failure showed that a single candidate generator cannot be
treated as source agnostic: a printed range table, a scaled composite log and
a graphical contact log expose different structural evidence.  This module
routes those families before numerical decoding and provides a conservative
range-table reader that abstains unless a contiguous sequence is recovered.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import csv
import io
import math
from pathlib import Path
import re
import subprocess
from typing import Iterable, Mapping, Sequence

import cv2
import numpy as np


@dataclass(frozen=True)
class PageFamilyAssessment:
    family: str
    confidence: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class ExplicitDepthRange:
    top_m: float
    bottom_m: float
    page: int
    bbox: tuple[float, float, float, float]
    source_texts: tuple[str, ...]
    view_support: int
    score: float


def _normalized_text(rows: Sequence[Mapping[str, object]]) -> str:
    return " ".join(
        re.sub(r"[^a-z0-9]+", " ", str(row.get("text") or "").lower()).strip()
        for row in rows
    )


def classify_borehole_page(
    rows: Sequence[Mapping[str, object]], *, width: int, height: int,
) -> PageFamilyAssessment:
    """Classify structural evidence without source IDs or reference intervals."""
    if width <= 0 or height <= 0:
        raise ValueError("page dimensions must be positive")
    text = _normalized_text(rows)
    tokens = set(text.split())
    evidence: list[str] = []

    explicit = 0
    if "thickness" in tokens:
        explicit += 2; evidence.append("header:thickness")
    if "depth" in tokens and "surface" in tokens:
        explicit += 3; evidence.append("header:depth_from_surface")
    if "recovered" in tokens:
        explicit += 1; evidence.append("header:recovered")
    if explicit >= 5:
        return PageFamilyAssessment("explicit_depth_range_table", min(0.99, 0.55 + 0.07 * explicit), tuple(evidence))

    scaled = 0
    if "stratigraphy" in tokens:
        scaled += 2; evidence.append("header:stratigraphy")
    if "graphic" in tokens and "log" in tokens:
        scaled += 2; evidence.append("header:graphic_log")
    if "depth" in tokens and ("drilled" in tokens or "below" in tokens):
        scaled += 2; evidence.append("header:drilled_depth")
    if "electrical" in tokens or "casing" in tokens:
        scaled += 1; evidence.append("header:auxiliary_log")
    if scaled >= 4:
        return PageFamilyAssessment("scaled_composite_log", min(0.98, 0.52 + 0.07 * scaled), tuple(evidence))

    graphical = 0
    if "composite" in tokens and "log" in tokens:
        graphical += 2; evidence.append("header:composite_log")
    if "lithology" in tokens or "lithological" in tokens:
        graphical += 2; evidence.append("header:lithology")
    if "description" in tokens:
        graphical += 2; evidence.append("header:description")
    if height / width >= 2.5:
        graphical += 1; evidence.append("geometry:long_page")
    if graphical >= 4:
        return PageFamilyAssessment("graphical_contact_log", min(0.97, 0.50 + 0.07 * graphical), tuple(evidence))

    return PageFamilyAssessment("unsupported", 1.0 - min(0.45, 0.05 * max(explicit, scaled, graphical)), tuple(evidence))


def _center(row: Mapping[str, object]) -> tuple[float, float]:
    bbox = [float(value) for value in row["bbox"]]
    return (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2


def locate_explicit_depth_column(
    rows: Sequence[Mapping[str, object]], *, width: int, height: int,
) -> tuple[int, int, int, int] | None:
    """Locate a `Depth from Surface` column from OCR header geometry."""
    depth = [row for row in rows if re.search(r"\bdepth\b", str(row.get("text") or ""), re.I)]
    surface = [row for row in rows if re.search(r"\bsurface\b", str(row.get("text") or ""), re.I)]
    pairs = []
    for left in depth:
        lx, ly = _center(left)
        for right in surface:
            rx, ry = _center(right)
            if abs(lx - rx) <= width * 0.12 and abs(ly - ry) <= height * 0.08:
                pairs.append((float(left.get("confidence") or 0) + float(right.get("confidence") or 0), left, right))
    if not pairs:
        return None
    _, depth_row, surface_row = max(pairs, key=lambda item: item[0])
    boxes = [[float(value) for value in row["bbox"]] for row in (depth_row, surface_row)]
    center_x = sum((box[0] + box[2]) / 2 for box in boxes) / len(boxes)
    header_bottom = max(box[3] for box in boxes)
    x1 = max(0, int(center_x - width * 0.115))
    x2 = min(width, int(center_x + width * 0.115))
    y1 = max(0, int(header_bottom + height * 0.02))
    y2 = min(height, int(height * 0.96))
    return (x1, y1, x2, y2) if x2 > x1 and y2 > y1 else None


def _numeric_hypotheses(text: str) -> list[tuple[float, float]]:
    cleaned = text.strip().replace(",", ".")
    cleaned = re.sub(r"[^0-9.]", "", cleaned)
    digits = "".join(re.findall(r"\d", cleaned))
    if not digits:
        return []
    hypotheses: dict[float, float] = {}
    if "." in cleaned:
        pieces = [piece for piece in cleaned.split(".") if piece]
        if pieces:
            normalized = pieces[0] + ("." + "".join(pieces[1:])[:2] if len(pieces) > 1 else "")
            try:
                hypotheses[float(normalized)] = 1.5
            except ValueError:
                pass
    integer = float(int(digits))
    hypotheses[integer] = max(hypotheses.get(integer, 0.0), 0.35)
    if len(digits) >= 3:
        value = float(int(digits)) / 100.0
        hypotheses[value] = max(hypotheses.get(value, 0.0), 1.15)
    if len(digits) >= 2:
        value = float(int(digits)) / 10.0
        hypotheses[value] = max(hypotheses.get(value, 0.0), 0.55)
    return sorted(hypotheses.items())


def _range_hypotheses(text: str) -> list[tuple[float, float, float]]:
    normalized = text.replace("—", "-").replace("–", "-").replace("_", "-")
    output = []
    for match in re.finditer(r"([0-9][0-9., ]*)\s*-+\s*([0-9][0-9., ]*)", normalized):
        for top, top_score in _numeric_hypotheses(match.group(1)):
            for bottom, bottom_score in _numeric_hypotheses(match.group(2)):
                if 0 <= top < bottom <= 5000 and bottom - top <= 1000:
                    output.append((top, bottom, top_score + bottom_score))
    return output


def _tesseract_lines(image: np.ndarray, *, scale: int, variant: str, psm: int) -> list[dict]:
    resized = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    if variant == "clean":
        binary = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        inverse = 255 - binary
        vertical = cv2.morphologyEx(
            inverse, cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (max(1, scale * 2), scale * 100)),
        )
        horizontal = cv2.morphologyEx(
            inverse, cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (scale * 80, max(1, scale * 2))),
        )
        resized = cv2.bitwise_not(cv2.subtract(inverse, cv2.bitwise_or(vertical, horizontal)))
    success, encoded = cv2.imencode(".png", resized)
    if not success:
        return []
    completed = subprocess.run(
        [
            "tesseract", "stdin", "stdout", "-l", "eng", "--psm", str(psm), "tsv",
            "-c", "tessedit_char_whitelist=0123456789.-",
        ],
        input=encoded.tobytes(), capture_output=True, check=False,
    )
    if completed.returncode != 0:
        return []
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    reader = csv.DictReader(io.StringIO(completed.stdout.decode("utf-8", errors="replace")), delimiter="\t")
    for row in reader:
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        try:
            grouped[(row["block_num"], row["par_num"], row["line_num"])].append({
                "text": text,
                "confidence": max(0.0, float(row.get("conf") or 0) / 100),
                "left": float(row["left"]) / scale,
                "top": float(row["top"]) / scale,
                "right": (float(row["left"]) + float(row["width"])) / scale,
                "bottom": (float(row["top"]) + float(row["height"])) / scale,
            })
        except (KeyError, TypeError, ValueError):
            continue
    lines = []
    for words in grouped.values():
        words.sort(key=lambda row: row["left"])
        lines.append({
            "text": " ".join(row["text"] for row in words),
            "confidence": sum(row["confidence"] for row in words) / len(words),
            "bbox": (
                min(row["left"] for row in words), min(row["top"] for row in words),
                max(row["right"] for row in words), max(row["bottom"] for row in words),
            ),
            "view": f"{variant}{scale}x_psm{psm}",
        })
    return lines


def extract_explicit_depth_ranges(
    image_path: Path, rows: Sequence[Mapping[str, object]], *, page: int,
) -> tuple[list[ExplicitDepthRange], dict[str, object]]:
    """Read a printed interval column and abstain on weak/non-contiguous output."""
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise FileNotFoundError(image_path)
    height, width = gray.shape[:2]
    roi = locate_explicit_depth_column(rows, width=width, height=height)
    if roi is None:
        return [], {"status": "abstained", "reason": "depth_from_surface_header_not_localized"}
    x1, y1, x2, y2 = roi
    crop = gray[y1:y2, x1:x2]
    lines = [
        line
        for scale in (2, 4)
        for variant in ("gray", "clean")
        for psm in (6, 11)
        for line in _tesseract_lines(crop, scale=scale, variant=variant, psm=psm)
    ]
    raw = []
    for line in lines:
        bbox = line["bbox"]
        page_bbox = (bbox[0] + x1, bbox[1] + y1, bbox[2] + x1, bbox[3] + y1)
        for top, bottom, parse_score in _range_hypotheses(line["text"]):
            raw.append({
                "top": top, "bottom": bottom, "score": parse_score + line["confidence"],
                "bbox": page_bbox, "text": line["text"], "view": line["view"],
                "center_y": (page_bbox[1] + page_bbox[3]) / 2,
            })
    clusters: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for row in raw:
        clusters[(round(row["top"] * 100), round(row["bottom"] * 100))].append(row)
    candidates = []
    for (top_key, bottom_key), values in clusters.items():
        ys = sorted(float(row["center_y"]) for row in values)
        median_y = ys[len(ys) // 2]
        local = [row for row in values if abs(float(row["center_y"]) - median_y) <= max(30.0, height * 0.012)]
        best = max(local, key=lambda row: row["score"])
        support = len({row["view"] for row in local})
        candidates.append({
            "top": top_key / 100, "bottom": bottom_key / 100,
            "score": float(best["score"]) + min(2.0, 0.45 * support),
            "bbox": best["bbox"], "center_y": median_y,
            "texts": tuple(sorted({row["text"] for row in local})), "support": support,
        })
    candidates.sort(key=lambda row: (row["center_y"], row["top"], row["bottom"]))

    # Reject decimal-loss hypotheses that create an isolated order-of-
    # magnitude jump.  The limit is adaptive to the smallest observed rows;
    # it is a risk gate, not a correction rule.
    observed_steps = sorted(
        row["bottom"] - row["top"] for row in candidates
        if 0 < row["bottom"] - row["top"] <= 20
    )
    maximum_explicit_step = max(20.0, 10.0 * (observed_steps[min(2, len(observed_steps) - 1)] if observed_steps else 2.0))
    candidates = [
        row for row in candidates
        if 0 < row["bottom"] - row["top"] <= maximum_explicit_step
    ]

    # Longest high-evidence contiguous path. A gap is allowed but penalized;
    # overlapping or depth-inverted rows are never silently repaired.
    scores = [float(row["score"]) + (1.5 if abs(row["top"]) <= 0.01 else 0.0) for row in candidates]
    previous = [-1] * len(candidates)
    for index, row in enumerate(candidates):
        for left in range(index):
            prior = candidates[left]
            if row["center_y"] <= prior["center_y"] + 5 or row["top"] < prior["bottom"] - 0.05:
                continue
            gap = abs(row["top"] - prior["bottom"])
            edge = 3.5 * math.exp(-gap / 0.08) - min(2.5, gap * 0.3)
            proposal = scores[left] + float(row["score"]) + edge
            if proposal > scores[index]:
                scores[index] = proposal; previous[index] = left
    if not candidates:
        return [], {"status": "abstained", "reason": "no_range_candidates", "roi": list(roi), "ocr_line_count": len(lines)}
    end = max(range(len(candidates)), key=scores.__getitem__)
    selected = []
    while end >= 0:
        selected.append(candidates[end]); end = previous[end]
    selected.reverse()
    adjacency = sum(abs(right["top"] - left["bottom"]) <= 0.05 for left, right in zip(selected, selected[1:]))
    continuity = adjacency / max(1, len(selected) - 1)
    starts_at_zero = bool(selected and abs(selected[0]["top"]) <= 0.05)
    if len(selected) < 3 or continuity < 0.66 or not starts_at_zero:
        return [], {
            "status": "abstained", "reason": "insufficient_contiguous_range_evidence",
            "roi": list(roi), "ocr_line_count": len(lines), "candidate_count": len(candidates),
            "selected_count": len(selected), "continuity": continuity,
        }
    output = [
        ExplicitDepthRange(
            top_m=float(row["top"]), bottom_m=float(row["bottom"]), page=page,
            bbox=tuple(float(value) for value in row["bbox"]), source_texts=row["texts"],
            view_support=int(row["support"]), score=float(row["score"]),
        )
        for row in selected
    ]
    return output, {
        "status": "accepted", "reason": "contiguous_explicit_depth_ranges",
        "roi": list(roi), "ocr_line_count": len(lines), "candidate_count": len(candidates),
        "selected_count": len(output), "continuity": continuity,
    }


def boundaries_from_ranges(ranges: Iterable[ExplicitDepthRange]) -> list[float]:
    return sorted({value for row in ranges for value in (row.top_m, row.bottom_m)})
