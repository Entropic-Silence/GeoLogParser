#!/usr/bin/env python3
"""Audit priority CAD rasters and probe LibreCAD's headless capability."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from geologparser.cad_raster import RasterAuditConfig, compare_rasters


SCRIPT_PATH = Path(__file__).resolve()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_manifest(path: Path) -> dict[str, dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    identifiers = [row["source_record_id"] for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"duplicate source_record_id in {path}")
    return {row["source_record_id"]: row for row in rows}


def libre_cad_help(executable: Path, environment: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(executable), "--help"], capture_output=True, text=True, env=environment,
        timeout=30,
    )


def debian_package_version(executable: Path) -> str | None:
    result = subprocess.run(
        ["dpkg-query", "-S", str(executable)], capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    package = result.stdout.split(":", 1)[0].strip()
    version = subprocess.run(
        ["dpkg-query", "-W", "-f=${Version}", package], capture_output=True, text=True,
    )
    return version.stdout.strip() if version.returncode == 0 else None


def probe_librecad(
    executable: Path, dxf_path: Path, environment: dict[str, str], timeout_seconds: float,
) -> tuple[dict, str, str]:
    started = time.perf_counter()
    process = subprocess.Popen(
        [str(executable), str(dxf_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, env=environment,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
    fatal_markers = (
        "could not connect to display", "could not load the qt platform plugin",
        "no qt platform plugin could be initialized", "segmentation fault",
    )
    combined = f"{stdout}\n{stderr}".lower()
    fatal_errors = [marker for marker in fatal_markers if marker in combined]
    if fatal_errors:
        status = "qt_or_process_fatal_error"
    elif timed_out:
        status = "process_remained_open_until_timeout"
    elif process.returncode == 0:
        status = "process_exited_zero"
    else:
        status = "process_exited_nonzero"
    return ({
        "status": status,
        "returncode": process.returncode,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
        "fatal_error_markers": fatal_errors,
        "elapsed_seconds": time.perf_counter() - started,
        "interpretation": (
            "GUI startup probe only; timeout without a fatal Qt error does not prove complete "
            "DXF parsing, rendering correctness, or export capability."
        ),
    }, stdout, stderr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dxf_manifest", type=Path)
    parser.add_argument("dxf_root", type=Path)
    parser.add_argument("svg_manifest", type=Path)
    parser.add_argument("svg_root", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("librecad", type=Path)
    parser.add_argument("--probe-timeout-seconds", type=float, default=3.0)
    parser.add_argument("--minimum-tolerant-f1", type=float, default=0.50)
    arguments = parser.parse_args()
    if arguments.output_directory.exists():
        raise FileExistsError(f"output directory already exists: {arguments.output_directory}")
    if arguments.probe_timeout_seconds <= 0:
        raise ValueError("probe timeout must be positive")
    dxf_rows, svg_rows = read_manifest(arguments.dxf_manifest), read_manifest(arguments.svg_manifest)
    identifiers = sorted(dxf_rows.keys())
    if not identifiers or set(identifiers) - svg_rows.keys():
        raise ValueError("SVG manifest does not cover every selected DXF derivative")
    arguments.output_directory.mkdir(parents=True)
    environment = os.environ.copy()
    runtime = arguments.output_directory / "runtime"
    runtime.mkdir(mode=0o700)
    environment.update({
        "QT_QPA_PLATFORM": "offscreen",
        "XDG_RUNTIME_DIR": str(runtime),
        "XDG_CONFIG_HOME": str(arguments.output_directory / "xdg_config"),
        "XDG_CACHE_HOME": str(arguments.output_directory / "xdg_cache"),
        "XDG_DATA_HOME": str(arguments.output_directory / "xdg_data"),
    })
    help_result = libre_cad_help(arguments.librecad, environment)
    help_log = arguments.output_directory / "librecad_help.log"
    help_text = f"STDOUT\n{help_result.stdout}\nSTDERR\n{help_result.stderr}"
    help_log.write_text(help_text, encoding="utf-8")
    help_lower = help_text.lower()
    advertised_export_flags = [
        flag for flag in ("--export", "--print", "--pdf", "--png", "--save-as")
        if flag in help_lower
    ]
    config = RasterAuditConfig(minimum_tolerant_f1=arguments.minimum_tolerant_f1)
    output_rows = []
    for identifier in identifiers:
        dxf_row, svg_row = dxf_rows[identifier], svg_rows[identifier]
        if dxf_row["source_sha256"] != svg_row["source_sha256"]:
            raise ValueError(f"source hash mismatch between renderers: {identifier}")
        dxf_item, svg_item = arguments.dxf_root / identifier, arguments.svg_root / identifier
        dxf_path = dxf_item / "source.dxf"
        first_png, second_png = dxf_item / "model.png", svg_item / "model.png"
        if sha256(dxf_path) != dxf_row["dxf_sha256"]:
            raise ValueError(f"DXF hash mismatch: {identifier}")
        if sha256(first_png) != dxf_row["png_sha256"] or sha256(second_png) != svg_row["png_sha256"]:
            raise ValueError(f"raster hash mismatch: {identifier}")
        probe, stdout, stderr = probe_librecad(
            arguments.librecad, dxf_path, environment, arguments.probe_timeout_seconds,
        )
        stdout_path = arguments.output_directory / f"{identifier}_librecad.stdout.log"
        stderr_path = arguments.output_directory / f"{identifier}_librecad.stderr.log"
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        probe["stdout_sha256"] = sha256(stdout_path)
        probe["stderr_sha256"] = sha256(stderr_path)
        comparison = compare_rasters(
            first_png, second_png,
            first_is_placeholder=bool(dxf_row.get("raster_is_placeholder", False)),
            second_is_placeholder=bool(svg_row.get("raster_is_placeholder", False)),
            config=config,
        )
        output_rows.append({
            "audit_schema_version": "cad_cross_renderer_audit_v002",
            "source_record_id": identifier,
            "source_sha256": dxf_row["source_sha256"],
            "dxf_manifest_sha256": sha256(arguments.dxf_manifest),
            "svg_manifest_sha256": sha256(arguments.svg_manifest),
            "dxf_sha256": sha256(dxf_path),
            "ezdxf_png_sha256": sha256(first_png),
            "libredwg_svg_png_sha256": sha256(second_png),
            "librecad_probe": probe,
            "cross_renderer_comparison": comparison,
            "human_visual_review_status": "not_reviewed",
            "font_correctness_status": "not_assessed",
            "privacy_review_status": "not_reviewed",
            "benchmark_eligible": False,
        })
        print(f"{identifier}: {comparison['status']}; LibreCAD={probe['status']}")
    manifest = arguments.output_directory / "renderer_audit_manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output_rows),
        encoding="utf-8",
    )
    status_counts: dict[str, int] = {}
    for row in output_rows:
        status = row["cross_renderer_comparison"]["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    summary = {
        "scope": "quarantined CAD technical renderer audit; not benchmark evidence",
        "items": len(output_rows),
        "audit_script_sha256": sha256(SCRIPT_PATH),
        "cross_renderer_status_counts": status_counts,
        "librecad_executable_sha256": sha256(arguments.librecad),
        "librecad_debian_package_version": debian_package_version(arguments.librecad),
        "librecad_help_returncode": help_result.returncode,
        "librecad_help_log_sha256": sha256(help_log),
        "librecad_advertised_export_flags": advertised_export_flags,
        "librecad_batch_export_capability": (
            "advertised_in_help" if advertised_export_flags else "not_advertised_in_help"
        ),
        "librecad_successful_exports": 0,
        "human_visual_reviews": 0,
        "font_correctness_reviews": 0,
        "privacy_reviews": 0,
        "benchmark_eligible_items": 0,
        "manifest_sha256": sha256(manifest),
        "warning": (
            "Raster nonblank/overlap checks and GUI startup probes do not establish visual "
            "fidelity, correct fonts, complete parsing, privacy clearance, or benchmark eligibility."
        ),
    }
    (arguments.output_directory / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
