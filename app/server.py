from __future__ import annotations

import os
from pathlib import Path

from geologparser.annotation_api import create_app


ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_ROOT = Path(os.environ.get(
    "GEOLOGPARSER_ANNOTATION_ROOT",
    "/data/GeoLogParser/artifacts/annotation/sanming_quarantine_v001/annotations",
))

app = create_app(ANNOTATION_ROOT, ROOT / "app" / "static")
