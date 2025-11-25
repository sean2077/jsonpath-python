"""Shared fixtures for jsonpath-python tests."""

import json

import pytest


@pytest.fixture(scope="session")
def sample_data():
    """Standard test data for JSONPath tests."""
    with open("tests/data/2.json", "rb") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def large_data():
    """Large test data for performance tests."""
    with open("tests/data/1.json") as f:
        return json.load(f)
