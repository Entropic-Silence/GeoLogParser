from __future__ import annotations

import os
from pathlib import Path

from geologparser.page_review import create_page_review_app


ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = Path(os.environ.get(
    "GEOLOGPARSER_PAGE_REVIEW_PACK_ROOT",
    "/data/GeoLogParser/artifacts/source_review/international_candidates_v001",
))
REVIEW_ROOT = Path(os.environ.get(
    "GEOLOGPARSER_PAGE_REVIEW_ROOT",
    "/data/GeoLogParser/artifacts/source_review/international_candidates_v001/reviews",
))
FIXED_REVIEWER_ID = os.environ.get("GEOLOGPARSER_PAGE_REVIEWER_ID") or None
STATUS_OUTPUT = Path(os.environ.get(
    "GEOLOGPARSER_PAGE_REVIEW_STATUS_OUTPUT",
    str(REVIEW_ROOT / "review_status.json"),
))

app = create_page_review_app(
    PACK_ROOT,
    REVIEW_ROOT,
    ROOT / "app" / "page_review_static",
    ROOT / "schemas" / "page_content_review_v001.schema.json",
    fixed_reviewer_id=FIXED_REVIEWER_ID,
    status_output=STATUS_OUTPUT,
)
