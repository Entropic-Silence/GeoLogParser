from __future__ import annotations

import os
from pathlib import Path

from geologparser.cad_review import create_cad_review_app


ROOT = Path(__file__).resolve().parents[1]
DERIVATIVE_ROOT = Path(os.environ.get(
    "GEOLOGPARSER_CAD_DERIVATIVE_ROOT",
    "/data/GeoLogParser/datasets/public/mendeley_borehole_logs_v002/audit/full_svg_derivatives_v002",
))
REVIEW_ROOT = Path(os.environ.get(
    "GEOLOGPARSER_CAD_REVIEW_ROOT",
    "/data/GeoLogParser/datasets/public/mendeley_borehole_logs_v002/audit/content_reviews_v001",
))

app = create_cad_review_app(
    DERIVATIVE_ROOT / "derivative_manifest.jsonl",
    DERIVATIVE_ROOT,
    REVIEW_ROOT,
    ROOT / "app" / "cad_static",
    ROOT / "schemas" / "cad_content_review_v001.schema.json",
)
