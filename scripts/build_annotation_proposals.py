#!/usr/bin/env python3
"""Build auto-labelled annotation proposals from a rendered panel manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.annotation import create_annotation, pdf_bbox_to_rendered_pixels, save_annotation
from geologparser.extraction import extract_structured
from geologparser.pdf import PyMuPDFPanelTextAdapter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("panel_manifest", type=Path)
    parser.add_argument("annotation_root", type=Path)
    arguments = parser.parse_args()
    adapter = PyMuPDFPanelTextAdapter()
    for line in arguments.panel_manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        panel = json.loads(line)
        source = Path(panel["source_path"])
        regions = adapter.extract_panel(
            source, int(panel["source_page"]), tuple(panel["normalized_bbox"]),
        )
        record = extract_structured(regions, source)
        for envelope in list(record["borehole"].values()) + [
            value for interval in record["intervals"] for key, value in interval.items()
            if key != "interval_id"
        ]:
            if isinstance(envelope, dict) and envelope.get("source_bbox") is not None:
                envelope["display_bbox"] = pdf_bbox_to_rendered_pixels(envelope["source_bbox"], panel)
        record["document"]["document_id"] = panel["panel_id"]
        record["document"]["page_count"] = 1
        record["document"]["metadata"].update({
            "project_id": panel.get("project_id"),
            "template_id": panel.get("template_id"),
            "source_id": "QUARANTINE_SANMING_PUBLIC_WEB",
            "contains_stamp": True,
            "contains_handwriting": None,
            "dpi": panel.get("render_dpi"),
        })
        annotation = create_annotation(
            annotation_id=panel["panel_id"], panel=panel, record=record,
            annotator_id="AUTO_NATIVE_PDF_V001", status="auto",
        )
        destination = arguments.annotation_root / f"{panel['panel_id']}.json"
        if destination.exists():
            raise FileExistsError(f"proposal already exists and will not be overwritten: {destination}")
        save_annotation(annotation, destination)
        print(destination)


if __name__ == "__main__":
    main()
