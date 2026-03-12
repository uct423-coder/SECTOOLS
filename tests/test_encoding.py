"""Tests for encoding/decoding roundtrips."""

from sectools.encoding import CODECS


def test_base64_roundtrip():
    original = "Hello, World!"
    encoded = CODECS["Base64"]["encode"](original)
    decoded = CODECS["Base64"]["decode"](encoded)
    assert decoded == original


def test_url_roundtrip():
    original = "hello world & foo=bar"
    encoded = CODECS["URL"]["encode"](original)
    decoded = CODECS["URL"]["decode"](encoded)
    assert decoded == original


def test_hex_roundtrip():
    original = "test123"
    encoded = CODECS["Hex"]["encode"](original)
    decoded = CODECS["Hex"]["decode"](encoded)
    assert decoded == original


def test_rot13_roundtrip():
    original = "Hello"
    encoded = CODECS["ROT13"]["encode"](original)
    decoded = CODECS["ROT13"]["decode"](encoded)
    assert decoded == original


def test_html_roundtrip():
    original = '<script>alert("xss")</script>'
    encoded = CODECS["HTML Entities"]["encode"](original)
    decoded = CODECS["HTML Entities"]["decode"](encoded)
    assert decoded == original


def test_binary_roundtrip():
    original = "ABC"
    encoded = CODECS["Binary"]["encode"](original)
    decoded = CODECS["Binary"]["decode"](encoded)
    assert decoded == original
