import pytest

from jsonpath_rw import parse
from jsonpath_rw.jsonpath import Child, Fields, Root


@pytest.mark.parametrize(
    "field",
    ["derp.herp", "two words", "where", "", "a,b", "x[y]",
     "x'y", "x\\y", "caf\u00e9", "line\nbreak"],
)
def test_quoted_field_names_survive_string_round_trip(field):
    path = Child(Root(), Fields(field))
    error = None
    restored = None
    try:
        restored = parse(str(path))
    except Exception as caught:
        error = caught

    assert error is None, "A printed field name must remain valid JSONPath"
    assert restored == path, "Printing a field must preserve its literal name"
    assert [match.value for match in restored.find({field: 42})] == [42]


def test_quoted_dotted_key_is_distinct_from_nested_path():
    dotted = parse('$.foo."derp.herp"')
    nested = parse('$.foo.derp.herp')

    assert str(dotted) != str(nested)
    assert parse(str(dotted)) == dotted


@pytest.mark.parametrize("field", ["foo", "_foo", "@foo", "foo-bar", "foo42", "*", "123", "-1"])
def test_simple_field_rendering_remains_unchanged(field):
    assert str(Fields(field)) == field


def test_multiple_field_selectors_keep_literal_names():
    path = Fields("plain", "with.dot", "where")
    error = None
    restored = None
    try:
        restored = parse(str(path))
    except Exception as caught:
        error = caught

    assert error is None
    assert restored == path
    assert [match.value for match in restored.find(
        {"plain": 1, "with.dot": 2, "where": 3}
    )] == [1, 2, 3]
