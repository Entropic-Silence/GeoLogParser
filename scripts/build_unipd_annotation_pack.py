#!/usr/bin/env python3
"""Render every Padova borehole-log page and create immutable auto proposals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.annotation import PanelSpec, create_annotation, pdf_bbox_to_rendered_pixels, render_panel, save_annotation
from geologparser.extraction import extract_structured
from geologparser.pdf import PyMuPDFPanelTextAdapter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=150)
    arguments = parser.parse_args()
    rows = [json.loads(line) for line in arguments.source_manifest.read_text(encoding="utf-8").splitlines() if line]
    panel_rows = []
    adapter = PyMuPDFPanelTextAdapter()
    for item in rows:
        for page in range(1, int(item["page_count"]) + 1):
            panel_id = f"UNIPD_{item['source_record_id']}_P{page:03d}"
            spec = PanelSpec(
                panel_id=panel_id,
                source_path=item["local_path"],
                source_page=page,
                normalized_bbox=(0.0, 0.0, 1.0, 1.0),
                borehole_hint=item["source_record_id"],
                project_id="UNIPD_LEVEE_GEOTECH_V001",
                template_id="UNIPD_NATIVE_LOG",
                redistribution_status="allowed_with_attribution_CC_BY_4_0",
            )
            image_path = arguments.output_root / "images" / f"{panel_id}.png"
            panel = render_panel(spec, image_path, arguments.dpi)
            panel_rows.append(panel)
            regions = adapter.extract_panel(Path(item["local_path"]), page, spec.normalized_bbox)
            record = extract_structured(regions, Path(item["local_path"]))
            for envelope in list(record["borehole"].values()) + [
                value for interval in record["intervals"] for key, value in interval.items()
                if key != "interval_id"
            ]:
                if isinstance(envelope, dict) and envelope.get("source_bbox") is not None:
                    envelope["display_bbox"] = pdf_bbox_to_rendered_pixels(envelope["source_bbox"], panel)
                    envelope["display_bbox_source"] = "pdf_transform_v001"
                    envelope["display_bbox_annotator_id"] = None
            record["document"]["document_id"] = panel_id
            record["document"]["page_count"] = 1
            record["document"]["metadata"].update({
                "project_id": "UNIPD_LEVEE_GEOTECH_V001",
                "template_id": "UNIPD_NATIVE_LOG",
                "source_id": "UNIPD_LEVEE_GEOTECH_V001",
                "contains_stamp": False,
                "contains_handwriting": False,
                "dpi": arguments.dpi,
                "license": "CC-BY-4.0",
                "source_dataset_doi": item["source_dataset_doi"],
                "source_record_id": item["source_record_id"],
                "source_document_page": page,
            })
            annotation = create_annotation(panel_id, panel, record, "AUTO_NATIVE_PDF_V001", "auto")
            destination = arguments.output_root / "annotations" / f"{panel_id}.json"
            if destination.exists():
                raise FileExistsError(f"annotation already exists: {destination}")
            save_annotation(annotation, destination)
    manifest_path = arguments.output_root / "panel_manifest.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in panel_rows),
        encoding="utf-8",
    )
    print(json.dumps({"pages": len(panel_rows), "manifest": str(manifest_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
