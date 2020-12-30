from jsonpath import JSONPath


def test_cases(cases):
    assert cases.result == JSONPath(cases.expr).parse(cases.data)