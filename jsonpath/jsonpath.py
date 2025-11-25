import logging
import os
import re
from collections import OrderedDict, defaultdict
from typing import Any, Callable, Union


def create_logger(name: str = None, level: Union[int, str] = logging.INFO):
    """Get or create a logger used for local debug."""
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    formater = logging.Formatter(f"%(asctime)s-%(levelname)s-[{name}] %(message)s", datefmt="[%Y-%m-%d %H:%M:%S]")

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formater)

    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger = create_logger("jsonpath", os.getenv("PYLOGLEVEL", "INFO"))


class ExprSyntaxError(Exception):
    pass


class JSONPathTypeError(Exception):
    pass


class JSONPath:
    RESULT_TYPE = {
        "VALUE": "A list of specific values.",
        "PATH": "All path of specific values.",
    }

    _MISSING = object()

    # common patterns
    SEP = ";"
    SEP_DOUBLEDOT = ";..;"  # Pre-computed for better performance
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
    REP_FILTER_CONTENT = re.compile(r"@([.\[].*?)(?=<=|>=|==|!=|>|<| in| not| is|\s|\)|$)|len\(@([.\[].*?)\)")
    REP_PATH_SEGMENT = re.compile(r"(?:\.|^)(?P<dot>\w+)|\[['\"](?P<quote>.*?)['\"]\]|\[(?P<int>\d+)\]")
    REP_WORD_KEY = re.compile(r"^\w+$")
    REP_REGEX_PATTERN = re.compile(r"=~\s*/(.*?)/")
    REP_ATTR_PATH = re.compile(r"\.(\w+|'[^']*'|\"[^\"]*\")")
    REP_DOTDOT_BRACKET = re.compile(r"\.(\.#B)")

    def __init__(self, expr: str):
        # Initialize instance variables
        self.subx = defaultdict(list)
        self.segments = []
        self.lpath = 0
        self.result = []
        self.result_type = "VALUE"
        self.eval_func = eval

        expr = self._parse_expr(expr)
        self.segments = [s for s in expr.split(JSONPath.SEP) if s]
        self.lpath = len(self.segments)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"segments  : {self.segments}")

    def parse(self, obj, result_type="VALUE", eval_func=eval):
        if not isinstance(obj, (list, dict)):
            raise TypeError("obj must be a list or a dict.")

        if result_type not in JSONPath.RESULT_TYPE:
            raise ValueError(f"result_type must be one of {tuple(JSONPath.RESULT_TYPE.keys())}")
        self.result_type = result_type
        self.eval_func = eval_func

        # Reset state for each parse call
        self.result = []
        self._trace(obj, 0, "$")

        return self.result

    def search(self, obj, result_type="VALUE"):
        return self.parse(obj, result_type)

    def _parse_expr(self, expr):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"before expr : {expr}")
        # pick up special patterns
        expr = JSONPath.REP_GET_QUOTE.sub(self._get_quote, expr)
        expr = JSONPath.REP_GET_BACKQUOTE.sub(self._get_backquote, expr)
        expr = JSONPath.REP_GET_PAREN.sub(self._get_paren, expr)
        expr = JSONPath.REP_GET_BRACKET.sub(self._get_bracket, expr)
        expr = JSONPath.REP_DOTDOT_BRACKET.sub(r"\1", expr)
        # split
        expr = JSONPath.REP_DOUBLEDOT.sub(JSONPath.SEP_DOUBLEDOT, expr)
        expr = JSONPath.REP_DOT.sub(JSONPath.SEP, expr)
        # put back
        expr = JSONPath.REP_PUT_BRACKET.sub(self._put_bracket, expr)
        expr = JSONPath.REP_PUT_PAREN.sub(self._put_paren, expr)
        expr = JSONPath.REP_PUT_BACKQUOTE.sub(self._put_backquote, expr)
        expr = JSONPath.REP_PUT_QUOTE.sub(self._put_quote, expr)
        if expr == "$":
            expr = ""
        elif expr.startswith("$;"):
            expr = expr[2:]

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"after expr  : {expr}")
        return expr

    def _save_pattern(self, pattern_type: str, content: str, wrapper: str = "") -> str:
        """Save pattern content and return placeholder.

        Args:
            pattern_type: Pattern identifier (e.g., '#Q', '#BQ', '#B', '#P')
            content: Content to save
            wrapper: Optional wrapper format string (e.g., "'{}'", "`{}`")

        Returns:
            Placeholder string
        """
        n = len(self.subx[pattern_type])
        self.subx[pattern_type].append(content)
        if wrapper:
            return wrapper.format(f"{pattern_type}{n}")
        return f"{pattern_type}{n}"

    def _restore_pattern(self, pattern_type: str, index: str, wrapper: str = "") -> str:
        """Restore pattern content from placeholder.

        Args:
            pattern_type: Pattern identifier (e.g., '#Q', '#BQ', '#B', '#P')
            index: Index as string
            wrapper: Optional wrapper format string (e.g., "'{}'", "`{}`")

        Returns:
            Original content with optional wrapper
        """
        content = self.subx[pattern_type][int(index)]
        if wrapper:
            return wrapper.format(content)
        return content

    def _get_quote(self, m):
        return self._save_pattern("#Q", m.group(1))

    def _put_quote(self, m):
        return self._restore_pattern("#Q", m.group(1), "'{}'")

    def _get_backquote(self, m):
        return self._save_pattern("#BQ", m.group(1), "`{}`")

    def _put_backquote(self, m):
        return self._restore_pattern("#BQ", m.group(1))

    def _get_bracket(self, m):
        return "." + self._save_pattern("#B", m.group(1))

    def _put_bracket(self, m):
        return self._restore_pattern("#B", m.group(1))

    def _get_paren(self, m):
        return "(" + self._save_pattern("#P", m.group(1)) + ")"

    def _put_paren(self, m):
        return self._restore_pattern("#P", m.group(1))

    @staticmethod
    def _gen_obj(m):
        content = m.group(1) or m.group(2)  # group 2 is for len()

        def repl(m):
            g = m.group(1)
            if g[0] in ("'", '"'):
                return f"[{g}]"
            return f"['{g}']"

        content = JSONPath.REP_ATTR_PATH.sub(repl, content)
        return "__obj" + content

    @staticmethod
    def _build_path(path: str, key) -> str:
        """Build JSON path string for a given key.

        Args:
            path: Current path string
            key: Key (string) or index (int)

        Returns:
            Formatted path string
        """
        if isinstance(key, int):
            return f"{path}[{key}]"
        if JSONPath.REP_WORD_KEY.match(key):
            return f"{path}.{key}"
        return f"{path}['{key}']"

    @staticmethod
    def _extract_key_from_group(group: dict):
        """Extract key from regex match group dictionary.

        Args:
            group: Match group dictionary with 'dot', 'quote', or 'int' keys

        Returns:
            Key as string or int
        """
        if group["dot"]:
            return group["dot"]
        if group["quote"]:
            return group["quote"]
        if group["int"]:
            return int(group["int"])
        return None

    @staticmethod
    def _traverse(f, obj, i: int, path: str, *args):
        if isinstance(obj, list):
            for idx, v in enumerate(obj):
                f(v, i, JSONPath._build_path(path, idx), *args)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                f(v, i, JSONPath._build_path(path, k), *args)

    @staticmethod
    def _getattr(obj: Any, path: str, *, convert_number_str=False):
        # Fast path for single key (most common case)
        if "." not in path:
            if isinstance(obj, dict) and path in obj:
                r = obj[path]
            else:
                return JSONPath._MISSING
        else:
            # Multi-level path
            r = obj
            for k in path.split("."):
                if isinstance(r, dict):
                    if k in r:
                        r = r[k]
                    else:
                        return JSONPath._MISSING
                else:
                    return JSONPath._MISSING

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
        """Sort objects by multiple fields using stable sort."""

        def key_func(t, k):
            v = JSONPath._getattr(t[1], k, convert_number_str=True)
            return v if v is not JSONPath._MISSING else None

        try:
            for sortby in sortbys.split(",")[::-1]:
                sortby = sortby.strip()
                if sortby.startswith("~"):
                    obj.sort(
                        key=lambda t, k=sortby: key_func(t, k[1:]),
                        reverse=True,
                    )
                else:
                    obj.sort(key=lambda t, k=sortby: key_func(t, k))
        except TypeError as e:
            raise JSONPathTypeError(f"not possible to compare str and int when sorting: {e}") from e

    def _filter(self, obj, i: int, path: str, step: str):
        r = False
        try:
            r = self.eval_func(step, None, {"__obj": obj, "RegexPattern": RegexPattern})
        except Exception:
            pass
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
            if logger.isEnabledFor(logging.DEBUG):
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
                self._trace(obj[ikey], i + 1, f"{path}[{step}]")
            return

        # get value from dict
        step_key = step[1:-1] if (len(step) >= 2 and step[0] == "'" and step[-1] == "'") else step

        if isinstance(obj, dict) and step_key in obj:
            self._trace(obj[step_key], i + 1, self._build_path(path, step_key))
            return

        # slice
        if isinstance(obj, list) and JSONPath.REP_SLICE_CONTENT.fullmatch(step):
            obj = list(enumerate(obj))
            vals = self.eval_func(f"obj[{step}]")
            for idx, v in vals:
                self._trace(v, i + 1, f"{path}[{idx}]")
            return

        # select
        if isinstance(obj, dict) and JSONPath.REP_SELECT_CONTENT.fullmatch(step):
            for k in step.split(","):
                k = k.strip()  # Remove whitespace
                if k in obj:
                    self._trace(obj[k], i + 1, self._build_path(path, k))
            return

        # filter and sorter - check first char for efficiency
        if step and step[0] in "?/" and step.endswith(")"):
            if step.startswith("?("):
                # filter
                step = step[2:-1]
                step = JSONPath.REP_FILTER_CONTENT.sub(self._gen_obj, step)

                if "=~" in step:
                    step = JSONPath.REP_REGEX_PATTERN.sub(r"@ RegexPattern(r'\1')", step)

                if isinstance(obj, dict):
                    self._filter(obj, i + 1, path, step)
                self._traverse(self._filter, obj, i + 1, path, step)
                return

            if step.startswith("/("):
                # sorter
                if isinstance(obj, list):
                    obj = list(enumerate(obj))
                    self._sorter(obj, step[2:-1])
                    for idx, v in obj:
                        self._trace(v, i + 1, self._build_path(path, idx))
                elif isinstance(obj, dict):
                    obj = list(obj.items())
                    self._sorter(obj, step[2:-1])
                    for k, v in obj:
                        self._trace(v, i + 1, self._build_path(path, k))
                else:
                    raise ExprSyntaxError("sorter must acting on list or dict")
                return

        # field-extractor
        if step and step[0] == "(" and step.endswith(")"):
            if isinstance(obj, dict):
                obj_ = {}
                for k in step[1:-1].split(","):
                    k = k.strip()  # Remove whitespace
                    v = self._getattr(obj, k)
                    if v is not JSONPath._MISSING:
                        obj_[k] = v
                self._trace(obj_, i + 1, path)
            else:
                raise ExprSyntaxError("field-extractor must acting on dict")

            return

    def update(self, obj: Union[list, dict], value_or_func: Union[Any, Callable[[Any], Any]]) -> Any:
        """Update values in JSON object using JSONPath expression.

        Args:
            obj: JSON object (dict or list) to update
            value_or_func: Static value or callable that transforms the current value

        Returns:
            Updated object (modified in-place for nested paths, returns new value for root)
        """
        paths = self.parse(obj, result_type="PATH")
        is_func = callable(value_or_func)

        # Handle root object update specially
        if len(paths) == 1 and paths[0] == "$":
            return value_or_func(obj) if is_func else value_or_func

        for path in paths:
            matches = list(JSONPath.REP_PATH_SEGMENT.finditer(path))
            if not matches:
                continue

            target = obj
            # Traverse to parent
            for match in matches[:-1]:
                key = self._extract_key_from_group(match.groupdict())
                target = target[key]

            # Update last segment
            key = self._extract_key_from_group(matches[-1].groupdict())
            target[key] = value_or_func(target[key]) if is_func else value_or_func

        return obj


class RegexPattern:
    def __init__(self, pattern):
        self.pattern = pattern
        self._compiled = re.compile(pattern)  # Pre-compile for better performance

    def __rmatmul__(self, other):
        if isinstance(other, str):
            return bool(self._compiled.search(other))
        return False


def compile(expr):
    return JSONPath(expr)


# global cache with LRU eviction to prevent memory leaks
_jsonpath_cache = OrderedDict()
_CACHE_MAX_SIZE = 128


def search(expr, data):
    """Search JSON data using JSONPath expression with LRU caching.

    Args:
        expr: JSONPath expression string
        data: JSON data (dict or list)

    Returns:
        List of matched values
    """
    if expr in _jsonpath_cache:
        # Move to end (mark as recently used)
        _jsonpath_cache.move_to_end(expr)
    else:
        # Evict oldest if cache is full
        if len(_jsonpath_cache) >= _CACHE_MAX_SIZE:
            _jsonpath_cache.popitem(last=False)  # Remove oldest (FIFO)
        _jsonpath_cache[expr] = JSONPath(expr)
    return _jsonpath_cache[expr].parse(data)
