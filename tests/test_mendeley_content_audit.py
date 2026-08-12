import importlib.util


def _load_module(root):
    path = root / "scripts/audit_mendeley_dwg_content.py"
    spec = importlib.util.spec_from_file_location("audit_mendeley_dwg_content", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_iter_strings_and_risk_categories(request):
    module = _load_module(request.config.rootpath)
    values = list(module.iter_strings({"a": ["钻孔柱状图", {"b": "某某矿业公司"}], "n": 3}))
    assert values == ["钻孔柱状图", "某某矿业公司"]
    risks = module.category_counts(values, module.RISK_PATTERNS)
    domains = module.category_counts(values, module.DOMAIN_PATTERNS)
    assert risks["organization"] == 1
    assert domains["borehole_log"] == 1


def test_category_counts_count_strings_not_matches(request):
    module = _load_module(request.config.rootpath)
    counts = module.category_counts(["公司集团", "公司", "无"], module.RISK_PATTERNS)
    assert counts["organization"] == 2
