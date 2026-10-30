import pytest

from jsonpath_rw import parse


@pytest.mark.parametrize("data, expected", [
    (
        {"list": [{"amount": 1}], "tuple": ({"amount": 2},)},
        [("list.[0].amount", 1), ("tuple.[0].amount", 2)],
    ),
    (
        ({"amount": 3},),
        [("[0].amount", 3)],
    ),
    (
        {"items": (({"amount": 4},), [{"amount": 5}])},
        [("items.[0].[0].amount", 4), ("items.[1].[0].amount", 5)],
    ),
    (
        [({"amount": 6},), {"amount": 7}],
        [("[0].[0].amount", 6), ("[1].amount", 7)],
    ),
    (
        ((), None, "amount", 8),
        [],
    ),
])
def test_recursive_field_lookup_traverses_tuples(data, expected):
    matches = parse("$..amount").find(data)

    assert sorted((str(match.full_path), match.value) for match in matches) == expected
    for match in matches:
        assert [result.value for result in match.full_path.find(data)] == [match.value]
