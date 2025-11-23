from jsonpath import JSONPath


def test_value_cases(value_cases):
    print(value_cases.expr)
    r = JSONPath(value_cases.expr).parse(value_cases.data)
    assert r == value_cases.result


def test_path_cases(path_cases):
    print(path_cases.expr)
    r = JSONPath(path_cases.expr).parse(path_cases.data, "PATH")
    assert r == path_cases.result
