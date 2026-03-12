"""Tests for configuration loading and migration."""

import json
from unittest.mock import patch
from pathlib import Path
from sectools.config import load_config, _migrate_config, DEFAULT_CONFIG


def test_default_config_has_required_keys():
    required = ["default_wordlist", "notifications_enabled", "theme_color", "log_retention_days"]
    for key in required:
        assert key in DEFAULT_CONFIG


def test_migrate_config_fixes_bare_wordlist():
    config = {"default_wordlist": "rockyou.txt", "default_dirwordlist": "common.txt"}
    changed = _migrate_config(config)
    assert changed is True
    assert "/" in config["default_wordlist"]


def test_migrate_config_no_change_needed():
    config = dict(DEFAULT_CONFIG)
    changed = _migrate_config(config)
    assert changed is False


def test_load_config_returns_defaults_when_no_file(tmp_path):
    fake_path = tmp_path / "nonexistent.json"
    with patch("sectools.config.CONFIG_PATH", fake_path):
        config = load_config()
    assert config["theme_color"] == "cyan"
    assert config["notifications_enabled"] is True
