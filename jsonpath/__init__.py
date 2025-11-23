"""
JSONPath
========

A more powerful JSONPath implementation in modern python.
"""

__version__ = "1.0.6"
__author__ = "sean2077"

from .jsonpath import ExprSyntaxError, JSONPath, JSONPathTypeError, compile, search

__all__ = ["JSONPath", "ExprSyntaxError", "JSONPathTypeError", "compile", "search"]
