"""
Author       : zhangxianbing1
Date         : 2020-12-27 09:22:14
LastEditors  : zhangxianbing1
LastEditTime : 2020-12-31 11:07:08
Description  : JSONPath
"""
__version__ = "1.0.0"
__author__ = "zhangxianbing"

import json
import logging
import os
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
REP_PICKUP_QUOTE = re.compile(r"['\"](.*?)['\"]")
REP_PICKUP_BRACKET = re.compile(r"[\[](.*?)[\]]")
REP_PUTBACK_QUOTE = re.compile(r"#Q(\d+)")
REP_PUTBACK_BRACKET = re.compile(r"#B(\d+)")
REP_DOUBLEDOTS = re.compile(r"\.\.")
REP_DOT = re.compile(r"(?<!\.)\.(?!\.)")
REP_FILTER = re.compile(r"\[(\??\(.*?\))\]")
REP_SORT = re.compile(r"\[[\\|/](.*?),\]")


# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring


def concat(x, y, con=SEP):
    return f"{x}{con}{y}"


class ExprSyntaxError(Exception):
    pass


class JSONPath:
    # annotations
    result: Iterable
    result_type: str
    caller_globals: Dict[str, Any]
    subx = defaultdict(list)
    ops: list
    oplen: int

    def __init__(self, expr: str, *, result_type="VALUE"):
        if result_type not in RESULT_TYPE:
            raise ValueError(f"result_type must be one of {tuple(RESULT_TYPE.keys())}")
        self.result_type = result_type
        self.caller_globals = sys._getframe(1).f_globals

        # parse expression
        expr = self._parse_expr(expr)
        self.ops = expr.split(SEP)
        self.oplen = len(self.ops)
        print(f"operations  : {self.ops}")

    def _parse_expr(self, expr):
        if __debug__:
            print(f"before expr : {expr}")

        expr = REP_PICKUP_QUOTE.sub(self._f_pickup_quote, expr)
        expr = REP_PICKUP_BRACKET.sub(self._f_pickup_bracket, expr)
        expr = REP_DOUBLEDOTS.sub(f"{SEP}..{SEP}", expr)
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

    def parse(self, obj):
        if not isinstance(obj, (list, dict)):
            raise TypeError("obj must be a list or a dict.")

        if self.result_type == "FIELD":
            self.result = {}
        else:
            self.result = []

        self._operate(obj, 0)

        return self.result

    def _op(self, i):
        if i < self.oplen:
            return self.ops[i]
        return None

    def _traverse(self, f, obj, idx: int):
        if isinstance(obj, list):
            for i, v in enumerate(obj):
                f(v, idx)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                f(v, idx)

    def _operate(self, obj, idx: int):
        """Perform operation on object.

        Args:
            obj ([type]): current operating object
            idx (int): current operation specified by index in self.ops
        """

        # store
        if idx >= self.oplen:
            self.result.append(obj)
            print(obj)
            return

        op = self.ops[idx]

        # wildcard
        if op == "*":
            self._traverse(self._operate, obj, idx + 1)

        # recursive descent
        elif op == "..":
            self._operate(obj, idx + 1)
            self._traverse(self._operate, obj, idx)

        # get value from dict
        elif isinstance(obj, dict) and op in obj:
            self._operate(obj[op], idx + 1)

        # get value from list
        elif isinstance(obj, list) and op.isdigit():
            ikey = int(op)
            if ikey < len(obj):
                self._operate(obj[ikey], idx + 1)

        # elif key.startswith("?(") and key.endswith(")"):  # filter
        #     pass

        # elif key:  # sort
        #     pass

        # elif key:  # slice
        #     pass


if __name__ == "__main__":
    # JSONPath("$.a.'b.c'.'d e'.[f,g][h][*][j.k][l m][2:4]..d", result_type="FIELD")
    with open("test/data/2.json", "rb") as f:
        d = json.load(f)
    # JSONPath("$.book[1].title").parse(d)
    JSONPath("$..price").parse(d)
