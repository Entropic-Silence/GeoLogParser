from __future__ import annotations

import os
from pathlib import Path

from geologparser.annotation_api import create_app


ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_ROOT = Path(os.environ.get(
    "GEOLOGPARSER_ANNOTATION_ROOT",
    "/data/GeoLogParser/artifacts/annotation/sanming_quarantine_v001/annotations",
))
EXPERT_ANNOTATOR_IDS = {
    item.strip()
    for item in os.environ.get("GEOLOGPARSER_EXPERT_ANNOTATOR_IDS", "").split(",")
    if item.strip()
}
_ALLOWED_ANNOTATOR_IDS = os.environ.get("GEOLOGPARSER_ALLOWED_ANNOTATOR_IDS")
ALLOWED_ANNOTATOR_IDS = (
    {item.strip() for item in _ALLOWED_ANNOTATOR_IDS.split(",") if item.strip()}
    if _ALLOWED_ANNOTATOR_IDS is not None else None
)
FIXED_ANNOTATOR_ID = os.environ.get("GEOLOGPARSER_FIXED_ANNOTATOR_ID") or None

app = create_app(
    ANNOTATION_ROOT, ROOT / "app" / "static",
    expert_annotator_ids=EXPERT_ANNOTATOR_IDS,
    allowed_annotator_ids=ALLOWED_ANNOTATOR_IDS,
    fixed_annotator_id=FIXED_ANNOTATOR_ID,
)
