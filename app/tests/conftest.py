"""Pytest configuration and fixtures."""

import os
import pytest


@pytest.fixture
def sample_csv_path():
    """Return path to sample CSV file."""
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'sample.csv')


@pytest.fixture
def sample_csv_content(sample_csv_path):
    """Return content of sample CSV file."""
    with open(sample_csv_path, 'r') as f:
        return f.read()
