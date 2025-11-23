"""
JSONPath
========

A more powerful JSONPath implementation in modern python.
"""

__version__ = "1.1.1"

from .jsonpath import ExprSyntaxError, JSONPath, JSONPathTypeError, compile, search

__all__ = ["JSONPath", "ExprSyntaxError", "JSONPathTypeError", "compile", "search"]
