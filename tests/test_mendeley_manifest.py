from zipfile import ZipFile

import json
import subprocess
import sys
import importlib.util


def _load_manifest_module(root):
    path = root / "scripts/build_mendeley_dwg_manifest.py"
    spec = importlib.util.spec_from_file_location("build_mendeley_dwg_manifest", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_mendeley_manifest_keeps_legacy_name_and_hashes_dwg(tmp_path, request):
    archive = tmp_path / "logs.zip"
    with ZipFile(archive, "w") as output:
        output.writestr("group/BH1.dwg", b"AC1021" + b"fixture")
    manifest = tmp_path / "manifest.jsonl"
    subprocess.run([
        sys.executable, str(request.config.rootpath / "scripts/build_mendeley_dwg_manifest.py"),
        str(archive), str(manifest),
    ], check=True)
    row = json.loads(manifest.read_text(encoding="utf-8"))
    assert row["dwg_signature"] == "AC1021"
    assert row["archive_member_decoded"] == "group/BH1.dwg"
    assert row["benchmark_eligible"] is False
    assert len(row["sha256"]) == 64


def test_mendeley_manifest_decodes_gbk_legacy_zip_name(request):
    decode_zip_name = _load_manifest_module(request.config.rootpath).decode_zip_name
    chinese_name = "1.YPH/10检1（200柱状）.dwg"
    mojibake_name = chinese_name.encode("gbk").decode("cp437")
    decoded, status = decode_zip_name(mojibake_name, utf8_flag=False)
    assert decoded == chinese_name
    assert status == "cp437_bytes_decoded_as_gb18030"
