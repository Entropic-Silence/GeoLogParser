from geologparser.vlm.mineru_tables import decode_mineru_intervals


def test_decoder_uses_declared_top_bottom_columns_only():
    elements = [{
        "type": "table",
        "content": "<table><tr><td>Top ft</td><td>Bottom ft</td><td>Lithology</td></tr><tr><td>0</td><td>10</td><td>sand</td></tr><tr><td>10</td><td>25</td><td>clay</td></tr></table>",
    }]
    intervals, rejected, table_count = decode_mineru_intervals(elements, scale_to_m=0.3048)
    assert table_count == 1
    assert rejected == 0
    assert [(row["top_depth_m"], row["bottom_depth_m"]) for row in intervals] == [(0.0, 3.048), (3.048, 7.62)]


def test_decoder_rejects_unlabelled_or_invalid_numeric_rows():
    elements = [{
        "type": "table",
        "content": "<table><tr><td>Depth</td><td>Material</td></tr><tr><td>10</td><td>sand</td></tr></table><table><tr><td>From</td><td>To</td></tr><tr><td>10</td><td>9</td></tr></table>",
    }]
    intervals, rejected, table_count = decode_mineru_intervals(elements, scale_to_m=1.0)
    assert table_count == 2
    assert intervals == []
    assert rejected == 1
