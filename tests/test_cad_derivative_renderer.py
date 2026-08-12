import importlib.util
from pathlib import Path


def _load_module(root):
    path = root / "scripts/render_mendeley_dwg_derivatives.py"
    spec = importlib.util.spec_from_file_location("render_mendeley_dwg_derivatives", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sha256_is_file_content_hash(tmp_path, request):
    module = _load_module(request.config.rootpath)
    path = tmp_path / "value"
    path.write_bytes(b"abc")
    assert module.sha256(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_package_versions_are_resolved(request):
    module = _load_module(request.config.rootpath)
    assert module.package_version("ezdxf") == "1.4.3"
    assert module.package_version("matplotlib") == "3.10.5"
