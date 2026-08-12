from geologparser.cad_svg import (
    audit_svg_geometry, entity_coverage, graphical_entities, write_review_png,
)


def test_graphical_entities_excludes_block_markers():
    payload = {"OBJECTS": [
        {"entity": "BLOCK", "index": 1}, {"entity": "TEXT", "index": 2},
        {"object": "LAYER", "index": 3}, {"entity": "ENDBLK", "index": 4},
    ]}
    assert [item["index"] for item in graphical_entities(payload)] == [2]


def test_unsupported_mtext_remains_an_explicit_missing_entity():
    entities = [{"entity": "MTEXT", "index": 7, "text": "地质描述"}]
    result = entity_coverage("<svg></svg>", entities)
    assert result["complete_entity_id_coverage"] is False
    assert result["missing_entity_type_counts"] == {"MTEXT": 1}


def test_coverage_reports_missing_types_and_extra_ids():
    entities = [{"entity": "TEXT", "index": 1}, {"entity": "LINE", "index": 2}]
    result = entity_coverage('<svg><g id="dwg-object-1"/><g id="dwg-object-9"/></svg>', entities)
    assert result["entity_coverage"] == 0.5
    assert result["missing_entity_type_counts"] == {"LINE": 1}
    assert result["extra_rendered_indexes"] == [9]


def test_svg_geometry_rejects_libredwg_sentinel_and_negative_extent():
    result = audit_svg_geometry(
        '<svg viewBox="1e20 1e20 -2e20 -2e20"></svg>'
    )
    assert result["geometry_sanity_passed"] is False
    assert result["failure_reasons"] == [
        "non_positive_viewbox_extent", "viewbox_exceeds_renderer_sanity_limit"
    ]


def test_svg_geometry_accepts_finite_positive_engineering_extents():
    result = audit_svg_geometry('<svg viewBox="-0.6 -878.85 208.5 903.45"></svg>')
    assert result["geometry_sanity_passed"] is True
    assert result["failure_reasons"] == []


def test_raster_audit_distinguishes_content_empty_and_invalid(tmp_path):
    content = write_review_png(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<path d="M 1,1 L 9,9" stroke="white"/></svg>',
        tmp_path / "content.png", 500,
    )
    assert content["raster_content_status"] == "nontransparent_content_detected_and_trimmed"
    assert content["raster_is_placeholder"] is False

    empty = write_review_png(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>',
        tmp_path / "empty.png", 500,
    )
    assert empty["raster_content_status"] == "transparent_or_empty_raster"
    assert empty["raster_is_placeholder"] is True

    invalid = write_review_png(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="1e20 1e20 -2e20 -2e20"></svg>',
        tmp_path / "invalid.png", 500,
    )
    assert invalid["raster_content_status"] == "not_attempted_invalid_svg_geometry"
    assert invalid["raster_is_placeholder"] is True
