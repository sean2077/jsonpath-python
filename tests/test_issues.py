import pytest

from jsonpath import JSONPath, JSONPathTypeError


def test_issue_17():
    data = [
        {"time": "2023-01-02T20:32:01Z", "user": "user1"},
        {"time": "2023-01-02T20:32:03Z", "user": "user2"},
        {"time": "2023-01-02T20:32:03Z", "user": "user1"},
    ]
    user = "user1"
    expr = f'$.[?(@.user=="{user}")]'
    result = JSONPath(expr).parse(data)
    assert len(result) == 2
    assert result[0]["user"] == "user1"
    assert result[1]["user"] == "user1"


def test_issue_17_bracket_dot_normalization():
    data = {"store": "book"}
    # Case 1: Standard bracket notation
    assert JSONPath("$['store']").parse(data) == ["book"]
    # Case 2: Dot followed by bracket (should be normalized to bracket)
    assert JSONPath("$.['store']").parse(data) == ["book"]
    # Case 3: Recursive descent with bracket (should NOT be normalized)
    data_recursive = {"a": {"store": "book"}, "b": {"store": "paper"}}
    # $..['store'] should find all 'store' keys
    assert sorted(JSONPath("$..['store']").parse(data_recursive)) == ["book", "paper"]


def test_issue_16_quoted_keys():
    data = {"user-list": [{"city-name": "Austin", "name": "John"}, {"city-name": "New York", "name": "Jane"}]}

    # Case 1: Key with hyphen in the path
    assert JSONPath("$.'user-list'").parse(data) == [
        [{"city-name": "Austin", "name": "John"}, {"city-name": "New York", "name": "Jane"}]
    ]

    # Case 2: Key with hyphen in a filter (single quotes)
    assert JSONPath("$.'user-list'[?(@.'city-name'=='Austin')]").parse(data) == [
        {"city-name": "Austin", "name": "John"}
    ]

    # Case 3: Key with hyphen in a filter (double quotes)
    assert JSONPath('$.\'user-list\'[?(@."city-name"=="Austin")]').parse(data) == [
        {"city-name": "Austin", "name": "John"}
    ]


def test_issue_15_bracket_notation_in_filter():
    data = {
        "tool": {
            "books": [
                {"properties": [{"name": "moq", "value": "x"}, {"name": "url", "value": "1"}]},
                {"properties": [{"name": "url", "value": "3"}]},
                {"properties": [{"name": "moq", "value": "q"}, {"name": "url", "value": "4"}]},
            ]
        }
    }

    # Case 1: Bracket notation in filter
    expr = "$['tool']['books'][*]['properties'][*][?(@['name'] == 'moq')]['value']"
    assert JSONPath(expr).parse(data) == ["x", "q"]

    # Case 2: Dot notation in filter (already working, but good to keep)
    expr_dot = "$.tool.books.[*].properties.[*].[?(@.name=='moq')].value"
    assert JSONPath(expr_dot).parse(data) == ["x", "q"]


def test_issue_10_mixed_type_sorting():
    # Case 1: Mixed types (int and str) - Should raise JSONPathTypeError
    data1 = [{"code": "N"}, {"code": 0}]
    with pytest.raises(JSONPathTypeError):
        JSONPath("$./(code)").parse(data1)

    # Case 2: Numbers (numerical sort)
    data2 = [{"code": 10}, {"code": 2}]
    result2 = JSONPath("$./(code)").parse(data2)
    assert result2 == [{"code": 2}, {"code": 10}]

    # Case 3: Strings (lexicographical sort)
    data3 = [{"code": "b"}, {"code": "a"}]
    result3 = JSONPath("$./(code)").parse(data3)
    assert result3 == [{"code": "a"}, {"code": "b"}]

    # Case 4: Strings that look like numbers (converted to numbers by _getattr)
    data4 = [{"code": "10"}, {"code": "2"}]
    result4 = JSONPath("$./(code)").parse(data4)
    # "2" -> 2, "10" -> 10. 2 < 10.
    assert result4 == [{"code": "2"}, {"code": "10"}]

    # Case 5: Mixed numbers and strings that look like numbers
    data5 = [{"code": 10}, {"code": "2"}]
    result5 = JSONPath("$./(code)").parse(data5)
    # "2" -> 2. 2 < 10.
    assert result5 == [{"code": "2"}, {"code": 10}]

    # Case 6: Missing keys (None)
    # None vs int comparison in Python 3 raises TypeError
    data6 = [{"code": 1}, {"other": 2}]
    with pytest.raises(JSONPathTypeError):
        JSONPath("$./(code)").parse(data6)
