"""Tests for envoy_lite.trimmer."""

from __future__ import annotations

import re

import pytest

from envoy_lite.trimmer import (
    TrimError,
    trim_by_pattern,
    trim_by_prefix,
    trim_keys,
)


# ---------------------------------------------------------------------------
# trim_keys
# ---------------------------------------------------------------------------


def test_trim_keys_removes_specified():
    env = {"A": "1", "B": "2", "C": "3"}
    result = trim_keys(env, ["B"])
    assert result == {"A": "1", "C": "3"}


def test_trim_keys_preserves_original():
    env = {"A": "1", "B": "2"}
    trim_keys(env, ["A"])
    assert "A" in env  # original unchanged


def test_trim_keys_multiple():
    env = {"A": "1", "B": "2", "C": "3"}
    result = trim_keys(env, ["A", "C"])
    assert result == {"B": "2"}


def test_trim_keys_missing_silent_by_default():
    env = {"A": "1"}
    result = trim_keys(env, ["MISSING"])
    assert result == {"A": "1"}


def test_trim_keys_missing_strict_raises():
    env = {"A": "1"}
    with pytest.raises(TrimError, match="MISSING"):
        trim_keys(env, ["MISSING"], strict=True)


def test_trim_keys_empty_list_returns_copy():
    env = {"A": "1"}
    result = trim_keys(env, [])
    assert result == env
    assert result is not env


# ---------------------------------------------------------------------------
# trim_by_prefix
# ---------------------------------------------------------------------------


def test_trim_by_prefix_removes_matching():
    env = {"APP_HOST": "localhost", "APP_PORT": "8080", "DB_URL": "sqlite"}
    result = trim_by_prefix(env, "APP_")
    assert result == {"DB_URL": "sqlite"}


def test_trim_by_prefix_no_match_returns_all():
    env = {"X": "1", "Y": "2"}
    result = trim_by_prefix(env, "Z_")
    assert result == env


def test_trim_by_prefix_case_insensitive():
    env = {"APP_HOST": "h", "app_port": "p", "OTHER": "o"}
    result = trim_by_prefix(env, "APP_", case_sensitive=False)
    assert result == {"OTHER": "o"}


def test_trim_by_prefix_empty_raises():
    with pytest.raises(TrimError):
        trim_by_prefix({"A": "1"}, "")


def test_trim_by_prefix_exact_key_also_removed():
    # A key that equals the prefix itself should be removed.
    env = {"APP": "1", "APP_X": "2", "OTHER": "3"}
    result = trim_by_prefix(env, "APP")
    assert "APP" not in result
    assert "APP_X" not in result
    assert result == {"OTHER": "3"}


# ---------------------------------------------------------------------------
# trim_by_pattern
# ---------------------------------------------------------------------------


def test_trim_by_pattern_basic():
    env = {"SECRET_KEY": "s", "PUBLIC_URL": "u", "SECRET_TOKEN": "t"}
    result = trim_by_pattern(env, r"^SECRET_")
    assert result == {"PUBLIC_URL": "u"}


def test_trim_by_pattern_case_flag():
    env = {"secret_key": "s", "PUBLIC": "p"}
    result = trim_by_pattern(env, r"^secret_", flags=re.IGNORECASE)
    assert result == {"PUBLIC": "p"}


def test_trim_by_pattern_no_match_returns_all():
    env = {"A": "1", "B": "2"}
    result = trim_by_pattern(env, r"^Z")
    assert result == env


def test_trim_by_pattern_invalid_pattern_raises():
    with pytest.raises(TrimError, match="Invalid pattern"):
        trim_by_pattern({"A": "1"}, r"[invalid")


def test_trim_by_pattern_preserves_original():
    env = {"SECRET": "s", "OPEN": "o"}
    trim_by_pattern(env, r"SECRET")
    assert "SECRET" in env
