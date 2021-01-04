from jsonpath import JSONPath


def test_value_cases(value_cases):
    assert value_cases.result == JSONPath(value_cases.expr).parse(value_cases.data)


def test_path_cases(path_cases):
    print(JSONPath(path_cases.expr).parse(path_cases.data, "PATH"))
    # assert path_cases.result == JSONPath(path_cases.expr).parse(path_cases.data, "PATH")
