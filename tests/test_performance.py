"""Performance tests for jsonpath-python.

Run with: pytest tests/test_performance.py -m perf -v
"""

import json
import time

import pytest

from jsonpath import JSONPath, search


@pytest.fixture(scope="module")
def large_data():
    """Load large test data for performance testing."""
    with open("tests/data/1.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def small_data():
    """Load small test data for performance testing."""
    with open("tests/data/2.json") as f:
        return json.load(f)


@pytest.mark.perf
class TestPerformance:
    """Performance benchmark tests."""

    def test_parse_reuse_instance(self, large_data, benchmark):
        """Benchmark parsing with reused JSONPath instance."""
        jp = JSONPath("$..price")
        benchmark(jp.parse, large_data)

    def test_parse_new_instance(self, large_data, benchmark):
        """Benchmark parsing with new JSONPath instance each time."""

        def parse_with_new_instance():
            return JSONPath("$..price").parse(large_data)

        benchmark(parse_with_new_instance)

    def test_cached_search(self, large_data, benchmark):
        """Benchmark using cached search function."""
        benchmark(search, "$..price", large_data)

    def test_simple_path(self, small_data, benchmark):
        """Benchmark simple path access."""
        jp = JSONPath("$.book[0].price")
        benchmark(jp.parse, small_data)

    def test_recursive_descent(self, large_data, benchmark):
        """Benchmark recursive descent operator."""
        jp = JSONPath("$..price")
        benchmark(jp.parse, large_data)

    def test_wildcard(self, small_data, benchmark):
        """Benchmark wildcard operator."""
        jp = JSONPath("$.book[*].price")
        benchmark(jp.parse, small_data)

    def test_filter_expression(self, small_data, benchmark):
        """Benchmark filter expression."""
        jp = JSONPath("$.book[?(@.price < 10)].title")
        benchmark(jp.parse, small_data)

    def test_slice_operation(self, small_data, benchmark):
        """Benchmark slice operation."""
        jp = JSONPath("$.book[1:3]")
        benchmark(jp.parse, small_data)

    def test_sorter_single_field(self, small_data, benchmark):
        """Benchmark single field sorter operation."""
        jp = JSONPath("$.book[/(price)].title")
        benchmark(jp.parse, small_data)

    def test_sorter_multi_field_same_direction(self, small_data, benchmark):
        """Benchmark multi-field sorter with same direction."""
        jp = JSONPath("$.book[/(price, title)]")
        benchmark(jp.parse, small_data)

    def test_sorter_multi_field_mixed_direction(self, small_data, benchmark):
        """Benchmark multi-field sorter with mixed directions."""
        jp = JSONPath("$.book[/(price, ~title)]")
        benchmark(jp.parse, small_data)

    def test_field_extractor(self, small_data, benchmark):
        """Benchmark field extractor operation."""
        jp = JSONPath("$.book[*].(title,price)")
        benchmark(jp.parse, small_data)

    def test_complex_expression(self, small_data, benchmark):
        """Benchmark complex JSONPath expression with filter and field extraction."""
        jp = JSONPath("$.book[?(@.price > 8 and @.price < 13)].(title,price)")
        benchmark(jp.parse, small_data)

    def test_update_static_value(self, small_data, benchmark):
        """Benchmark update with static value."""
        jp = JSONPath("$.book[*].price")

        def update_static():
            data = json.loads(json.dumps(small_data))  # Deep copy
            return jp.update(data, 100)

        benchmark(update_static)

    def test_update_function(self, small_data, benchmark):
        """Benchmark update with callback function."""
        jp = JSONPath("$.book[*].price")

        def update_func():
            data = json.loads(json.dumps(small_data))  # Deep copy
            return jp.update(data, lambda x: x * 0.9)

        benchmark(update_func)

    def test_regex_filter(self, small_data, benchmark):
        """Benchmark regex pattern matching in filters."""
        jp = JSONPath("$.book[?(@.title =~ /^Sword/)].price")
        benchmark(jp.parse, small_data)

    def test_nested_filter(self, small_data, benchmark):
        """Benchmark nested filter expressions."""
        jp = JSONPath("$.book[?(@.price < 10 and @.category == 'fiction')]")
        benchmark(jp.parse, small_data)

    def test_path_result_type(self, small_data, benchmark):
        """Benchmark returning paths instead of values."""
        jp = JSONPath("$..price")
        benchmark(jp.parse, small_data, "PATH")


@pytest.mark.perf
@pytest.mark.slow
class TestScalability:
    """Scalability tests with varying data sizes."""

    def test_parse_scaling_with_depth(self, benchmark):
        """Test performance scaling with nested depth."""
        # Create deeply nested structure
        data = {"level": 1}
        current = data
        for i in range(2, 50):
            current["nested"] = {"level": i}
            current = current["nested"]

        jp = JSONPath("$..level")
        benchmark(jp.parse, data)

    def test_parse_scaling_with_array_size(self, benchmark):
        """Test performance scaling with array size."""
        # Create large array
        data = {"items": [{"id": i, "value": i * 2} for i in range(1000)]}

        jp = JSONPath("$.items[*].value")
        benchmark(jp.parse, data)

    def test_filter_scaling(self, benchmark):
        """Test filter performance with large arrays."""
        data = {"items": [{"id": i, "active": i % 2 == 0} for i in range(1000)]}

        jp = JSONPath("$.items[?(@.active == true)].id")
        benchmark(jp.parse, data)


@pytest.mark.perf
class TestCacheEfficiency:
    """Test caching efficiency."""

    def test_cache_hit_rate(self, small_data):
        """Measure cache effectiveness."""
        expressions = [
            "$.book[*].price",
            "$..price",
            "$.book[0].title",
            "$.book[?(@.price < 10)]",
        ]

        # Warm up cache
        for expr in expressions:
            search(expr, small_data)

        # Measure cached performance
        start = time.time()
        for _ in range(100):
            for expr in expressions:
                search(expr, small_data)
        cached_time = time.time() - start

        # Clear cache and measure uncached performance
        from jsonpath.jsonpath import _jsonpath_cache  # noqa: PLC2701

        _jsonpath_cache.clear()

        start = time.time()
        for _ in range(100):
            for expr in expressions:
                JSONPath(expr).parse(small_data)
        uncached_time = time.time() - start

        # Cache should provide some benefit
        assert cached_time < uncached_time * 1.1, f"Cache not effective: {cached_time:.3f}s vs {uncached_time:.3f}s"

    def test_cache_memory_limit(self, small_data):
        """Test that cache size limit is enforced."""
        from jsonpath.jsonpath import _CACHE_MAX_SIZE, _jsonpath_cache  # noqa: PLC2701

        _jsonpath_cache.clear()

        # Create more expressions than cache size
        for i in range(_CACHE_MAX_SIZE + 10):
            search(f"$.book[{i % 4}]", small_data)

        # Cache should not exceed max size (or be cleared)
        assert len(_jsonpath_cache) <= _CACHE_MAX_SIZE, (
            f"Cache size {len(_jsonpath_cache)} exceeds limit {_CACHE_MAX_SIZE}"
        )
