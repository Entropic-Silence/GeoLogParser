from geologparser.datasets.swissgeol import choose_interval_section, explicit_interval_sections


def test_explicit_range_table_and_ocr_one_normalization():
    text = "Bis Tiefe Beschreibung\n0-lm Ueberlagerung\nl-26m Moraene\n26-144m Molasse\n144-180m Sandstein\nGrundwasser"
    assert choose_interval_section(text, 180) == [(0.0, 1.0), (1.0, 26.0), (26.0, 144.0), (144.0, 180.0)]


def test_boundary_only_table_becomes_contiguous_intervals():
    text = "Tiefe Beschreibung des Bohrgutes\nbis m Art Eigenschaften\n40 Kies\n100 Mergel\n180 Sandstein\nBohrkote"
    assert explicit_interval_sections(text, 180) == [[(0.0, 40.0), (40.0, 100.0), (100.0, 180.0)]]


def test_ocr_tiefem_header_parses_without_reference_final_depth():
    text = (
        "Tiefem Beschreibung des Bohrgutes / Schichtenverzeichnis\n"
        "bis Art, Eigenschaften Farbe\n"
        "50m Kies Moraene Lehm\n"
        "160m Mergel Sandstein\n"
        "Bohrkote"
    )
    assert choose_interval_section(text) == [(0.0, 50.0), (50.0, 160.0)]


def test_relaxed_roi_header_and_table_border_parse_ranges():
    text = (
        "Bis Tief Basaran dew Balewut\n"
        "}0- 8 | Kies Lehm\n"
        "8 - 140 | Sandstein Mergel\n"
        "Beschreibung des Bohrgutes / Schichtenverzeichnis\n"
    )
    assert choose_interval_section(text) == [(0.0, 8.0), (8.0, 140.0)]


def test_description_only_roi_header_is_sufficient():
    text = (
        "Beschreibung des Bohrgutes / Schichtenverzeichnis\n"
        "bis Art, Eigenschaften\n"
        "0-20m Moraene\n"
        "20-125m Mergel und Sandstein\n"
    )
    assert choose_interval_section(text) == [(0.0, 20.0), (20.0, 125.0)]


def test_parses_ocr_table_underscores_after_boundary_values():
    text = (
        "Tiefe Beschreibung Bohrgut\n"
        "bis m Eigenschaften\n"
        "6 _|Ueberlagerung\n"
        "_10___|Mergel teilweise verwittert\n"
        "_200__|Mergel und Sandstein\n"
    )
    assert choose_interval_section(text) == [
        (0.0, 6.0), (6.0, 10.0), (10.0, 200.0),
    ]


def test_normalizes_letter_o_as_zero_in_explicit_leading_range():
    text = (
        "Tiefe Beschreibung des Bohrgutes\n"
        "von / bis Eigenschaften\n"
        "Om-20m sand kies moraene\n"
        "20m-160m mergel\n"
    )
    assert choose_interval_section(text) == [(0.0, 20.0), (20.0, 160.0)]
