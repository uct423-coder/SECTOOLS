"""Shared test fixtures."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def mock_console():
    """Return a mock Rich Console."""
    console = MagicMock()
    console.print = MagicMock()
    console.rule = MagicMock()
    return console


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config file and patch CONFIG_PATH."""
    config_file = tmp_path / "config.json"
    config_file.write_text("{}")
    return config_file
