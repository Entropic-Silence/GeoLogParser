import importlib.util


def load_script(root):
    path = root / "scripts/audit_priority_cad_renderers.py"
    spec = importlib.util.spec_from_file_location("audit_priority_cad_renderers", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_manifest_reader_rejects_duplicate_ids(tmp_path, request):
    module = load_script(request.config.rootpath)
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        '{"source_record_id": "A"}\n{"source_record_id": "A"}\n', encoding="utf-8",
    )
    try:
        module.read_manifest(manifest)
    except ValueError as error:
        assert "duplicate source_record_id" in str(error)
    else:
        raise AssertionError("duplicate IDs were accepted")


def test_sha256_is_content_hash(tmp_path, request):
    module = load_script(request.config.rootpath)
    value = tmp_path / "value"
    value.write_bytes(b"abc")
    assert module.sha256(value) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_debian_package_version_is_recordable(monkeypatch, request):
    from pathlib import Path
    from subprocess import CompletedProcess

    module = load_script(request.config.rootpath)
    responses = iter([
        CompletedProcess([], 0, "librecad: /usr/bin/librecad\n", ""),
        CompletedProcess([], 0, "2.1.3-3", ""),
    ])
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: next(responses))
    assert module.debian_package_version(Path("/usr/bin/librecad")) == "2.1.3-3"
