#!/usr/bin/env python3
"""Render source DWGs to review PNGs with entity-level SVG coverage evidence.

The output is quarantined review material.  It never becomes benchmark data
without a separate human visual/content review and a later annotation gate.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from zipfile import ZipFile

from geologparser.cad_svg import entity_coverage, graphical_entities, write_review_png


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("dwg2svg", type=Path)
    parser.add_argument("dwgread", type=Path)
    parser.add_argument("--library-dir", type=Path)
    parser.add_argument("--output-width", type=int, default=1600)
    parser.add_argument(
        "--source-record-id", action="append", default=[],
        help="render only this source ID; repeat for a smoke-test subset",
    )
    arguments = parser.parse_args()
    if arguments.output_directory.exists():
        raise FileExistsError(f"output directory exists: {arguments.output_directory}")
    if arguments.output_width < 500:
        raise ValueError("output width must be at least 500 pixels")
    environment = os.environ.copy()
    if arguments.library_dir:
        previous = environment.get("LD_LIBRARY_PATH")
        environment["LD_LIBRARY_PATH"] = str(arguments.library_dir) + (f":{previous}" if previous else "")
    sources = [json.loads(line) for line in arguments.source_manifest.read_text(encoding="utf-8").splitlines() if line]
    source_ids = [source["source_record_id"] for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source manifest contains duplicate source_record_id values")
    if arguments.source_record_id:
        requested = set(arguments.source_record_id)
        unknown = sorted(requested - set(source_ids))
        if unknown:
            raise ValueError(f"unknown source-record IDs: {unknown}")
        sources = [source for source in sources if source["source_record_id"] in requested]
    if not sources:
        raise ValueError("no source records selected")
    arguments.output_directory.mkdir(parents=True)
    rows = []
    with ZipFile(arguments.archive) as archive:
        members = archive.infolist()
        for source in sources:
            started = time.perf_counter()
            identifier = source["source_record_id"]
            item = arguments.output_directory / identifier
            item.mkdir()
            data = archive.read(members[source["archive_index"]])
            if hashlib.sha256(data).hexdigest() != source["sha256"]:
                raise ValueError(f"source hash mismatch: {identifier}")
            dwg_path = item / "source.dwg"
            source_svg_path = item / "source_renderer.svg"
            review_svg_path = item / "review.svg"
            png_path = item / "model.png"
            render_log = item / "dwg2svg.log"
            dwg_path.write_bytes(data)
            render = subprocess.run(
                [str(arguments.dwg2svg), str(dwg_path)], capture_output=True, env=environment,
            )
            source_svg_path.write_bytes(render.stdout)
            diagnostic = render.stderr.decode("utf-8", errors="replace")
            render_log.write_text(diagnostic, encoding="utf-8")
            if render.returncode != 0 or not render.stdout.startswith(b"<?xml"):
                raise RuntimeError(f"dwg2SVG failed: {identifier}")
            with tempfile.TemporaryDirectory(dir=arguments.output_directory, prefix="minjson_") as temporary:
                json_path = Path(temporary) / "source.min.json"
                decoded = subprocess.run(
                    [str(arguments.dwgread), "-O", "minJSON", "-o", str(json_path), str(dwg_path)],
                    capture_output=True, text=True, env=environment,
                )
                if decoded.returncode != 0 or not json_path.is_file():
                    raise RuntimeError(f"dwgread failed: {identifier}")
                payload = json.loads(json_path.read_text(encoding="utf-8"))
            entities = graphical_entities(payload)
            # Preserve the renderer output exactly.  Unsupported MTEXT remains
            # missing instead of being overlaid using an unverified transform.
            review_svg = render.stdout.decode("utf-8")
            review_svg_path.write_text(review_svg, encoding="utf-8")
            coverage = entity_coverage(review_svg, entities)
            raster = write_review_png(review_svg, png_path, arguments.output_width)
            incomplete = (
                not coverage["complete_entity_id_coverage"]
                or not raster["geometry_audit"]["geometry_sanity_passed"]
                or raster["raster_is_placeholder"]
            )
            if not raster["geometry_audit"]["geometry_sanity_passed"]:
                technical_status = "renderer_emitted_invalid_svg_geometry"
            elif raster["raster_is_placeholder"]:
                technical_status = "renderer_emitted_empty_raster"
            elif coverage["complete_entity_id_coverage"]:
                technical_status = "review_raster_created_with_complete_entity_ids"
            else:
                technical_status = "review_raster_created_with_missing_or_extra_entity_ids"
            rows.append({
                "derivative_schema_version": "cad_svg_derivative_v002",
                "source_record_id": identifier,
                "source_sha256": source["sha256"],
                "source_manifest_sha256": sha256(arguments.source_manifest),
                "renderer": "LibreDWG dwg2SVG 0.14 + CairoSVG 2.8.2",
                "dwg2svg_executable_sha256": sha256(arguments.dwg2svg),
                "dwgread_executable_sha256": sha256(arguments.dwgread),
                "dwg2svg_returncode": render.returncode,
                "dwg2svg_diagnostic_sha256": sha256(render_log),
                "source_svg_sha256": sha256(source_svg_path),
                "review_svg_sha256": sha256(review_svg_path),
                "png_sha256": sha256(png_path),
                **raster,
                "coverage": coverage,
                "entity_id_coverage_complete": coverage["complete_entity_id_coverage"],
                "technical_render_status": technical_status,
                "visual_fidelity_status": "not_assessed",
                "conversion_may_be_incomplete": incomplete,
                "human_visual_review_status": "not_reviewed",
                "benchmark_eligible": False,
                "elapsed_seconds": time.perf_counter() - started,
            })
            print(f"{len(rows)}/{len(sources)} {identifier} coverage={coverage['entity_coverage']}")
    manifest = arguments.output_directory / "derivative_manifest.jsonl"
    manifest.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    summary = {
        "scope": "quarantined review-only source-DWG SVG derivatives; not benchmark data",
        "items": len(rows),
        "items_with_complete_entity_id_coverage": sum(row["coverage"]["complete_entity_id_coverage"] for row in rows),
        "items_with_incomplete_conversion_warning": sum(row["conversion_may_be_incomplete"] for row in rows),
        "source_entity_count": sum(row["coverage"]["source_entity_count"] for row in rows),
        "rendered_source_entity_count": sum(row["coverage"]["rendered_source_entity_count"] for row in rows),
        "missing_entity_type_counts": dict(sorted(sum((Counter(
            row["coverage"]["missing_entity_type_counts"]
        ) for row in rows), Counter()).items())),
        "items_with_geometry_sanity_failure": sum(
            not row["geometry_audit"]["geometry_sanity_passed"] for row in rows
        ),
        "placeholder_images": sum(row["raster_is_placeholder"] for row in rows),
        "technical_render_status_counts": dict(sorted(Counter(
            row["technical_render_status"] for row in rows
        ).items())),
        "visual_fidelity_status": "not_assessed",
        "human_visual_reviews": 0, "benchmark_eligible_items": 0,
        "manifest_sha256": sha256(manifest),
    }
    (arguments.output_directory / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
