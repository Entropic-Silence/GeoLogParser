from geologparser.cad_fidelity import compare_inventories, inventory_from_entities, public_inventory


def entities(text="粉质黏土"):
    return [
        {"entity": "BLOCK", "handle": [0, 1, 1]},
        {"entity": "TEXT", "handle": [0, 1, 16], "text_value": text},
        {"entity": "LINE", "handle": [0, 1, 17]},
        {"entity": "ENDBLK", "handle": [0, 1, 18]},
    ]


def test_exact_entity_text_and_handle_inventory_matches():
    source = inventory_from_entities(entities())
    derivative = inventory_from_entities([
        {"type": "TEXT", "handle": "10", "text": "粉质黏土"},
        {"type": "LINE", "handle": "11"},
    ])
    result = compare_inventories(source, derivative)
    assert result["status"] == "structural_inventory_match"
    assert result["shared_handle_count"] == 2
    assert result["ordered_text_sha256_match"] is True


def test_same_count_but_changed_text_is_a_mismatch():
    result = compare_inventories(
        inventory_from_entities(entities()), inventory_from_entities(entities("粉土")),
    )
    assert result["structural_inventory_match"] is False
    assert result["ordered_text_sha256_match"] is False


def test_public_inventory_does_not_disclose_raw_text_or_handles():
    value = public_inventory(inventory_from_entities(entities()))
    assert "texts" not in value
    assert "handles" not in value
    assert value["text_entity_count"] == 1


def test_numeric_object_type_is_not_an_entity_name():
    # Callers must filter LibreDWG database objects before comparison.  The
    # inventory itself also refuses a numeric-only type to avoid accidental
    # style/dictionary inflation.
    value = inventory_from_entities([{"type": 48, "handle": [0, 1, 1]}])
    assert value["entity_count"] == 0
