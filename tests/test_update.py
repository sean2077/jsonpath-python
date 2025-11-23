from jsonpath.jsonpath import JSONPath


def test_update_value():
    data = {
        "store": {
            "book": [
                {"category": "reference", "author": "Nigel Rees", "title": "Sayings of the Century", "price": 8.95}
            ]
        }
    }
    jp = JSONPath("$.store.book[0].price")
    result = jp.update(data, 10.0)
    assert result["store"]["book"][0]["price"] == 10.0


def test_update_function():
    data = {"count": 1}
    jp = JSONPath("$.count")
    result = jp.update(data, lambda x: x + 1)
    assert result["count"] == 2


def test_update_root():
    data = {"a": 1}
    jp = JSONPath("$")
    result = jp.update(data, {"b": 2})
    assert result == {"b": 2}


def test_update_list_index():
    data = [1, 2, 3]
    jp = JSONPath("$[1]")
    result = jp.update(data, 5)
    assert result == [1, 5, 3]


def test_update_multiple():
    data = {"items": [{"value": 1}, {"value": 2}, {"value": 3}]}
    jp = JSONPath("$.items[*].value")
    result = jp.update(data, 0)
    for item in result["items"]:
        assert item["value"] == 0


def test_update_multiple_func():
    data = {"items": [{"value": 1}, {"value": 2}, {"value": 3}]}
    jp = JSONPath("$.items[*].value")
    result = jp.update(data, lambda x: x * 2)
    assert result["items"][0]["value"] == 2
    assert result["items"][1]["value"] == 4
    assert result["items"][2]["value"] == 6


def test_update_with_filter():
    data = {"books": [{"price": 10, "title": "A"}, {"price": 20, "title": "B"}, {"price": 30, "title": "C"}]}
    # Update price where price > 15
    jp = JSONPath("$.books[?(@.price > 15)].price")
    result = jp.update(data, 0)
    assert result["books"][0]["price"] == 10  # Unchanged
    assert result["books"][1]["price"] == 0  # Updated
    assert result["books"][2]["price"] == 0  # Updated


def test_update_slice():
    data = [0, 1, 2, 3, 4]
    jp = JSONPath("$[1:4]")  # Indices 1, 2, 3
    result = jp.update(data, 9)
    assert result == [0, 9, 9, 9, 4]


def test_update_special_keys():
    data = {"complex.key": 1, "key with space": 2, "normal": 3}
    # Note: jsonpath-python might handle keys with dots using ['...'] syntax in path output
    jp = JSONPath("$['complex.key']")
    result = jp.update(data, 10)
    assert result["complex.key"] == 10

    jp = JSONPath("$['key with space']")
    result = jp.update(data, 20)
    assert result["key with space"] == 20


def test_update_no_match():
    data = {"a": 1}
    jp = JSONPath("$.b")
    result = jp.update(data, 2)
    assert result == {"a": 1}


def test_update_nested_structure():
    data = {"a": [{"b": [1, 2]}, {"b": [3, 4]}]}
    jp = JSONPath("$.a[*].b[1]")
    result = jp.update(data, 99)
    assert result["a"][0]["b"][1] == 99
    assert result["a"][1]["b"][1] == 99


def test_update_recursive():
    data = {
        "store": {
            "book": [{"category": "reference", "price": 8.95}, {"category": "fiction", "price": 12.99}],
            "bicycle": {"color": "red", "price": 19.95},
        }
    }
    jp = JSONPath("$..price")
    result = jp.update(data, 10.0)
    assert result["store"]["book"][0]["price"] == 10.0
    assert result["store"]["book"][1]["price"] == 10.0
    assert result["store"]["bicycle"]["price"] == 10.0


def test_update_union():
    data = {"a": 1, "b": 2, "c": 3}
    jp = JSONPath("$[a,b]")
    result = jp.update(data, 0)
    assert result["a"] == 0
    assert result["b"] == 0
    assert result["c"] == 3


def test_update_quote_keys():
    data = {'c"d': 1, "normal": 2}
    jp = JSONPath("$['c\"d']")
    result = jp.update(data, 99)
    assert result['c"d'] == 99
