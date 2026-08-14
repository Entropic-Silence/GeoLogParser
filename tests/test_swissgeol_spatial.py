from geologparser.extraction.swissgeol_spatial import parse_swissgeol_spatial_text


def test_parses_common_lv95_grouping_styles():
    examples = {
        "Koordinaten X 2725213 / Y l 270 690": (2725213, 1270690),
        "Koordinaten: 2'740'719-1'269'290": (2740719, 1269290),
        "Koordinaten: 2.708 812 /1.268 012": (2708812, 1268012),
        "Koordinaten: 2 735 426 ,1 272 788": (2735426, 1272788),
        "Koordinaten 2’714’203 1’262’506": (2714203, 1262506),
    }
    for text, expected in examples.items():
        prediction = parse_swissgeol_spatial_text(text)
        assert (prediction.x_coordinate, prediction.y_coordinate) == expected
        assert prediction.coordinate_status == "EXTRACTED_UNAMBIGUOUS"


def test_ignores_date_numbers_before_coordinate_label():
    prediction = parse_swissgeol_spatial_text(
        "Bohrbeginn: 22.09.2022 Ende: 26.09.2022 Koordinaten: 2 737 104 / 1 265 221"
    )
    assert (prediction.x_coordinate, prediction.y_coordinate) == (2737104, 1265221)


def test_abstains_when_page_contains_two_distinct_pairs():
    prediction = parse_swissgeol_spatial_text(
        "Koordinaten 2'709'439 / 1'268'604\n"
        "Koordinaten 2 709 567 / 1 268 576"
    )
    assert prediction.x_coordinate is None
    assert prediction.coordinate_candidate_count == 2
    assert prediction.coordinate_status == "ABSTAIN_AMBIGUOUS_MULTIPLE_COORDINATES"


def test_collar_parser_distinguishes_value_from_tolerance():
    explicit = parse_swissgeol_spatial_text("Bohrkote: 406,0 ± 0.5m")
    assert explicit.collar_elevation_m == 406.0
    tolerance_only = parse_swissgeol_spatial_text("Bohrkote: ± 0.5m")
    assert tolerance_only.collar_elevation_m is None
    assert tolerance_only.collar_status == "ABSTAIN_NO_EXPLICIT_ELEVATION"


def test_absent_spatial_metadata_is_an_explicit_abstention():
    prediction = parse_swissgeol_spatial_text("Tiefe Beschreibung Endteufe 100 m")
    assert prediction.coordinate_status == "ABSTAIN_NO_COORDINATE_PAIR"
    assert prediction.collar_status == "ABSTAIN_NO_EXPLICIT_ELEVATION"
