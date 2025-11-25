"""Basic JSONPath functionality tests.

Tests are organized by feature category for clarity and maintainability.
"""

import pytest

from jsonpath import JSONPath, compile, search


class TestSimplePath:
    """Test simple path expressions."""

    def test_root_access(self):
        data = {"a": 1, "b": 2}
        assert JSONPath("$").parse(data) == [{"a": 1, "b": 2}]

    def test_dot_notation(self):
        data = {"store": {"book": "title"}}
        assert JSONPath("$.store").parse(data) == [{"book": "title"}]
        assert JSONPath("$.store.book").parse(data) == ["title"]

    def test_bracket_notation(self):
        data = {"store": {"book": "title"}}
        assert JSONPath("$['store']").parse(data) == [{"book": "title"}]
        assert JSONPath("$['store']['book']").parse(data) == ["title"]

    def test_mixed_notation(self):
        data = {"store": {"book": "title"}}
        assert JSONPath("$.store['book']").parse(data) == ["title"]
        assert JSONPath("$['store'].book").parse(data) == ["title"]

    def test_array_index(self):
        data = {"items": [1, 2, 3]}
        assert JSONPath("$.items[0]").parse(data) == [1]
        assert JSONPath("$.items[2]").parse(data) == [3]

    def test_negative_index(self):
        # Note: Negative indices are not directly supported in path expressions
        # but work in slice operations
        data = {"items": [1, 2, 3]}
        assert JSONPath("$.items[-1:]").parse(data) == [3]


class TestWildcard:
    """Test wildcard operator (*)."""

    def test_wildcard_object(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = JSONPath("$.*").parse(data)
        assert sorted(result) == [1, 2, 3]

    def test_wildcard_array(self):
        data = {"items": [1, 2, 3]}
        assert JSONPath("$.items[*]").parse(data) == [1, 2, 3]

    def test_wildcard_nested(self):
        data = {"items": [{"v": 1}, {"v": 2}, {"v": 3}]}
        assert JSONPath("$.items[*].v").parse(data) == [1, 2, 3]


class TestRecursiveDescent:
    """Test recursive descent operator (..)."""

    def test_recursive_simple(self):
        data = {"a": {"b": {"c": 1}}}
        assert JSONPath("$..c").parse(data) == [1]

    def test_recursive_multiple(self):
        data = {
            "store": {
                "book": [{"price": 10}, {"price": 20}],
                "bicycle": {"price": 30},
            }
        }
        assert sorted(JSONPath("$..price").parse(data)) == [10, 20, 30]

    def test_recursive_array(self):
        data = {"a": [{"b": 1}, {"b": 2}]}
        assert JSONPath("$..b").parse(data) == [1, 2]


class TestSlice:
    """Test array slice operations."""

    def test_slice_start_end(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[1:3]").parse(data) == [1, 2]

    def test_slice_start_only(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[2:]").parse(data) == [2, 3, 4]

    def test_slice_end_only(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[:3]").parse(data) == [0, 1, 2]

    def test_slice_negative(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[1:-1]").parse(data) == [1, 2, 3]

    def test_slice_step(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[::2]").parse(data) == [0, 2, 4]
        assert JSONPath("$.items[0:-1:2]").parse(data) == [0, 2]

    def test_slice_all(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[:]").parse(data) == [0, 1, 2, 3, 4]

    def test_slice_empty_result(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[-1:1]").parse(data) == []


class TestFilter:
    """Test filter expressions."""

    def test_filter_comparison(self):
        data = {"items": [{"v": 1}, {"v": 2}, {"v": 3}]}
        assert JSONPath("$.items[?(@.v > 1)].v").parse(data) == [2, 3]
        assert JSONPath("$.items[?(@.v >= 2)].v").parse(data) == [2, 3]
        assert JSONPath("$.items[?(@.v < 3)].v").parse(data) == [1, 2]
        assert JSONPath("$.items[?(@.v <= 2)].v").parse(data) == [1, 2]
        assert JSONPath("$.items[?(@.v == 2)].v").parse(data) == [2]
        assert JSONPath("$.items[?(@.v != 2)].v").parse(data) == [1, 3]

    def test_filter_logical_and(self):
        data = {"items": [{"v": 1}, {"v": 2}, {"v": 3}]}
        assert JSONPath("$.items[?(@.v > 1 and @.v < 3)].v").parse(data) == [2]

    def test_filter_logical_or(self):
        data = {"items": [{"v": 1}, {"v": 2}, {"v": 3}]}
        assert JSONPath("$.items[?(@.v == 1 or @.v == 3)].v").parse(data) == [1, 3]

    def test_filter_string_equality(self):
        data = {"items": [{"name": "a"}, {"name": "b"}]}
        assert JSONPath('$.items[?(@.name == "a")].name').parse(data) == ["a"]
        assert JSONPath("$.items[?(@.name == 'b')].name").parse(data) == ["b"]

    def test_filter_in_operator_list(self):
        data = {"items": [{"tags": ["a", "b"]}, {"tags": ["c", "d"]}]}
        assert JSONPath("$.items[?('a' in @.tags)].tags").parse(data) == [["a", "b"]]

    def test_filter_in_operator_string(self):
        data = {"items": [{"name": "apple"}, {"name": "banana"}]}
        assert JSONPath("$.items[?('app' in @.name)].name").parse(data) == ["apple"]

    def test_filter_regex(self):
        data = {"items": [{"name": "apple"}, {"name": "banana"}]}
        assert JSONPath("$.items[?(@.name =~ /^app/)].name").parse(data) == ["apple"]
        assert JSONPath("$.items[?(@.name =~ /(?i)APPLE/)].name").parse(data) == ["apple"]

    def test_filter_on_dict(self):
        data = {"item": {"price": 10, "name": "test"}}
        assert JSONPath("$[?(@.price > 5)]").parse(data) == [{"price": 10, "name": "test"}]


class TestSelect:
    """Test select (union) operations."""

    def test_select_multiple_keys(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = JSONPath("$[a,b]").parse(data)
        assert sorted(result) == [1, 2]

    def test_select_with_spaces(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = JSONPath("$[a, b]").parse(data)
        assert sorted(result) == [1, 2]


class TestSorter:
    """Test sorter operations."""

    def test_sort_ascending(self):
        data = {"items": [{"v": 3}, {"v": 1}, {"v": 2}]}
        result = JSONPath("$.items[/(v)].v").parse(data)
        assert result == [1, 2, 3]

    def test_sort_descending(self):
        data = {"items": [{"v": 3}, {"v": 1}, {"v": 2}]}
        result = JSONPath("$.items[/(~v)].v").parse(data)
        assert result == [3, 2, 1]

    def test_sort_multi_field(self):
        data = {"items": [{"a": 1, "b": 2}, {"a": 1, "b": 1}, {"a": 2, "b": 1}]}
        result = JSONPath("$.items[/(a,b)]").parse(data)
        assert result == [{"a": 1, "b": 1}, {"a": 1, "b": 2}, {"a": 2, "b": 1}]

    def test_sort_nested_field(self):
        data = {"items": [{"x": {"y": 3}}, {"x": {"y": 1}}, {"x": {"y": 2}}]}
        result = JSONPath("$.items[/(x.y)].x.y").parse(data)
        assert result == [1, 2, 3]

    def test_sort_string_numbers(self):
        """Strings that look like numbers should be sorted numerically."""
        data = [{"v": "10"}, {"v": "2"}]
        result = JSONPath("$[/(v)].v").parse(data)
        assert result == ["2", "10"]

    def test_sort_dict(self):
        data = {"items": {"a": {"v": 3}, "b": {"v": 1}, "c": {"v": 2}}}
        result = JSONPath("$.items[/(v)].v").parse(data)
        assert result == [1, 2, 3]


class TestFieldExtractor:
    """Test field extractor operations."""

    def test_extract_single_field(self):
        data = {"items": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]}
        result = JSONPath("$.items[*].(a)").parse(data)
        assert result == [{"a": 1}, {"a": 3}]

    def test_extract_multiple_fields(self):
        data = {"items": [{"a": 1, "b": 2, "c": 3}]}
        result = JSONPath("$.items[*].(a,b)").parse(data)
        assert result == [{"a": 1, "b": 2}]

    def test_extract_nested_field(self):
        data = {"item": {"x": {"y": 1}, "a": 2}}
        result = JSONPath("$.item.(a,x.y)").parse(data)
        assert result == [{"a": 2, "x.y": 1}]

    def test_extract_missing_field(self):
        """Missing fields should be omitted from result."""
        data = {"item": {"a": 1}}
        result = JSONPath("$.item.(a,b)").parse(data)
        assert result == [{"a": 1}]


class TestSpecialKeys:
    """Test handling of special key names."""

    def test_key_with_space(self):
        data = {"key with space": 1}
        assert JSONPath("$['key with space']").parse(data) == [1]
        assert JSONPath("$.'key with space'").parse(data) == [1]

    def test_key_with_dot(self):
        data = {"a.b": 1}
        assert JSONPath("$['a.b']").parse(data) == [1]
        assert JSONPath("$.'a.b'").parse(data) == [1]

    def test_key_with_hyphen(self):
        data = {"a-b": 1}
        assert JSONPath("$['a-b']").parse(data) == [1]
        assert JSONPath("$.'a-b'").parse(data) == [1]

    def test_key_with_hyphen_in_filter(self):
        data = {"items": [{"a-b": 1}, {"a-b": 2}]}
        assert JSONPath("$.items[?(@.'a-b' > 1)].'a-b'").parse(data) == [2]

    def test_key_with_quote(self):
        data = {'c"d': 1}
        assert JSONPath("$['c\"d']").parse(data) == [1]


class TestPathResult:
    """Test PATH result type."""

    def test_path_simple(self):
        data = {"a": {"b": 1}}
        assert JSONPath("$.a.b").parse(data, "PATH") == ["$.a.b"]

    def test_path_array(self):
        data = {"items": [1, 2]}
        assert JSONPath("$.items[0]").parse(data, "PATH") == ["$.items[0]"]

    def test_path_wildcard(self):
        data = {"a": 1, "b": 2}
        result = JSONPath("$.*").parse(data, "PATH")
        assert sorted(result) == ["$.a", "$.b"]

    def test_path_recursive(self):
        data = {"a": {"b": 1}, "c": 2}
        result = JSONPath("$..b").parse(data, "PATH")
        assert result == ["$.a.b"]

    def test_path_special_key(self):
        data = {"a.b": 1}
        assert JSONPath("$['a.b']").parse(data, "PATH") == ["$['a.b']"]


class TestAPI:
    """Test public API functions."""

    def test_compile(self):
        jp = compile("$.a")
        data = {"a": 1}
        assert jp.parse(data) == [1]

    def test_search(self):
        data = {"a": 1}
        assert search("$.a", data) == [1]

    def test_search_cached(self):
        """Same expression should use cached JSONPath instance."""
        data = {"a": 1}
        result1 = search("$.a", data)
        result2 = search("$.a", data)
        assert result1 == result2 == [1]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_result(self):
        data = {"a": 1}
        assert JSONPath("$.b").parse(data) == []

    def test_nonexistent_nested_path(self):
        data = {"a": 1}
        assert JSONPath("$.a.b.c").parse(data) == []

    def test_nonexistent_array_index(self):
        data = {"items": [1, 2]}
        assert JSONPath("$.items[5]").parse(data) == []

    def test_empty_object(self):
        data = {}
        assert JSONPath("$.a").parse(data) == []
        assert JSONPath("$.*").parse(data) == []

    def test_empty_array(self):
        data = {"items": []}
        assert JSONPath("$.items[*]").parse(data) == []
        assert JSONPath("$.items[0]").parse(data) == []

    def test_none_value(self):
        data = {"a": None}
        assert JSONPath("$.a").parse(data) == [None]

    def test_boolean_value(self):
        data = {"a": True, "b": False}
        assert JSONPath("$.a").parse(data) == [True]
        assert JSONPath("$.b").parse(data) == [False]

    def test_type_error_on_invalid_input(self):
        with pytest.raises(TypeError):
            JSONPath("$.a").parse("not a dict or list")

        with pytest.raises(TypeError):
            JSONPath("$.a").parse(123)

    def test_value_error_on_invalid_result_type(self):
        with pytest.raises(ValueError):
            JSONPath("$.a").parse({"a": 1}, "INVALID")


class TestExprSyntaxError:
    """Test syntax error handling."""

    def test_sorter_on_non_collection(self):
        """Sorter must operate on list or dict."""
        from jsonpath import ExprSyntaxError

        data = {"value": "string"}
        with pytest.raises(ExprSyntaxError, match="sorter must acting on list or dict"):
            JSONPath("$.value[/(x)]").parse(data)

    def test_field_extractor_on_non_dict(self):
        """Field extractor must operate on dict."""
        from jsonpath import ExprSyntaxError

        data = {"items": [1, 2, 3]}
        with pytest.raises(ExprSyntaxError, match="field-extractor must acting on dict"):
            JSONPath("$.items[0].(a,b)").parse(data)


class TestCustomEval:
    """Test custom eval function."""

    def test_custom_eval_function(self):
        """Custom eval can be used for safe expression evaluation."""
        data = {"items": [{"v": 1}, {"v": 2}]}
        jp = JSONPath("$.items[?(@.v > 0)]")

        # Track eval calls
        eval_calls = []

        def custom_eval(expr, *args, **kwargs):
            eval_calls.append(expr)
            return eval(expr, *args, **kwargs)

        result = jp.parse(data, eval_func=custom_eval)
        assert len(result) == 2
        assert len(eval_calls) > 0


class TestSliceAdvanced:
    """Test advanced slice operations."""

    def test_slice_reverse(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[::-1]").parse(data) == [4, 3, 2, 1, 0]

    def test_slice_reverse_step(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[::-2]").parse(data) == [4, 2, 0]

    def test_slice_negative_start(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[-2:]").parse(data) == [3, 4]

    def test_slice_negative_end(self):
        data = {"items": [0, 1, 2, 3, 4]}
        assert JSONPath("$.items[:-2]").parse(data) == [0, 1, 2]


class TestFilterAdvanced:
    """Test advanced filter operations."""

    def test_filter_not_in_operator(self):
        data = {"items": [{"tags": ["a", "b"]}, {"tags": ["c", "d"]}]}
        assert JSONPath("$.items[?('a' not in @.tags)].tags").parse(data) == [["c", "d"]]

    def test_filter_not_operator(self):
        data = {"items": [{"active": True}, {"active": False}]}
        assert JSONPath("$.items[?(not @.active)]").parse(data) == [{"active": False}]

    def test_filter_is_operator(self):
        data = {"items": [{"v": None}, {"v": 1}]}
        assert JSONPath("$.items[?(@.v is None)]").parse(data) == [{"v": None}]

    def test_filter_is_not_operator(self):
        data = {"items": [{"v": None}, {"v": 1}]}
        assert JSONPath("$.items[?(@.v is not None)]").parse(data) == [{"v": 1}]

    def test_filter_nested_attribute(self):
        data = {"items": [{"x": {"y": 1}}, {"x": {"y": 2}}]}
        assert JSONPath("$.items[?(@.x.y > 1)]").parse(data) == [{"x": {"y": 2}}]

    def test_filter_bracket_notation(self):
        data = {"items": [{"a-b": 1}, {"a-b": 2}]}
        assert JSONPath("$.items[?(@['a-b'] > 1)]").parse(data) == [{"a-b": 2}]


class TestRecursiveDescentAdvanced:
    """Test advanced recursive descent operations."""

    def test_recursive_with_bracket(self):
        data = {"a": {"b": 1}, "c": {"b": 2}}
        assert sorted(JSONPath("$..['b']").parse(data)) == [1, 2]

    def test_recursive_with_filter(self):
        data = {"items": [{"v": 1}, {"v": 2}]}
        result = JSONPath("$.items[*][?(@.v > 1)]").parse(data)
        assert result == [{"v": 2}]

    def test_recursive_multiple_levels(self):
        data = {"a": {"b": {"c": {"d": 1}}}}
        assert JSONPath("$..d").parse(data) == [1]


class TestJSONPathTypeError:
    """Test JSONPathTypeError exception."""

    def test_sort_incompatible_types(self):
        from jsonpath import JSONPathTypeError

        # Sorting with mixed types that can't be compared
        data = {"items": [{"v": "a"}, {"v": 1}]}
        with pytest.raises(JSONPathTypeError, match="not possible to compare"):
            JSONPath("$.items[/(v)]").parse(data)


class TestInstanceMethod:
    """Test JSONPath instance methods."""

    def test_search_method(self):
        """JSONPath.search() is an alias for parse()."""
        data = {"a": 1}
        jp = JSONPath("$.a")
        assert jp.search(data) == [1]
        assert jp.search(data, "PATH") == ["$.a"]

    def test_parse_reuse(self):
        """Same JSONPath instance can be reused for multiple parse calls."""
        jp = JSONPath("$.a")
        assert jp.parse({"a": 1}) == [1]
        assert jp.parse({"a": 2}) == [2]
        assert jp.parse({"a": 3}) == [3]
