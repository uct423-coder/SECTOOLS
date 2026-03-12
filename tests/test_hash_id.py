"""Tests for hash identification."""

from sectools.hash_id import HASH_TYPES


def test_md5_detection():
    md5_hash = "d41d8cd98f00b204e9800998ecf8427e"
    matches = [name for name, test, _, _ in HASH_TYPES if test(md5_hash)]
    assert "MD5" in matches


def test_sha1_detection():
    sha1_hash = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
    matches = [name for name, test, _, _ in HASH_TYPES if test(sha1_hash)]
    assert "SHA-1" in matches


def test_sha256_detection():
    sha256_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    matches = [name for name, test, _, _ in HASH_TYPES if test(sha256_hash)]
    assert "SHA-256" in matches


def test_sha512_detection():
    sha512_hash = "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
    matches = [name for name, test, _, _ in HASH_TYPES if test(sha512_hash)]
    assert "SHA-512" in matches


def test_bcrypt_detection():
    bcrypt_hash = "$2b$12$LJ3m4ys3Lk0TSwEAijNME.TBRAzeLHBEOlmCWAjFMmLx6RLYPa.0G"
    matches = [name for name, test, _, _ in HASH_TYPES if test(bcrypt_hash)]
    assert "bcrypt" in matches


def test_no_match_for_random_string():
    matches = [name for name, test, _, _ in HASH_TYPES if test("hello world")]
    assert len(matches) == 0
