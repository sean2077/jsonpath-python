from jsonpath import JSONPath


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
