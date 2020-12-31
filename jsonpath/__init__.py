"""
Author       : zhangxianbing1
Date         : 2020-12-27 09:22:14
LastEditors  : zhangxianbing1
LastEditTime : 2020-12-31 18:05:36
Description  : JSONPath
"""
__version__ = "1.0.0"
__author__ = "zhangxianbing"

import json
import re
import sys
from typing import Any, Dict, Iterable
from collections import defaultdict

RESULT_TYPE = {
    "VALUE": "A list of specific values.",
    "FIELD": "A dict with specific fields.",
    "PATH": "All path of specific values.",
}


SEP = ";"
# regex patterns
REP_PICKUP_QUOTE = re.compile(r"['](.*?)[']")
REP_PICKUP_BRACKET = re.compile(r"[\[](.*?)[\]]")
REP_PUTBACK_QUOTE = re.compile(r"#Q(\d+)")
REP_PUTBACK_BRACKET = re.compile(r"#B(\d+)")
REP_DOUBLEDOT = re.compile(r"\.\.")
REP_DOT = re.compile(r"(?<!\.)\.(?!\.)")

# operators
REP_SLICE_CONTENT = re.compile(r"^(-?\d*)?:(-?\d*)?(:-?\d*)?$")
REP_SELECT_CONTENT = re.compile(r"^([\w.]+)(,[\w.]+)+$")
REP_FILTER_CONTENT = re.compile(
    r"@\.(.*?)(?=<=|>=|==|!=|>|<| in| not| is)|len\(@\.(.*?)\)"
)

# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring,eval-used


def concat(x, y, con=SEP):
    return f"{x}{con}{y}"


def _getattr(obj: dict, path: str):
    r = obj
    for k in path.split("."):
        try:
            r = r.get(k)
        except (AttributeError, KeyError) as err:
            print(err)
            return None

    return r


class ExprSyntaxError(Exception):
    pass


class JSONPath:
    # annotations
    result: Iterable
    result_type: str
    subx = defaultdict(list)
    steps: list
    lpath: int

    def __init__(self, expr: str, *, result_type="VALUE"):
        if result_type not in RESULT_TYPE:
            raise ValueError(f"result_type must be one of {tuple(RESULT_TYPE.keys())}")
        self.result_type = result_type

        # parse expression
        expr = self._parse_expr(expr)
        self.steps = expr.split(SEP)
        self.lpath = len(self.steps)
        print(f"steps  : {self.steps}")

    def _parse_expr(self, expr):
        if __debug__:
            print(f"before expr : {expr}")

        expr = REP_PICKUP_QUOTE.sub(self._f_pickup_quote, expr)
        expr = REP_PICKUP_BRACKET.sub(self._f_pickup_bracket, expr)
        expr = REP_DOUBLEDOT.sub(f"{SEP}..{SEP}", expr)
        expr = REP_DOT.sub(SEP, expr)
        expr = REP_PUTBACK_BRACKET.sub(self._f_putback_bracket, expr)
        expr = REP_PUTBACK_QUOTE.sub(self._f_putback_quote, expr)
        if expr.startswith("$;"):
            expr = expr[2:]

        if __debug__:
            print(f"after expr  : {expr}")
        return expr

    def _f_pickup_quote(self, m):
        n = len(self.subx["#Q"])
        self.subx["#Q"].append(m.group(1))
        return f"#Q{n}"

    def _f_pickup_bracket(self, m):
        n = len(self.subx["#B"])
        self.subx["#B"].append(m.group(1))
        return f".#B{n}"

    def _f_putback_quote(self, m):
        return self.subx["#Q"][int(m.group(1))]

    def _f_putback_bracket(self, m):
        return self.subx["#B"][int(m.group(1))]

    @staticmethod
    def _f_notvar(m):
        return f"{m.group(1)} not in __obj"

    @staticmethod
    def _f_brackets(m):
        ret = "__obj"
        for e in m.group(1).split("."):
            ret += '["%s"]' % e
        return ret

    def parse(self, obj):
        if not isinstance(obj, (list, dict)):
            raise TypeError("obj must be a list or a dict.")

        if self.result_type == "FIELD":
            self.result = {}
        else:
            self.result = []

        self._trace(obj, 0)

        return self.result

    @staticmethod
    def _traverse(f, obj, istep: int, *args):
        if isinstance(obj, list):
            for v in obj:
                f(v, istep, *args)
        elif isinstance(obj, dict):
            for v in obj.values():
                f(v, istep, *args)

    def _filter(self, obj, istep: int, step):
        r = False
        try:
            r = eval(step, None, {"__obj": obj})
        except Exception as err:
            print(err)
        if r:
            self._trace(obj, istep)

    def _trace(self, obj, istep: int):
        """Perform operation on object.

        Args:
            obj ([type]): current operating object
            istep (int): current operation specified by index in self.steps
        """

        # store
        if istep >= self.lpath:
            self.result.append(obj)
            print(obj)
            return

        step = self.steps[istep]

        # wildcard
        if step == "*":
            self._traverse(self._trace, obj, istep + 1)
            return

        # recursive descent
        if step == "..":
            self._trace(obj, istep + 1)
            self._traverse(self._trace, obj, istep)
            return

        # get value from list
        if isinstance(obj, list) and step.isdigit():
            ikey = int(step)
            if ikey < len(obj):
                self._trace(obj[ikey], istep + 1)
            return

        # get value from dict
        if isinstance(obj, dict) and step in obj:
            self._trace(obj[step], istep + 1)
            return

        # slice
        if isinstance(obj, list) and REP_SLICE_CONTENT.fullmatch(step):
            vals = eval(f"obj[{step}]")
            for v in vals:
                self._trace(v, istep + 1)
            return

        # select
        if isinstance(obj, dict) and REP_SELECT_CONTENT.fullmatch(step):
            for k in step.split(","):
                if k in obj:
                    self._trace(obj[k], istep + 1)
            return

        # filter
        if step.startswith("?(") and step.endswith(")"):
            step = step[2:-1]
            step = REP_FILTER_CONTENT.sub(self._f_brackets, step)
            self._traverse(self._filter, obj, istep + 1, step)
            return

        # sort
        if step.startswith("/(") and step.endswith(")"):
            if isinstance(obj, list):
                step = step[2:-1]
                for sortby in step.split(",")[::-1]:
                    if sortby.startswith("~"):
                        obj.sort(
                            key=lambda t, k=sortby: _getattr(t, k[1:]), reverse=True
                        )
                    else:
                        obj.sort(key=lambda t, k=sortby: _getattr(t, k))

            self._traverse(self._trace, obj, istep + 1)
            return


if __name__ == "__main__":
    # JSONPath("$.a.'b.c'.'d e'.[f,g][h][*][j.k][l m][2:4]..d", result_type="FIELD")
    with open("test/data/2.json", "rb") as f:
        d = json.load(f)
    # JSONPath(
    #     '$.book[?(@.title=="Herman Melville" or @.title=="Evelyn Waugh")].title'
    # ).parse(d)
    # JSONPath("$..price").parse(d)
    JSONPath("$.book[/(price)].price").parse(d)
