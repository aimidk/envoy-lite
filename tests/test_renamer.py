"""Tests for envoy_lite.renamer."""

from __future__ import annotations

import pytest

from envoy_lite.renamer import (
    RenameError,
    rename_key,
    rename_prefix,
    apply_rename_map,
)


# ---------------------------------------------------------------------------
# rename_key
# ---------------------------------------------------------------------------

def test_rename_key_basic():
    result = rename_key({"FOO": "bar"}, "FOO", "BAZ")
    assert result == {"BAZ": "bar"}


def test_rename_key_preserves_other_keys():
    env = {"A": "1", "B": "2", "C": "3"}
    result = rename_key(env, "B", "X")
    assert result == {"A": "1", "X": "2", "C": "3"}


def test_rename_key_missing_raises():
    with pytest.raises(RenameError, match="Key not found"):
        rename_key({"A": "1"}, "MISSING", "B")


def test_rename_key_collision_raises():
    with pytest.raises(RenameError, match="already exists"):
        rename_key({"A": "1", "B": "2"}, "A", "B")


def test_rename_key_collision_overwrite():
    result = rename_key({"A": "1", "B": "2"}, "A", "B", overwrite=True)
    assert result == {"B": "1"}


def test_rename_key_does_not_mutate_original():
    env = {"FOO": "bar"}
    rename_key(env, "FOO", "BAZ")
    assert "FOO" in env


# ---------------------------------------------------------------------------
# rename_prefix
# ---------------------------------------------------------------------------

def test_rename_prefix_basic():
    env = {"APP_HOST": "localhost", "APP_PORT": "8080", "OTHER": "x"}
    result = rename_prefix(env, "APP_", "SVC_")
    assert result == {"SVC_HOST": "localhost", "SVC_PORT": "8080", "OTHER": "x"}


def test_rename_prefix_no_matches_returns_copy():
    env = {"FOO": "1", "BAR": "2"}
    result = rename_prefix(env, "MISSING_", "NEW_")
    assert result == env
    assert result is not env


def test_rename_prefix_collision_raises():
    env = {"APP_X": "1", "SVC_X": "2"}
    with pytest.raises(RenameError, match="collision"):
        rename_prefix(env, "APP_", "SVC_")


def test_rename_prefix_collision_overwrite():
    env = {"APP_X": "new", "SVC_X": "old"}
    result = rename_prefix(env, "APP_", "SVC_", overwrite=True)
    assert result["SVC_X"] == "new"


# ---------------------------------------------------------------------------
# apply_rename_map
# ---------------------------------------------------------------------------

def test_apply_rename_map_basic():
    env = {"A": "1", "B": "2"}
    result = apply_rename_map(env, {"A": "X", "B": "Y"})
    assert result == {"X": "1", "Y": "2"}


def test_apply_rename_map_missing_raises_by_default():
    with pytest.raises(RenameError, match="Key not found"):
        apply_rename_map({"A": "1"}, {"MISSING": "NEW"})


def test_apply_rename_map_skip_missing():
    result = apply_rename_map({"A": "1"}, {"MISSING": "NEW"}, skip_missing=True)
    assert result == {"A": "1"}


def test_apply_rename_map_empty_mapping():
    env = {"A": "1"}
    result = apply_rename_map(env, {})
    assert result == env
