"""
Author       : zhangxianbing
Date         : 2020-12-27 09:22:14
LastEditors  : zhangxianbing
LastEditTime : 2022-03-14 10:33:55
Description  : JSONPath
"""
__version__ = "1.0.6"
__author__ = "zhangxianbing"

import json
import logging
import os
import re
import sys
from collections import defaultdict
from typing import Union


def create_logger(name: str = None, level: Union[int, str] = logging.INFO):
    """Get or create a logger used for local debug."""

    formater = logging.Formatter(
        f"%(asctime)s-%(levelname)s-[{name}] %(message)s", datefmt="[%Y-%m-%d %H:%M:%S]"
    )

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formater)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger = create_logger("jsonpath", os.getenv("PYLOGLEVEL", "INFO"))


class ExprSyntaxError(Exception):
    pass


class JSONPath:
    RESULT_TYPE = {
        "VALUE": "A list of specific values.",
        "PATH": "All path of specific values.",
    }

    # common patterns
    SEP = ";"
    REP_DOUBLEDOT = re.compile(r"\.\.")
    REP_DOT = re.compile(r"(?<!\.)\.(?!\.)")

    # save special patterns
    REP_GET_QUOTE = re.compile(r"['](.*?)[']")
    REP_PUT_QUOTE = re.compile(r"#Q(\d+)")
    REP_GET_BACKQUOTE = re.compile(r"[`](.*?)[`]")
    REP_PUT_BACKQUOTE = re.compile(r"#BQ(\d+)")
    REP_GET_BRACKET = re.compile(r"[\[](.*?)[\]]")
    REP_PUT_BRACKET = re.compile(r"#B(\d+)")
    REP_GET_PAREN = re.compile(r"[\(](.*?)[\)]")
    REP_PUT_PAREN = re.compile(r"#P(\d+)")

    # operators
    REP_SLICE_CONTENT = re.compile(r"^(-?\d*)?:(-?\d*)?(:-?\d*)?$")
    REP_SELECT_CONTENT = re.compile(r"^([\w.']+)(, ?[\w.']+)+$")
    REP_FILTER_CONTENT = re.compile(
        r"@\.(.*?)(?=<=|>=|==|!=|>|<| in| not| is)|len\(@\.(.*?)\)"
    )

    # annotations
    f: list
    segments: list
    lpath: int
    subx = defaultdict(list)
    result: list
    result_type: str
    eval_func: callable

    def __init__(self, expr: str):
        expr = self._parse_expr(expr)
        self.segments = expr.split(JSONPath.SEP)
        self.lpath = len(self.segments)
        logger.debug(f"segments  : {self.segments}")

        self.caller_globals = sys._getframe(1).f_globals

    def parse(self, obj, result_type="VALUE", eval_func=eval):
        if not isinstance(obj, (list, dict)):
            raise TypeError("obj must be a list or a dict.")

        if result_type not in JSONPath.RESULT_TYPE:
            raise ValueError(
                f"result_type must be one of {tuple(JSONPath.RESULT_TYPE.keys())}"
            )
        self.result_type = result_type
        self.eval_func = eval_func

        self.result = []
        self._trace(obj, 0, "$")

        return self.result

    def search(self, obj, result_type="VALUE"):
        return self.parse(obj, result_type)

    def _parse_expr(self, expr):
        logger.debug(f"before expr : {expr}")
        # pick up special patterns
        expr = JSONPath.REP_GET_QUOTE.sub(self._get_quote, expr)
        expr = JSONPath.REP_GET_BACKQUOTE.sub(self._get_backquote, expr)
        expr = JSONPath.REP_GET_BRACKET.sub(self._get_bracket, expr)
        expr = JSONPath.REP_GET_PAREN.sub(self._get_paren, expr)
        # split
        expr = JSONPath.REP_DOUBLEDOT.sub(f"{JSONPath.SEP}..{JSONPath.SEP}", expr)
        expr = JSONPath.REP_DOT.sub(JSONPath.SEP, expr)
        # put back
        expr = JSONPath.REP_PUT_PAREN.sub(self._put_paren, expr)
        expr = JSONPath.REP_PUT_BRACKET.sub(self._put_bracket, expr)
        expr = JSONPath.REP_PUT_BACKQUOTE.sub(self._put_backquote, expr)
        expr = JSONPath.REP_PUT_QUOTE.sub(self._put_quote, expr)
        if expr.startswith("$;"):
            expr = expr[2:]

        logger.debug(f"after expr  : {expr}")
        return expr

    # TODO abstract get and put procedures
    def _get_quote(self, m):
        n = len(self.subx["#Q"])
        self.subx["#Q"].append(m.group(1))
        return f"#Q{n}"

    def _put_quote(self, m):
        return self.subx["#Q"][int(m.group(1))]

    def _get_backquote(self, m):
        n = len(self.subx["#BQ"])
        self.subx["#BQ"].append(m.group(1))
        return f"`#BQ{n}`"

    def _put_backquote(self, m):
        return self.subx["#BQ"][int(m.group(1))]

    def _get_bracket(self, m):
        n = len(self.subx["#B"])
        self.subx["#B"].append(m.group(1))
        return f".#B{n}"

    def _put_bracket(self, m):
        return self.subx["#B"][int(m.group(1))]

    def _get_paren(self, m):
        n = len(self.subx["#P"])
        self.subx["#P"].append(m.group(1))
        return f"(#P{n})"

    def _put_paren(self, m):
        return self.subx["#P"][int(m.group(1))]

    @staticmethod
    def _gen_obj(m):
        ret = "__obj"
        for e in m.group(1).split("."):
            ret += '["%s"]' % e
        return ret

    @staticmethod
    def _traverse(f, obj, i: int, path: str, *args):
        if isinstance(obj, list):
            for idx, v in enumerate(obj):
                f(v, i, f"{path}{JSONPath.SEP}{idx}", *args)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                f(v, i, f"{path}{JSONPath.SEP}{k}", *args)

    @staticmethod
    def _getattr(obj: dict, path: str, *, convert_number_str=False):
        r = obj
        for k in path.split("."):
            try:
                r = r.get(k)
            except (AttributeError, KeyError) as err:
                logger.error(err)
                return None
        if convert_number_str and isinstance(r, str):
            try:
                if r.isdigit():
                    return int(r)
                return float(r)
            except ValueError:
                pass
        return r

    @staticmethod
    def _sorter(obj, sortbys):
        for sortby in sortbys.split(",")[::-1]:
            if sortby.startswith("~"):
                obj.sort(
                    key=lambda t, k=sortby: JSONPath._getattr(
                        t[1], k[1:], convert_number_str=True
                    ),
                    reverse=True,
                )
            else:
                obj.sort(
                    key=lambda t, k=sortby: JSONPath._getattr(
                        t[1], k, convert_number_str=True
                    )
                )

    def _filter(self, obj, i: int, path: str, step: str):
        r = False
        try:
            r = self.eval_func(step, None, {"__obj": obj})
        except Exception as err:
            logger.error(err)
        if r:
            self._trace(obj, i, path)

    def _trace(self, obj, i: int, path):
        """Perform operation on object.

        Args:
            obj ([type]): current operating object
            i (int): current operation specified by index in self.segments
        """

        # store
        if i >= self.lpath:
            if self.result_type == "VALUE":
                self.result.append(obj)
            elif self.result_type == "PATH":
                self.result.append(path)
            logger.debug(f"path: {path} | value: {obj}")
            return

        step = self.segments[i]

        # wildcard
        if step == "*":
            self._traverse(self._trace, obj, i + 1, path)
            return

        # recursive descent
        if step == "..":
            self._trace(obj, i + 1, path)
            self._traverse(self._trace, obj, i, path)
            return

        # get value from list
        if isinstance(obj, list) and step.isdigit():
            ikey = int(step)
            if ikey < len(obj):
                self._trace(obj[ikey], i + 1, f"{path}{JSONPath.SEP}{step}")
            return

        # get value from dict
        if isinstance(obj, dict) and step in obj:
            self._trace(obj[step], i + 1, f"{path}{JSONPath.SEP}{step}")
            return

        # slice
        if isinstance(obj, list) and JSONPath.REP_SLICE_CONTENT.fullmatch(step):
            obj = list(enumerate(obj))
            vals = self.eval_func(f"obj[{step}]")
            for idx, v in vals:
                self._trace(v, i + 1, f"{path}{JSONPath.SEP}{idx}")
            return

        # select
        if isinstance(obj, dict) and JSONPath.REP_SELECT_CONTENT.fullmatch(step):
            for k in step.split(","):
                if k in obj:
                    self._trace(obj[k], i + 1, f"{path}{JSONPath.SEP}{k}")
            return

        # filter
        if step.startswith("?(") and step.endswith(")"):
            step = step[2:-1]
            step = JSONPath.REP_FILTER_CONTENT.sub(self._gen_obj, step)
            self._traverse(self._filter, obj, i + 1, path, step)
            return

        # sorter
        if step.startswith("/(") and step.endswith(")"):
            if isinstance(obj, list):
                obj = list(enumerate(obj))
                self._sorter(obj, step[2:-1])
                for idx, v in obj:
                    self._trace(v, i + 1, f"{path}{JSONPath.SEP}{idx}")
            elif isinstance(obj, dict):
                obj = list(obj.items())
                self._sorter(obj, step[2:-1])
                for k, v in obj:
                    self._trace(v, i + 1, f"{path}{JSONPath.SEP}{k}")
            else:
                raise ExprSyntaxError("sorter must acting on list or dict")
            return

        # field-extractor
        if step.startswith("(") and step.endswith(")"):
            if isinstance(obj, dict):
                obj_ = {}
                for k in step[1:-1].split(","):
                    obj_[k] = self._getattr(obj, k)
                self._trace(obj_, i + 1, path)
            else:
                raise ExprSyntaxError("field-extractor must acting on dict")

            return


def compile(expr):
    return JSONPath(expr)


# global cache
_jsonpath_cache = {}


def search(expr, data):
    global _jsonpath_cache
    if expr not in _jsonpath_cache:
        _jsonpath_cache[expr] = JSONPath(expr)
    return _jsonpath_cache[expr].parse(data)


if __name__ == "__main__":
    with open("test/data/2.json", "rb") as f:
        d = json.load(f)
    D = JSONPath("$.scores[/(score)].(score)").parse(d, "VALUE")
    print(D)
    for v in D:
        print(v)
