from jsonpath_rw import parse


def test_wildcard_on_null_field_returns_no_matches():
    query = parse("$.key[*]")
    try:
        matches = query.find({"key": None})
    except TypeError as error:
        raise AssertionError("Expected no matches for a null field, got %s" % error)

    assert matches == []
