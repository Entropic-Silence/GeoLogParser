import importlib.util
from pathlib import Path
from zipfile import ZipFile


def module(root):
    path = root / "scripts/build_unipd_location_manifest.py"
    spec = importlib.util.spec_from_file_location("build_unipd_location_manifest", path)
    value = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(value)
    return value


def test_canonical_id_removes_numeric_zero_padding(request):
    value = module(request.config.rootpath)
    assert value.canonical_id("TS06") == "TS6"
    assert value.canonical_id("tps007") == "TPS7"


def test_parse_kmz_preserves_raw_id_and_lon_lat(tmp_path, request):
    value = module(request.config.rootpath)
    kmz = tmp_path / "locations.kmz"
    kml = """<?xml version='1.0'?>
    <kml xmlns='http://www.opengis.net/kml/2.2'><Document><Placemark>
    <name>TS06</name><Point><coordinates>12.5,45.5,0</coordinates></Point>
    </Placemark></Document></kml>"""
    with ZipFile(kmz, "w") as archive:
        archive.writestr("doc.kml", kml)
    assert value.parse_kmz(kmz) == [{
        "source_id_raw": "TS06", "source_id_canonical": "TS6",
        "longitude": 12.5, "latitude": 45.5, "altitude": 0.0,
    }]
