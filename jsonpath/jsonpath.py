"""JSONPath implementation for Python.

This module provides a lightweight JSONPath implementation with support for:
- Standard JSONPath operators ($, @, ., .., *, [])
- Filter expressions with comparison, membership, and regex operators
- Sorter expressions for ordering results
- Field extractor expressions
- Value updates via JSONPath

Example:
    >>> from jsonpath import JSONPath, search
    >>> data = {"store": {"book": [{"price": 10}, {"price": 20}]}}
    >>> JSONPath("$..price").parse(data)
    [10, 20]
    >>> search("$.store.book[0].price", data)
    [10]
"""

import ast
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

    formatter = logging.Formatter(f"%(asctime)s-%(levelname)s-[{name}] %(message)s", datefmt="[%Y-%m-%d %H:%M:%S]")

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger = create_logger("jsonpath", os.getenv("PYLOGLEVEL", "INFO"))


class ExprSyntaxError(Exception):
    """Raised when a JSONPath expression has invalid syntax.

    Examples of invalid syntax:
    - Using sorter on non-collection types
    - Using field-extractor on non-dict types
    """


class JSONPathTypeError(Exception):
    """Raised when type-related errors occur during JSONPath operations.

    Examples:
    - Comparing incompatible types during sorting (e.g., str vs int)
    - Sorting with missing keys that result in None comparisons
    """


class JSONPath:
    """JSONPath expression parser and evaluator.

    A JSONPath expression is used to navigate and extract data from JSON objects.
    This implementation supports extended syntax including filters, sorters, and
    field extractors.

    Attributes:
        RESULT_TYPE: Supported result types ('VALUE' or 'PATH').

    Example:
        >>> jp = JSONPath("$.store.book[?(@.price < 10)].title")
        >>> jp.parse({"store": {"book": [{"title": "A", "price": 5}]}})
        ['A']
    """

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
    REP_REGEX_PATTERN = re.compile(r"=~\s*/(.*?)/")
    REP_ATTR_PATH = re.compile(r"\.(\w+|'[^']*'|\"[^\"]*\")")
    REP_DOTDOT_BRACKET = re.compile(r"\.(\.#B)")
    REP_BARE_AT = re.compile(r"(?<!\w)@(?![.\[\w])")
    REGEX_BINDING_PREFIX = "__jsonpath_regex_"

    # Safe expression evaluation: allowed AST node types for filter expressions
    _ALLOWED_AST_NODES = frozenset(
        {
            ast.Expression,
            # Boolean operators
            ast.BoolOp,
            ast.And,
            ast.Or,
            # Binary operators
            ast.BinOp,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.MatMult,
            # Unary operators
            ast.UnaryOp,
            ast.Not,
            ast.UAdd,
            ast.USub,
            # Comparisons
            ast.Compare,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Is,
            ast.IsNot,
            ast.In,
            ast.NotIn,
            # Values and names
            ast.Constant,
            ast.Name,
            # Subscripts
            ast.Subscript,
            ast.Slice,
            # Collections
            ast.List,
            ast.Tuple,
            ast.Dict,
            # Attribute access (validated separately)
            ast.Attribute,
            # Function calls (validated separately)
            ast.Call,
            # Context
            ast.Load,
        }
        # Python 3.8 compatibility: deprecated AST nodes removed in 3.12
        | {getattr(ast, n) for n in ("Index", "Num", "Str", "Bytes", "NameConstant") if hasattr(ast, n)}
    )
    _ALLOWED_NAMES = frozenset({"__obj", "len", "RegexPattern"})
    _ALLOWED_CALLS = frozenset({"len", "RegexPattern"})

    def __init__(self, expr: str):
        """Initialize JSONPath with an expression.

        Args:
            expr: JSONPath expression string (e.g., "$.store.book[*].price")
        """
        # Initialize instance variables
        self.subx = defaultdict(list)
        self.segments = []
        self.lpath = 0
        self.result = []
        self.result_type = "VALUE"
        self._custom_eval_func = None

        expr = self._parse_expr(expr)
        self.segments = [s for s in expr.split(JSONPath.SEP) if s]
        self.lpath = len(self.segments)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"segments  : {self.segments}")

    def parse(self, obj, result_type="VALUE", eval_func=None):
        """Parse JSON object using the JSONPath expression.

        Args:
            obj: JSON object (dict or list) to parse
            result_type: Type of result to return
                - 'VALUE': Return matched values (default)
                - 'PATH': Return JSONPath strings of matched locations
            eval_func: Custom eval function for filter expressions.
                If None (default), uses a safe expression evaluator that
                prevents code injection. Pass a custom function only if
                you trust the JSONPath expressions being evaluated.

        Returns:
            List of matched values or paths depending on result_type

        Raises:
            TypeError: If obj is not a dict or list
            ValueError: If result_type is invalid
        """
        if not isinstance(obj, (list, dict)):
            raise TypeError("obj must be a list or a dict.")

        if result_type not in JSONPath.RESULT_TYPE:
            raise ValueError(f"result_type must be one of {tuple(JSONPath.RESULT_TYPE.keys())}")
        self.result_type = result_type
        self._custom_eval_func = eval_func

        # Reset state for each parse call
        self.result = []
        self._trace(obj, 0, "$")

        return self.result

    def search(self, obj, result_type="VALUE"):
        """Alias for parse(). Search JSON object using the JSONPath expression."""
        return self.parse(obj, result_type)

    def _parse_expr(self, expr):
        """Parse and normalize JSONPath expression into segments.

        Handles special patterns (quotes, brackets, parentheses) by temporarily
        replacing them with placeholders, then splits by dots and restores.
        """
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
        is_len = m.group(2) is not None
        content = m.group(1) or m.group(2)  # group 2 is for len()

        def repl(m):
            g = m.group(1)
            if g[0] in ("'", '"'):
                return f"[{g}]"
            return f"['{g}']"

        content = JSONPath.REP_ATTR_PATH.sub(repl, content)
        result = "__obj" + content
        if is_len:
            result = f"len({result})"
        return result

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
        # Fast check: if all chars are word chars (alphanumeric + underscore)
        if key.isidentifier() or (key and key.replace("_", "a").isalnum()):
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
        """Traverse object children and apply function to each.

        Args:
            f: Function to apply to each child element
            obj: Object to traverse (list or dict)
            i: Current segment index
            path: Current JSONPath string
            *args: Additional arguments to pass to function f
        """
        if isinstance(obj, list):
            for idx, v in enumerate(obj):
                f(v, i, JSONPath._build_path(path, idx), *args)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                f(v, i, JSONPath._build_path(path, k), *args)

    @staticmethod
    def _getattr(obj: Any, path: str, *, convert_number_str=False):
        """Get attribute value from object by dot-notation path.

        Args:
            obj: Source object (dict)
            path: Dot-separated path string (e.g., "author.name")
            convert_number_str: If True, convert numeric strings to int/float

        Returns:
            The value at the path, or _MISSING sentinel if not found
        """
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

    @staticmethod
    def _validate_filter_expr(expr, extra_names=None):
        """Validate that a filter expression only contains safe AST constructs.

        Raises ValueError if the expression contains potentially dangerous
        constructs like function calls (except len/RegexPattern), attribute
        access to dunder names, or disallowed node types.
        """
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid filter expression syntax: {e}") from e

        extra_names = frozenset(extra_names or ())
        regex_operand_nodes = {
            id(node.right)
            for node in ast.walk(tree)
            if isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.MatMult)
            and isinstance(node.right, ast.Name)
            and node.right.id in extra_names
        }

        for node in ast.walk(tree):
            node_type = type(node)
            if node_type not in JSONPath._ALLOWED_AST_NODES:
                raise ValueError(f"Disallowed expression construct: {node_type.__name__}")
            if node_type is ast.Name:
                if node.id in extra_names:
                    if id(node) not in regex_operand_nodes:
                        raise ValueError(f"Regex binding is only allowed as a regex operand: {node.id}")
                elif node.id not in JSONPath._ALLOWED_NAMES:
                    raise ValueError(f"Disallowed name in filter expression: {node.id}")
            if node_type is ast.Attribute and node.attr.startswith("_"):
                raise ValueError(f"Disallowed attribute access: {node.attr}")
            if node_type is ast.Call:
                if not (isinstance(node.func, ast.Name) and node.func.id in JSONPath._ALLOWED_CALLS):
                    raise ValueError("Only len() and RegexPattern() calls are allowed in filter expressions")

    @staticmethod
    def _safe_eval_filter(expr, obj, regex_patterns=None):
        """Safely evaluate a filter expression against an object.

        Validates the expression AST before evaluation and uses a restricted
        namespace with no access to Python builtins (defense-in-depth for
        the RCE fix — AST validation is the primary gate, restricted
        __builtins__ is the secondary gate).
        """
        regex_patterns = regex_patterns or {}
        JSONPath._validate_filter_expr(expr, regex_patterns)
        eval_locals = {"__obj": obj, "RegexPattern": RegexPattern, "len": len}
        eval_locals.update({name: RegexPattern(pattern) for name, pattern in regex_patterns.items()})
        # fmt: off
        return eval(expr, {"__builtins__": {}}, eval_locals)  # noqa: S307 — safe: AST-validated, builtins stripped
        # fmt: on

    @staticmethod
    def _parse_slice(s):
        """Parse a slice expression string into a slice object.

        Args:
            s: Slice string like '1:3', '::2', '-1:', etc.

        Returns:
            A slice object
        """
        parts = s.split(":")

        def to_int(v):
            v = v.strip()
            return int(v) if v else None

        start = to_int(parts[0]) if len(parts) > 0 else None
        stop = to_int(parts[1]) if len(parts) > 1 else None
        step = to_int(parts[2]) if len(parts) > 2 else None
        return slice(start, stop, step)

    @staticmethod
    def _replace_regex_patterns(step: str):
        regex_patterns = {}

        def replace(match):
            name = f"{JSONPath.REGEX_BINDING_PREFIX}{len(regex_patterns)}"
            regex_patterns[name] = match.group(1)
            return f"@ {name}"

        return JSONPath.REP_REGEX_PATTERN.sub(replace, step), regex_patterns

    def _filter(self, obj, i: int, path: str, step: str, regex_patterns=None):
        """Evaluate filter expression and continue trace if condition is true.

        Args:
            obj: Current object to evaluate against filter
            i: Next segment index to trace
            path: Current JSONPath string
            step: Python expression string to evaluate
            regex_patterns: Regex binding names mapped to raw pattern strings
        """
        r = False
        try:
            regex_patterns = regex_patterns or {}
            if self._custom_eval_func is not None:
                eval_locals = {"__obj": obj, "RegexPattern": RegexPattern, "len": len}
                eval_locals.update({name: RegexPattern(pattern) for name, pattern in regex_patterns.items()})
                r = self._custom_eval_func(step, None, eval_locals)
            else:
                r = self._safe_eval_filter(step, obj, regex_patterns)
        except Exception:
            pass
        if r:
            self._trace(obj, i, path)

    def _trace(self, obj, i: int, path):
        """Recursively traverse object following JSONPath segments.

        This is the core evaluation method that processes each segment of the
        parsed JSONPath expression and navigates through the object accordingly.

        Args:
            obj: Current object being traversed
            i: Index of current segment in self.segments
            path: JSONPath string representing current location
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
            indexed = list(enumerate(obj))
            vals = indexed[self._parse_slice(step)]
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
                # Replace bare @ (current element reference) with __obj
                # Must happen after REP_FILTER_CONTENT (handles @.x, @[x])
                # and before REP_REGEX_PATTERN (introduces @ as matmul operator)
                step = JSONPath.REP_BARE_AT.sub("__obj", step)

                regex_patterns = None
                if "=~" in step:
                    step, regex_patterns = JSONPath._replace_regex_patterns(step)

                if isinstance(obj, dict):
                    self._filter(obj, i + 1, path, step, regex_patterns)
                self._traverse(self._filter, obj, i + 1, path, step, regex_patterns)
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
    """Regex pattern wrapper for use with the =~ operator in filter expressions.

    This class enables regex matching syntax like: @.name =~ /pattern/
    The @ operator is overloaded to perform the regex search.

    Example:
        >>> pattern = RegexPattern(r"^test")
        >>> "testing" @ pattern
        True
    """

    def __init__(self, pattern):
        """Initialize with a regex pattern string."""
        self.pattern = pattern
        self._compiled = re.compile(pattern)  # Pre-compile for better performance

    def __rmatmul__(self, other):
        """Right matmul operator (@) - checks if other matches the pattern."""
        if isinstance(other, str):
            return bool(self._compiled.search(other))
        return False


# Global cache with LRU eviction to prevent memory leaks
_jsonpath_cache = OrderedDict()
_CACHE_MAX_SIZE = 128


def _get_cached_jsonpath(expr: str) -> JSONPath:
    """Get or create a cached JSONPath instance.

    Args:
        expr: JSONPath expression string

    Returns:
        Cached or newly created JSONPath instance
    """
    if expr in _jsonpath_cache:
        # Move to end (mark as recently used)
        _jsonpath_cache.move_to_end(expr)
    else:
        # Evict oldest if cache is full
        if len(_jsonpath_cache) >= _CACHE_MAX_SIZE:
            _jsonpath_cache.popitem(last=False)  # Remove oldest (FIFO)
        _jsonpath_cache[expr] = JSONPath(expr)
    return _jsonpath_cache[expr]


def compile(expr):
    """Compile a JSONPath expression for reuse.

    Returns a cached JSONPath instance when available, avoiding redundant parsing.

    Args:
        expr: JSONPath expression string

    Returns:
        JSONPath object that can be used to parse multiple JSON objects

    Example:
        >>> jp = compile("$.store.book[*].price")
        >>> jp.parse(data1)
        >>> jp.parse(data2)
    """
    return _get_cached_jsonpath(expr)


def search(expr, data):
    """Search JSON data using JSONPath expression with caching.

    Args:
        expr: JSONPath expression string
        data: JSON data (dict or list)

    Returns:
        List of matched values
    """
    return _get_cached_jsonpath(expr).parse(data)
