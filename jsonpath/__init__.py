"""
JSONPath
========

A lightweight and powerful JSONPath implementation for Python.
"""

from importlib.metadata import version

__version__ = version("jsonpath-python")

from .jsonpath import ExprSyntaxError, JSONPath, JSONPathTypeError, compile, search

__all__ = ["JSONPath", "ExprSyntaxError", "JSONPathTypeError", "compile", "search"]
