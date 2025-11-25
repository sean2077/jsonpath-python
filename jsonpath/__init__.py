"""
JSONPath
========

A more powerful JSONPath implementation in modern python.
"""

from importlib.metadata import version

__version__ = version("jsonpath-python")

from .jsonpath import ExprSyntaxError, JSONPath, JSONPathTypeError, compile, search

__all__ = ["JSONPath", "ExprSyntaxError", "JSONPathTypeError", "compile", "search"]
