import pytest

from jsonpath import JSONPath, JSONPathTypeError


class TestIssue21Security:
    """Issue #21: CVE - Remote Code Execution via eval() in filter expressions."""

    def test_import_blocked(self):
        """__import__() calls in filter expressions should be blocked."""
        data = {"users": [{"name": "Alice"}]}
        result = JSONPath('$.users[?(__import__("os"))]').parse(data)
        assert result == []

    def test_os_system_blocked(self):
        """os.system() calls via __import__ should be blocked."""
        data = {"users": [{"name": "Alice"}]}
        result = JSONPath('$.users[?(__import__("os").system("echo PWNED"))]').parse(data)
        assert result == []

    def test_builtins_open_blocked(self):
        """open() calls should be blocked."""
        data = {"users": [{"name": "Alice"}]}
        result = JSONPath('$.users[?(__import__("builtins").open("/etc/passwd"))]').parse(data)
        assert result == []

    def test_type_function_blocked(self):
        """type() calls should be blocked."""
        data = {"users": [{"name": "Alice"}]}
        result = JSONPath("$.users[?(type(__obj) == dict)]").parse(data)
        assert result == []

    def test_dunder_attribute_blocked(self):
        """Access to __class__, __bases__, etc. should be blocked."""
        data = {"users": [{"name": "Alice"}]}
        result = JSONPath("$.users[?(@.__class__)]").parse(data)
        assert result == []

    def test_class_subclasses_blocked(self):
        """Sandbox escape via __class__.__subclasses__ should be blocked."""
        data = [1, 2, 3]
        result = JSONPath("$[?(@.__class__.__bases__[0].__subclasses__())]").parse(data)
        assert result == []

    def test_legitimate_filters_still_work(self):
        """Normal filter operations should still work after security fix."""
        data = {"items": [{"v": 1}, {"v": 2}, {"v": 3}]}
        assert JSONPath("$.items[?(@.v > 1)].v").parse(data) == [2, 3]
        assert JSONPath("$.items[?(@.v == 2)].v").parse(data) == [2]
        assert JSONPath("$.items[?(@.v >= 1 and @.v <= 2)].v").parse(data) == [1, 2]

    def test_len_allowed(self):
        """len() should still be allowed in filter expressions."""
        data = {"items": [{"tags": ["a", "b"]}, {"tags": ["c"]}]}
        assert JSONPath("$.items[?(len(@.tags) > 1)]").parse(data) == [{"tags": ["a", "b"]}]

    def test_regex_still_works(self):
        """Regex matching should still work after security fix."""
        data = {"items": [{"name": "apple"}, {"name": "banana"}]}
        assert JSONPath("$.items[?(@.name =~ /^app/)].name").parse(data) == ["apple"]

    def test_custom_eval_func_opt_in(self):
        """Users can opt in to custom eval via eval_func parameter."""
        data = {"items": [{"v": 1}, {"v": 2}]}
        jp = JSONPath("$.items[?(@.v > 0)]")

        calls = []

        def custom_eval_fn(expr, *args, **kwargs):  # noqa: S307
            calls.append(expr)
            return __builtins__["eval"](expr, *args, **kwargs)  # noqa: S307

        result = jp.parse(data, eval_func=custom_eval_fn)
        assert len(result) == 2
        assert len(calls) > 0


class TestIssue20BareAtFilter:
    """Issue #20: Filtering primitive arrays with bare @ reference."""

    def test_bare_at_string_equality(self):
        """$.tags[?(@ == 'web')] should work on string arrays."""
        data = {"tags": ["web", "test2"]}
        assert JSONPath("$.tags[?(@ == 'web')]").parse(data) == ["web"]

    def test_bare_at_numeric_comparison(self):
        """Bare @ should work for numeric comparisons."""
        data = {"nums": [1, 5, 10, 15]}
        assert JSONPath("$.nums[?(@ > 5)]").parse(data) == [10, 15]
        assert JSONPath("$.nums[?(@ >= 10)]").parse(data) == [10, 15]
        assert JSONPath("$.nums[?(@ == 5)]").parse(data) == [5]

    def test_bare_at_regex(self):
        """Bare @ should work with regex matching."""
        data = {"tags": ["web", "owasp:software_and_data_integrity_failures"]}
        assert JSONPath("$.tags[?(@ =~ /owasp:.+/)]").parse(data) == ["owasp:software_and_data_integrity_failures"]

    def test_bare_at_in_operator(self):
        """Bare @ with 'in' operator."""
        data = {"items": ["apple", "banana", "cherry"]}
        assert JSONPath("$.items[?('an' in @)]").parse(data) == ["banana"]

    def test_bare_at_on_root_array(self):
        """Bare @ on a root-level array."""
        data = [1, 2, 3, 4, 5]
        assert JSONPath("$[?(@ > 3)]").parse(data) == [4, 5]

    def test_bare_at_does_not_affect_dotted_access(self):
        """Dotted @ access should still work as before."""
        data = {"items": [{"v": 1}, {"v": 2}, {"v": 3}]}
        assert JSONPath("$.items[?(@.v > 1)].v").parse(data) == [2, 3]


class TestIssue19KeyExistence:
    """Issue #19: Key existence check works via truthiness."""

    def test_key_existence_with_and(self):
        data = [
            {"id": "room1", "type": "HotelRoom", "temperature": {"type": "Number"}},
            {"id": "room2", "type": "HotelRoom", "co2": {"type": "Number"}},
        ]
        result = JSONPath('$[?(@.type == "HotelRoom" and @.co2)]').parse(data)
        assert len(result) == 1
        assert result[0]["id"] == "room2"

    def test_key_existence_simple(self):
        data = [{"a": 1, "b": 2}, {"a": 3}]
        result = JSONPath("$[?(@.b)]").parse(data)
        assert result == [{"a": 1, "b": 2}]


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


def test_issue_9_filter_nulls_in_field_extractor():
    data = [
        {
            "author": [
                {"fullname": "some fullname", "rank": 3},
                {
                    "fullname": "other fullname",
                    "pid": {
                        "id": {"scheme": "orcid", "value": "0000-0000-0000-0000"},
                        "provenance": {"provenance": "Harvested", "trust": "0.91"},
                    },
                    "rank": 4,
                },
            ]
        }
    ]

    expr = "$.*.author[*].(fullname,pid.id.value,pid.id.scheme)"
    result = JSONPath(expr).parse(data)

    # First item should only have fullname, as pid.id... are missing
    assert result[0] == {"fullname": "some fullname"}

    # Second item should have all fields
    assert result[1] == {"fullname": "other fullname", "pid.id.value": "0000-0000-0000-0000", "pid.id.scheme": "orcid"}


def test_sorting_with_missing_keys():
    # Verify that missing keys are treated as None during sort (and thus come first or raise error if mixed)
    # Case 1: Missing keys vs Integers
    # None vs Int -> TypeError in Python 3. So this should raise JSONPathTypeError
    data = [{"val": 10}, {"other": 5}]  # second item has missing "val" -> None

    with pytest.raises(JSONPathTypeError):
        JSONPath("$./(val)").parse(data)

    # Case 2: All missing keys (all None) -> Should raise JSONPathTypeError because None < None is not supported in Python 3
    data2 = [{"other": 1}, {"other": 2}]
    with pytest.raises(JSONPathTypeError):
        JSONPath("$./(val)").parse(data2)


def test_issue_13_contains_and_regex():
    data = {
        "products": [
            {"name": "Apple", "tags": ["fruit", "red"]},
            {"name": "Banana", "tags": ["fruit", "yellow"]},
            {"name": "Carrot", "tags": ["vegetable", "orange"]},
        ]
    }

    # Case 1: 'in' operator (list contains)
    # Check if 'fruit' is in tags list
    expr_in_list = "$.products[?('fruit' in @.tags)].name"
    assert JSONPath(expr_in_list).parse(data) == ["Apple", "Banana"]

    # Case 2: 'in' operator (string contains)
    # Check if 'App' is in name
    expr_in_str = "$.products[?('App' in @.name)].name"
    assert JSONPath(expr_in_str).parse(data) == ["Apple"]

    # Case 3: Regex operator =~
    # Check if name starts with 'B'
    expr_regex = "$.products[?(@.name =~ /B.*/)].name"
    assert JSONPath(expr_regex).parse(data) == ["Banana"]

    # Case 4: Case insensitive regex
    expr_regex_case = "$.products[?(@.name =~ /(?i)apple/)].name"
    assert JSONPath(expr_regex_case).parse(data) == ["Apple"]
