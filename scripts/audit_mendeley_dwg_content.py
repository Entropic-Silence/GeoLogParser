#!/usr/bin/env python3
"""Pre-screen quarantined DWGs for Chinese text and disclosure-risk categories.

This is an automatic acquisition audit, not a visual review, annotation, or
benchmark eligibility decision. Raw extracted text stays outside the Git repo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from typing import Any, Iterable
from zipfile import ZipFile


RISK_PATTERNS = {
    "organization": re.compile(r"公司|集团|研究院|勘察院|煤业|矿业"),
    "named_location_or_project": re.compile(r"项目|工程|矿区|井田|煤田|地址"),
    "contact_information": re.compile(r"电话|手机|邮箱|电子邮件"),
    "person_or_approval_role": re.compile(r"总工程师|负责人|制图|审核|校核|批准"),
    "coordinate_or_location_field": re.compile(r"坐标|经度|纬度|高程"),
}
DOMAIN_PATTERNS = {
    "borehole_log": re.compile(r"钻孔|柱状图"),
    "geological_description": re.compile(r"粘土|黏土|砂岩|泥岩|风化|地层|岩性"),
}
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)


def category_counts(strings: list[str], patterns: dict[str, re.Pattern[str]]) -> dict[str, int]:
    return {name: sum(bool(pattern.search(text)) for text in strings) for name, pattern in patterns.items()}


def tool_version(executable: Path, environment: dict[str, str]) -> str:
    result = subprocess.run(
        [str(executable), "--version"], check=True, capture_output=True, text=True,
        env=environment,
    )
    return (result.stdout or result.stderr).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("dwgread", type=Path)
    parser.add_argument("--library-dir", type=Path)
    arguments = parser.parse_args()

    environment = os.environ.copy()
    if arguments.library_dir:
        previous = environment.get("LD_LIBRARY_PATH")
        environment["LD_LIBRARY_PATH"] = str(arguments.library_dir) + (f":{previous}" if previous else "")
    version = tool_version(arguments.dwgread, environment)
    executable_sha256 = hashlib.sha256(arguments.dwgread.read_bytes()).hexdigest()
    source_rows = [json.loads(line) for line in arguments.source_manifest.read_text(encoding="utf-8").splitlines()]
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = arguments.output_dir / "content_audit_manifest.jsonl"
    summary_path = arguments.output_dir / "content_audit_summary.json"
    audit_rows = []

    with ZipFile(arguments.archive) as archive:
        members = archive.infolist()
        for source in source_rows:
            started = time.perf_counter()
            member = members[source["archive_index"]]
            data = archive.read(member)
            if hashlib.sha256(data).hexdigest() != source["sha256"]:
                raise ValueError(f"source hash mismatch: {source['source_record_id']}")
            with tempfile.TemporaryDirectory(dir=arguments.output_dir, prefix="dwg_audit_") as temporary:
                temporary_path = Path(temporary)
                dwg_path = temporary_path / "source.dwg"
                json_path = temporary_path / "content.min.json"
                dwg_path.write_bytes(data)
                result = subprocess.run(
                    [str(arguments.dwgread), "-O", "minJSON", "-o", str(json_path), str(dwg_path)],
                    capture_output=True, text=True, env=environment,
                )
                if result.returncode == 0 and json_path.exists():
                    payload = json.loads(json_path.read_text(encoding="utf-8"))
                    strings = list(iter_strings(payload))
                    han_strings = [value for value in strings if HAN.search(value)]
                    text_sha256 = hashlib.sha256("\n".join(strings).encode("utf-8")).hexdigest()
                    status = "automatic_prescreen_completed"
                else:
                    strings, han_strings = [], []
                    text_sha256 = None
                    status = "conversion_failed"
                diagnostic = "\n".join(part for part in (result.stdout, result.stderr) if part)
                audit_rows.append({
                    "source_record_id": source["source_record_id"],
                    "source_sha256": source["sha256"],
                    "audit_status": status,
                    "human_visual_review_status": "not_reviewed",
                    "benchmark_eligible": False,
                    "converter": version,
                    "converter_executable_sha256": executable_sha256,
                    "converter_returncode": result.returncode,
                    "converter_reported_ignored_mtext": "MTEXT ignored" in diagnostic,
                    "conversion_may_be_incomplete": "ignored" in diagnostic.lower(),
                    "extracted_string_count": len(strings),
                    "han_string_count": len(han_strings),
                    "extracted_text_sha256": text_sha256,
                    "domain_signal_counts": category_counts(strings, DOMAIN_PATTERNS),
                    "risk_signal_counts": category_counts(strings, RISK_PATTERNS),
                    "automatic_risk_flag": any(category_counts(strings, RISK_PATTERNS).values()),
                    "elapsed_seconds": time.perf_counter() - started,
                })
                print(f"{len(audit_rows)}/{len(source_rows)} {source['source_record_id']} {status}")

    audit_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in audit_rows),
        encoding="utf-8",
    )
    summary = {
        "scope": "automatic DWG content/risk pre-screen; not human review or benchmark evidence",
        "items": len(audit_rows),
        "completed": sum(row["audit_status"] == "automatic_prescreen_completed" for row in audit_rows),
        "conversion_failures": sum(row["audit_status"] == "conversion_failed" for row in audit_rows),
        "items_with_han_text": sum(row["han_string_count"] > 0 for row in audit_rows),
        "items_with_automatic_risk_flag": sum(row["automatic_risk_flag"] for row in audit_rows),
        "items_with_ignored_mtext": sum(row["converter_reported_ignored_mtext"] for row in audit_rows),
        "human_visual_reviews": 0,
        "benchmark_eligible_items": 0,
        "source_manifest_sha256": hashlib.sha256(arguments.source_manifest.read_bytes()).hexdigest(),
        "audit_manifest_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        "converter": version,
        "converter_executable_sha256": executable_sha256,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary_path)


if __name__ == "__main__":
    main()
