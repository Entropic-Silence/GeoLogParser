#!/usr/bin/env python3
"""Inventory the licensed Mendeley DWG archive without extracting/rendering it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


def decode_zip_name(name: str, utf8_flag: bool) -> tuple[str, str]:
    """Recover the common GBK-in-ZIP legacy encoding without hiding uncertainty."""
    if utf8_flag:
        return name, "zip_utf8_flag"
    try:
        decoded = name.encode("cp437").decode("gb18030")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name, "zip_legacy_encoding_unresolved"
    return decoded, "cp437_bytes_decoded_as_gb18030"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    rows = []
    with ZipFile(arguments.archive) as archive:
        for archive_index, member in enumerate(archive.infolist()):
            if member.is_dir():
                continue
            data = archive.read(member)
            signature = data[:6].decode("ascii", errors="replace")
            if not signature.startswith("AC10"):
                raise ValueError(f"unexpected non-DWG signature for {member.filename}: {signature}")
            decoded_name, name_status = decode_zip_name(
                member.filename, bool(member.flag_bits & 0x800)
            )
            rows.append({
                "source_record_id": f"MENDELEY_DWG_{len(rows) + 1:03d}",
                "archive_index": archive_index,
                "archive_member_raw": member.filename,
                "archive_member_decoded": decoded_name,
                "archive_member_name_status": name_status,
                "source_group": decoded_name.split("/", 1)[0],
                "format": "dwg", "dwg_signature": signature,
                "size_bytes": member.file_size, "crc32": f"{member.CRC:08x}",
                "sha256": hashlib.sha256(data).hexdigest(),
                "license": "CC-BY-4.0", "source_dataset_doi": "10.17632/vcpz47r3sv.2",
                "annotation_status": "uninspected", "render_status": "not_rendered",
                "benchmark_eligible": False,
            })
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({"files": len(rows), "output": str(arguments.output)}))


if __name__ == "__main__":
    main()
