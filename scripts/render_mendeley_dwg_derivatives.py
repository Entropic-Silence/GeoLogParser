#!/usr/bin/env python3
"""Render selected quarantined DWGs into review-only PNG derivatives."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import time
from zipfile import ZipFile


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_version(name: str) -> str:
    from importlib.metadata import version

    return version(name)


def render_dxf(dxf_path: Path, output_path: Path, *, dpi: int, cjk_font: str) -> dict:
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.fonts import fonts
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fonts.build_system_font_cache()
    if not fonts.font_manager.has_font(cjk_font):
        raise RuntimeError(f"CJK fallback font is unavailable to ezdxf: {cjk_font}")
    fonts.font_manager._fallback_font_name = cjk_font
    document = ezdxf.readfile(dxf_path)
    substituted_styles = []
    for style in document.styles:
        if style.dxf.name in {"宋体", "黑体", "仿宋", "楷体"} or not style.dxf.font:
            substituted_styles.append({"style": style.dxf.name, "original_font": style.dxf.font})
            style.dxf.font = cjk_font
    layout = document.modelspace()
    entity_count = len(layout)
    figure = plt.figure(figsize=(8, 32), dpi=dpi)
    axes = figure.add_axes([0, 0, 1, 1])
    axes.set_axis_off()
    warnings = io.StringIO()
    with contextlib.redirect_stdout(warnings), contextlib.redirect_stderr(warnings):
        Frontend(RenderContext(document), MatplotlibBackend(axes)).draw_layout(layout, finalize=True)
        figure.savefig(
            output_path, dpi=dpi, facecolor="black", bbox_inches="tight", pad_inches=0.05
        )
    plt.close(figure)
    from PIL import Image

    with Image.open(output_path) as image:
        pixel_dimensions = [image.width, image.height]
    return {
        "layout": "Model",
        "entity_count": entity_count,
        "font_substitutions": substituted_styles,
        "renderer_diagnostics": warnings.getvalue(),
        "pixel_dimensions": pixel_dimensions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("dwg2dxf", type=Path)
    parser.add_argument("source_record_ids", nargs="+")
    parser.add_argument("--library-dir", type=Path)
    parser.add_argument("--dpi", type=int, default=250)
    parser.add_argument("--cjk-font", default="DroidSansFallbackFull.ttf")
    arguments = parser.parse_args()

    source_rows = {
        row["source_record_id"]: row
        for row in (
            json.loads(line)
            for line in arguments.source_manifest.read_text(encoding="utf-8").splitlines()
        )
    }
    missing = sorted(set(arguments.source_record_ids) - source_rows.keys())
    if missing:
        raise ValueError(f"unknown source record IDs: {missing}")
    if arguments.dpi < 72:
        raise ValueError("dpi must be at least 72")

    environment = os.environ.copy()
    if arguments.library_dir:
        previous = environment.get("LD_LIBRARY_PATH")
        environment["LD_LIBRARY_PATH"] = str(arguments.library_dir) + (f":{previous}" if previous else "")
    version_result = subprocess.run(
        [str(arguments.dwg2dxf), "--version"], capture_output=True, text=True,
        check=True, env=environment,
    )
    converter_version = (version_result.stdout or version_result.stderr).strip()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    with ZipFile(arguments.archive) as archive:
        members = archive.infolist()
        for source_record_id in arguments.source_record_ids:
            started = time.perf_counter()
            source = source_rows[source_record_id]
            member = members[source["archive_index"]]
            data = archive.read(member)
            if hashlib.sha256(data).hexdigest() != source["sha256"]:
                raise ValueError(f"source hash mismatch: {source_record_id}")
            item_dir = arguments.output_dir / source_record_id
            item_dir.mkdir(parents=True, exist_ok=False)
            dwg_path = item_dir / "source.dwg"
            dxf_path = item_dir / "source.dxf"
            png_path = item_dir / "model.png"
            converter_log_path = item_dir / "dwg2dxf.log"
            renderer_log_path = item_dir / "renderer.log"
            dwg_path.write_bytes(data)
            conversion = subprocess.run(
                [str(arguments.dwg2dxf), "-o", str(dxf_path), str(dwg_path)],
                capture_output=True, text=True, env=environment,
            )
            converter_diagnostics = "\n".join(
                part.strip() for part in (conversion.stdout, conversion.stderr) if part.strip()
            ) + "\n"
            converter_log_path.write_text(converter_diagnostics, encoding="utf-8")
            if conversion.returncode != 0 or not dxf_path.exists():
                raise RuntimeError(f"DWG-to-DXF conversion failed: {source_record_id}")
            rendering = render_dxf(
                dxf_path, png_path, dpi=arguments.dpi, cjk_font=arguments.cjk_font
            )
            renderer_log_path.write_text(rendering.pop("renderer_diagnostics"), encoding="utf-8")
            conversion_may_be_incomplete = any(
                marker in converter_diagnostics.lower()
                for marker in ("warning", "error", "ignored", "skip", "overflow", "invalid")
            )
            rows.append({
                "derivative_schema_version": "cad_derivative_v001",
                "source_record_id": source_record_id,
                "source_sha256": source["sha256"],
                "source_manifest_sha256": sha256(arguments.source_manifest),
                "dwg2dxf_version": converter_version,
                "dwg2dxf_executable_sha256": sha256(arguments.dwg2dxf),
                "dwg2dxf_returncode": conversion.returncode,
                "dxf_sha256": sha256(dxf_path),
                "converter_log_sha256": sha256(converter_log_path),
                "conversion_may_be_incomplete": conversion_may_be_incomplete,
                "renderer": f"ezdxf {package_version('ezdxf')} + matplotlib {package_version('matplotlib')}",
                "renderer_log_sha256": sha256(renderer_log_path),
                "dpi": arguments.dpi,
                "cjk_fallback_font": arguments.cjk_font,
                "png_sha256": sha256(png_path),
                "human_visual_review_status": "not_reviewed",
                "benchmark_eligible": False,
                "elapsed_seconds": time.perf_counter() - started,
                **rendering,
            })
            print(f"{len(rows)}/{len(arguments.source_record_ids)} {source_record_id}")

    manifest = arguments.output_dir / "derivative_manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "scope": "quarantined review-only CAD derivatives; not benchmark data",
        "items": len(rows),
        "items_with_incomplete_conversion_warning": sum(
            row["conversion_may_be_incomplete"] for row in rows
        ),
        "human_visual_reviews": 0,
        "benchmark_eligible_items": 0,
        "manifest_sha256": sha256(manifest),
    }
    (arguments.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
