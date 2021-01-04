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
        # recursive descent
        TestCase("$..price", data, [8.95, 12.99, 8.99, 22.99, 19.95]),
        # slice
        TestCase("$.book[1:3]", data, data["book"][1:3]),
        TestCase("$.book[1:-1]", data, data["book"][1:-1]),
        TestCase("$.book[0:-1:2]", data, data["book"][0:-1:2]),
        TestCase("$.book[-1:1]", data, data["book"][-1:1]),
        TestCase("$.book[-1:-11:3]", data, data["book"][-1:-11:3]),
        TestCase("$.book[:]", data, data["book"][:]),
        # filter
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
        # sort
        TestCase("$.book[/(price)].price", data, [8.95, 8.99, 12.99, 22.99]),
        TestCase("$.book[/(~price)].price", data, [22.99, 12.99, 8.99, 8.95]),
        TestCase("$.book[/(category,price)].price", data, [8.99, 12.99, 22.99, 8.95]),
        TestCase(
            "$.book[/(brand.version)].brand.version",
            data,
            ["v0.0.1", "v1.0.0", "v1.0.2", "v1.0.3"],
        ),
        TestCase("$.scores[/(score)].score", data, [60, 85, 90, 95, 100]),
        TestCase(
            "$.scores[/(score)].(score)",
            data,
            [
                {"score": 60},
                {"score": 85},
                {"score": 90},
                {"score": 95},
                {"score": 100},
            ],
        ),
        TestCase(
            "$.book[*].(title)",
            data,
            [
                {"title": "Sayings of the Century"},
                {"title": "Sword of Honour"},
                {"title": "Moby Dick"},
                {"title": "The Lord of the Rings"},
            ],
        ),
        TestCase(
            "$.book[/(category,price)].(title,price)",
            data,
            [
                {"title": "Moby Dick", "price": 8.99},
                {"title": "Sword of Honour", "price": 12.99},
                {"title": "The Lord of the Rings", "price": 22.99},
                {"title": "Sayings of the Century", "price": 8.95},
            ],
        ),
    ]
)
def value_cases(request):
    return request.param


@pytest.fixture(
    params=[
        TestCase("$.*", data, ["$;a.b c", "$;book", "$;bicycle", "$;scores"]),
        TestCase("$.book", data, ["$;book"]),
        TestCase("$[book]", data, ["$;book"]),
        TestCase("$.'a.b c'", data, ["$;a.b c"]),
        TestCase("$['a.b c']", data, ["$;a.b c"]),
        # recursive descent
        TestCase(
            "$..price",
            data,
            [
                "$;book;0;price",
                "$;book;1;price",
                "$;book;2;price",
                "$;book;3;price",
                "$;bicycle;price",
            ],
        ),
        # slice
        TestCase("$.book[1:3]", data, ["$;book;1", "$;book;2"]),
        TestCase("$.book[1:-1]", data, ["$;book;1", "$;book;2"]),
        TestCase("$.book[0:-1:2]", data, ["$;book;0", "$;book;2"]),
        TestCase("$.book[-1:1]", data, []),
        TestCase("$.book[-1:-11:3]", data, []),
        TestCase("$.book[:]", data, ["$;book;0", "$;book;1", "$;book;2", "$;book;3"]),
        # filter
        TestCase(
            "$.book[?(@.price>8 and @.price<9)].price",
            data,
            ["$;book;0;price", "$;book;2;price"],
        ),
        TestCase(
            '$.book[?(@.category=="reference")].category', data, ["$;book;0;category"]
        ),
        TestCase(
            '$.book[?(@.category!="reference" and @.price<9)].title',
            data,
            ["$;book;2;title"],
        ),
        TestCase(
            '$.book[?(@.author=="Herman Melville" or @.author=="Evelyn Waugh")].author',
            data,
            ["$;book;1;author", "$;book;2;author"],
        ),
        # sort
        TestCase(
            "$.book[/(price)].price",
            data,
            ["$;book;0;price", "$;book;2;price", "$;book;1;price", "$;book;3;price"],
        ),
        TestCase(
            "$.book[/(~price)].price",
            data,
            ["$;book;3;price", "$;book;1;price", "$;book;2;price", "$;book;0;price"],
        ),
        TestCase(
            "$.book[/(category,price)].price",
            data,
            ["$;book;2;price", "$;book;1;price", "$;book;3;price", "$;book;0;price"],
        ),
        TestCase(
            "$.book[/(brand.version)].brand.version",
            data,
            [
                "$;book;1;brand;version",
                "$;book;0;brand;version",
                "$;book;2;brand;version",
                "$;book;3;brand;version",
            ],
        ),
        TestCase(
            "$.scores[/(score)].score",
            data,
            [
                "$;scores;chinese;score",
                "$;scores;chemistry;score",
                "$;scores;physic;score",
                "$;scores;english;score",
                "$;scores;math;score",
            ],
        ),
    ]
)
def path_cases(request):
    return request.param
