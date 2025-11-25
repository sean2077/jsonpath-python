"""Integration tests using sample data file.

These tests verify JSONPath expressions against the standard test data file.
"""

from jsonpath import JSONPath


class TestValueResult:
    """Test VALUE result type with sample data."""

    def test_wildcard(self, sample_data):
        result = JSONPath("$.*").parse(sample_data)
        assert sorted(result, key=str) == sorted(sample_data.values(), key=str)

    def test_dot_notation(self, sample_data):
        assert JSONPath("$.book").parse(sample_data) == [sample_data["book"]]

    def test_bracket_notation(self, sample_data):
        assert JSONPath("$[book]").parse(sample_data) == [sample_data["book"]]

    def test_quoted_key_single(self, sample_data):
        assert JSONPath("$.'a.b c'").parse(sample_data) == [sample_data["a.b c"]]

    def test_quoted_key_bracket(self, sample_data):
        assert JSONPath("$['a.b c']").parse(sample_data) == [sample_data["a.b c"]]

    def test_recursive_descent(self, sample_data):
        result = JSONPath("$..price").parse(sample_data)
        assert sorted(result) == [8.95, 8.99, 12.99, 19.95, 22.99]

    def test_slice_basic(self, sample_data):
        assert JSONPath("$.book[1:3]").parse(sample_data) == sample_data["book"][1:3]

    def test_slice_negative(self, sample_data):
        assert JSONPath("$.book[1:-1]").parse(sample_data) == sample_data["book"][1:-1]

    def test_slice_step(self, sample_data):
        assert JSONPath("$.book[0:-1:2]").parse(sample_data) == sample_data["book"][0:-1:2]

    def test_slice_empty_result(self, sample_data):
        assert JSONPath("$.book[-1:1]").parse(sample_data) == []

    def test_slice_all(self, sample_data):
        assert JSONPath("$.book[:]").parse(sample_data) == sample_data["book"][:]

    def test_filter_range(self, sample_data):
        result = JSONPath("$.book[?(@.price>8 and @.price<9)].price").parse(sample_data)
        assert sorted(result) == [8.95, 8.99]

    def test_filter_equality(self, sample_data):
        result = JSONPath('$.book[?(@.category=="reference")].category').parse(sample_data)
        assert result == ["reference"]

    def test_filter_combined(self, sample_data):
        result = JSONPath('$.book[?(@.category!="reference" and @.price<9)].title').parse(sample_data)
        assert result == ["Moby Dick"]

    def test_filter_or(self, sample_data):
        result = JSONPath('$.book[?(@.author=="Herman Melville" or @.author=="Evelyn Waugh")].author').parse(
            sample_data
        )
        assert sorted(result) == ["Evelyn Waugh", "Herman Melville"]

    def test_sort_ascending(self, sample_data):
        result = JSONPath("$.book[/(price)].price").parse(sample_data)
        assert result == [8.95, 8.99, 12.99, 22.99]

    def test_sort_descending(self, sample_data):
        result = JSONPath("$.book[/(~price)].price").parse(sample_data)
        assert result == [22.99, 12.99, 8.99, 8.95]

    def test_sort_multi_field(self, sample_data):
        result = JSONPath("$.book[/(category,price)].price").parse(sample_data)
        assert result == [8.99, 12.99, 22.99, 8.95]

    def test_sort_nested_field(self, sample_data):
        result = JSONPath("$.book[/(brand.version)].brand.version").parse(sample_data)
        assert result == ["v0.0.1", "v1.0.0", "v1.0.2", "v1.0.3"]

    def test_sort_dict_values(self, sample_data):
        result = JSONPath("$.scores[/(score)].score").parse(sample_data)
        assert result == [60, 85, 90, 95, 100]

    def test_field_extractor(self, sample_data):
        result = JSONPath("$.book[*].(title)").parse(sample_data)
        expected = [
            {"title": "Sayings of the Century"},
            {"title": "Sword of Honour"},
            {"title": "Moby Dick"},
            {"title": "The Lord of the Rings"},
        ]
        assert result == expected

    def test_field_extractor_multiple(self, sample_data):
        result = JSONPath("$.book[/(category,price)].(title,price)").parse(sample_data)
        expected = [
            {"title": "Moby Dick", "price": 8.99},
            {"title": "Sword of Honour", "price": 12.99},
            {"title": "The Lord of the Rings", "price": 22.99},
            {"title": "Sayings of the Century", "price": 8.95},
        ]
        assert result == expected

    def test_field_extractor_nested(self, sample_data):
        result = JSONPath("$.book[*].(title,brand.version)").parse(sample_data)
        expected = [
            {"title": "Sayings of the Century", "brand.version": "v1.0.0"},
            {"title": "Sword of Honour", "brand.version": "v0.0.1"},
            {"title": "Moby Dick", "brand.version": "v1.0.2"},
            {"title": "The Lord of the Rings", "brand.version": "v1.0.3"},
        ]
        assert result == expected

    def test_sort_and_extract(self, sample_data):
        result = JSONPath("$.scores[/(score)].(score)").parse(sample_data)
        expected = [
            {"score": 60},
            {"score": 85},
            {"score": 90},
            {"score": 95},
            {"score": 100},
        ]
        assert result == expected


class TestPathResult:
    """Test PATH result type with sample data."""

    def test_wildcard(self, sample_data):
        result = JSONPath("$.*").parse(sample_data, "PATH")
        # Sort because dict iteration order may vary
        assert sorted(result) == sorted(["$['a.b c']", "$.bicycle", "$.book", "$.scores"])

    def test_dot_notation(self, sample_data):
        assert JSONPath("$.book").parse(sample_data, "PATH") == ["$.book"]

    def test_bracket_notation(self, sample_data):
        assert JSONPath("$[book]").parse(sample_data, "PATH") == ["$.book"]

    def test_quoted_key(self, sample_data):
        assert JSONPath("$.'a.b c'").parse(sample_data, "PATH") == ["$['a.b c']"]
        assert JSONPath("$['a.b c']").parse(sample_data, "PATH") == ["$['a.b c']"]

    def test_recursive_descent(self, sample_data):
        result = JSONPath("$..price").parse(sample_data, "PATH")
        expected = [
            "$.book[0].price",
            "$.book[1].price",
            "$.book[2].price",
            "$.book[3].price",
            "$.bicycle.price",
        ]
        assert result == expected

    def test_slice(self, sample_data):
        assert JSONPath("$.book[1:3]").parse(sample_data, "PATH") == ["$.book[1]", "$.book[2]"]
        assert JSONPath("$.book[1:-1]").parse(sample_data, "PATH") == ["$.book[1]", "$.book[2]"]
        assert JSONPath("$.book[0:-1:2]").parse(sample_data, "PATH") == ["$.book[0]", "$.book[2]"]
        assert JSONPath("$.book[-1:1]").parse(sample_data, "PATH") == []
        assert JSONPath("$.book[:]").parse(sample_data, "PATH") == [
            "$.book[0]",
            "$.book[1]",
            "$.book[2]",
            "$.book[3]",
        ]

    def test_filter(self, sample_data):
        result = JSONPath("$.book[?(@.price>8 and @.price<9)].price").parse(sample_data, "PATH")
        assert result == ["$.book[0].price", "$.book[2].price"]

        result = JSONPath('$.book[?(@.category=="reference")].category').parse(sample_data, "PATH")
        assert result == ["$.book[0].category"]

    def test_sort(self, sample_data):
        result = JSONPath("$.book[/(price)].price").parse(sample_data, "PATH")
        expected = ["$.book[0].price", "$.book[2].price", "$.book[1].price", "$.book[3].price"]
        assert result == expected

        result = JSONPath("$.book[/(~price)].price").parse(sample_data, "PATH")
        expected = ["$.book[3].price", "$.book[1].price", "$.book[2].price", "$.book[0].price"]
        assert result == expected

    def test_sort_dict(self, sample_data):
        result = JSONPath("$.scores[/(score)].score").parse(sample_data, "PATH")
        expected = [
            "$.scores.chinese.score",
            "$.scores.chemistry.score",
            "$.scores.physic.score",
            "$.scores.english.score",
            "$.scores.math.score",
        ]
        assert result == expected
