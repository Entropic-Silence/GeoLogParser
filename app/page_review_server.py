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

app = create_page_review_app(
    PACK_ROOT,
    REVIEW_ROOT,
    ROOT / "app" / "page_review_static",
    ROOT / "schemas" / "page_content_review_v001.schema.json",
)

