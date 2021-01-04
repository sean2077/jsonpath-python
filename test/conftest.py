import json
from collections import namedtuple

import pytest

TestCase = namedtuple("TestCase", ("expr", "data", "result"))

with open("test/data/2.json", "rb") as f:
    data = json.load(f)


@pytest.fixture(
    params=[
        TestCase("$.*", data, list(data.values())),
        TestCase("$.book", data, [data["book"]]),
        TestCase("$[book]", data, [data["book"]]),
        TestCase("$.'a.b c'", data, [data["a.b c"]]),
        TestCase("$['a.b c']", data, [data["a.b c"]]),
        TestCase("$..price", data, [8.95, 12.99, 8.99, 22.99, 19.95]),
        TestCase("$.book[1:3]", data, data["book"][1:3]),
        TestCase("$.book[1:-1]", data, data["book"][1:-1]),
        TestCase("$.book[0:-1:2]", data, data["book"][0:-1:2]),
        TestCase("$.book[-1:1]", data, data["book"][-1:1]),
        TestCase("$.book[-1:-11:3]", data, data["book"][-1:-11:3]),
        TestCase("$.book[:]", data, data["book"][:]),
        TestCase("$.book[?(@.price>8 and @.price<9)].price", data, [8.95, 8.99]),
        TestCase('$.book[?(@.category=="reference")].category', data, ["reference"]),
        TestCase(
            '$.book[?(@.category!="reference" and @.price<9)].title',
            data,
            ["Moby Dick"],
        ),
        TestCase(
            '$.book[?(@.author=="Herman Melville" or @.author=="Evelyn Waugh")].author',
            data,
            ["Evelyn Waugh", "Herman Melville"],
        ),
        TestCase("$.book[/(price)].price", data, [8.95, 8.99, 12.99, 22.99]),
        TestCase("$.book[/(~price)].price", data, [22.99, 12.99, 8.99, 8.95]),
        TestCase("$.book[/(category,price)].price", data, [8.99, 12.99, 22.99, 8.95]),
        TestCase(
            "$.book[/(brand.version)].brand.version",
            data,
            ["v0.0.1", "v1.0.0", "v1.0.2", "v1.0.3"],
        ),
        TestCase("$.scores[/(score)].score", data, [60, 85, 90, 95, 100]),
    ]
)
def cases(request):
    return request.param
