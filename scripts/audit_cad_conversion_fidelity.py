#!/usr/bin/env python3
"""Reconcile quarantined source-DWG and derivative-DXF entity inventories."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from geologparser.cad_fidelity import (
    compare_inventories, inventory_from_entities, public_inventory,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_inventory(
    dwg_path: Path, dwgread: Path, environment: dict[str, str], temporary_root: Path,
) -> tuple[dict[str, Any], str]:
    with tempfile.TemporaryDirectory(dir=temporary_root, prefix="fidelity_") as directory:
        json_path = Path(directory) / "source.min.json"
        result = subprocess.run(
            [str(dwgread), "-O", "minJSON", "-o", str(json_path), str(dwg_path)],
            capture_output=True, text=True, env=environment,
        )
        if result.returncode != 0 or not json_path.is_file():
            raise RuntimeError(f"dwgread inventory failed for {dwg_path}: {result.stderr}")
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        diagnostic = "\n".join(part for part in (result.stdout, result.stderr) if part)
    # LibreDWG OBJECTS mixes graphical entities with dictionaries, styles,
    # layers, and other database objects.  DXF modelspace contains only the
    # former, so compare the same semantic population on both sides.
    graphical_entities = [item for item in payload.get("OBJECTS", ()) if item.get("entity")]
    return inventory_from_entities(graphical_entities), diagnostic


def dxf_inventory(dxf_path: Path) -> dict[str, Any]:
    import ezdxf

    document = ezdxf.readfile(dxf_path)
    entities = []
    for entity in document.modelspace():
        entity_type = entity.dxftype()
        text = ""
        if entity_type in {"TEXT", "ATTRIB", "ATTDEF"}:
            text = entity.dxf.text
        elif entity_type == "MTEXT":
            text = entity.text
        entities.append({
            "type": entity_type,
            "handle": entity.dxf.get("handle"),
            "text": text,
        })
    return inventory_from_entities(entities)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("derivative_manifest", type=Path)
    parser.add_argument("derivative_root", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("dwgread", type=Path)
    parser.add_argument("--library-dir", type=Path)
    arguments = parser.parse_args()
    if arguments.output_directory.exists():
        raise FileExistsError(f"output directory already exists: {arguments.output_directory}")
    rows = [
        json.loads(line) for line in arguments.derivative_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError("derivative manifest is empty")
    environment = os.environ.copy()
    if arguments.library_dir:
        existing = environment.get("LD_LIBRARY_PATH")
        environment["LD_LIBRARY_PATH"] = str(arguments.library_dir) + (
            f":{existing}" if existing else ""
        )
    version = subprocess.run(
        [str(arguments.dwgread), "--version"], capture_output=True, text=True,
        check=True, env=environment,
    )
    converter_version = (version.stdout or version.stderr).strip()
    arguments.output_directory.mkdir(parents=True)
    output_rows = []
    for row in rows:
        identifier = str(row["source_record_id"])
        item_root = arguments.derivative_root / identifier
        dwg_path, dxf_path = item_root / "source.dwg", item_root / "source.dxf"
        if sha256(dwg_path) != row["source_sha256"] or sha256(dxf_path) != row["dxf_sha256"]:
            raise ValueError(f"source/derivative hash mismatch: {identifier}")
        source, diagnostic = source_inventory(
            dwg_path, arguments.dwgread, environment, arguments.output_directory,
        )
        derivative = dxf_inventory(dxf_path)
        comparison = compare_inventories(source, derivative)
        output_rows.append({
            "fidelity_schema_version": "cad_conversion_fidelity_v001",
            "source_record_id": identifier,
            "source_sha256": row["source_sha256"],
            "dxf_sha256": row["dxf_sha256"],
            "derivative_manifest_sha256": sha256(arguments.derivative_manifest),
            "dwgread_version": converter_version,
            "dwgread_executable_sha256": sha256(arguments.dwgread),
            "dwgread_diagnostic_sha256": hashlib.sha256(diagnostic.encode("utf-8")).hexdigest(),
            "source_inventory": public_inventory(source),
            "derivative_inventory": public_inventory(derivative),
            "comparison": comparison,
            "human_visual_review_status": "not_reviewed",
            "privacy_review_status": "not_reviewed",
            "benchmark_eligible": False,
        })
        print(f"{identifier}: {comparison['status']}")
    manifest = arguments.output_directory / "fidelity_manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output_rows),
        encoding="utf-8",
    )
    summary = {
        "scope": "automated DWG-to-DXF structural/text inventory reconciliation only",
        "items": len(output_rows),
        "structural_inventory_matches": sum(
            row["comparison"]["structural_inventory_match"] for row in output_rows
        ),
        "structural_inventory_mismatches": sum(
            not row["comparison"]["structural_inventory_match"] for row in output_rows
        ),
        "human_visual_reviews": 0,
        "privacy_reviews": 0,
        "benchmark_eligible_items": 0,
        "fidelity_manifest_sha256": sha256(manifest),
        "warning": (
            "Inventory agreement does not establish pixel fidelity, privacy clearance, "
            "rights clearance, Ground Truth, or benchmark eligibility."
        ),
    }
    (arguments.output_directory / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
