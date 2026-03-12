"""Tests for sectools.utils helper functions."""

from sectools.utils import extract_hostname, check_installed


def test_extract_hostname_plain():
    hostname, modified = extract_hostname("example.com")
    assert hostname == "example.com"
    assert modified is False


def test_extract_hostname_with_scheme():
    hostname, modified = extract_hostname("https://example.com/path")
    assert hostname == "example.com"
    assert modified is True


def test_extract_hostname_http():
    hostname, modified = extract_hostname("http://10.0.0.1:8080/test")
    assert hostname == "10.0.0.1"
    assert modified is True


def test_extract_hostname_strips_whitespace():
    hostname, modified = extract_hostname("  example.com  ")
    assert hostname == "example.com"
    assert modified is False


def test_check_installed_python():
    """Python should always be installed."""
    assert check_installed("python3") is True or check_installed("python") is True


def test_check_installed_nonexistent():
    assert check_installed("nonexistent_tool_xyz_12345") is False
