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
