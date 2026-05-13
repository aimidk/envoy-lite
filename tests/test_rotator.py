"""Tests for envoy_lite.rotator."""
from __future__ import annotations

import pytest

from envoy_lite.rotator import (
    RotationError,
    _versioned,
    current_version,
    list_versions,
    rollback,
    rotate_key,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def test_versioned_format():
    assert _versioned("DB_URL", 1) == "DB_URL_v1"
    assert _versioned("DB_URL", 10) == "DB_URL_v10"


def test_current_version_empty_env():
    assert current_version("DB_URL", {}) == 0


def test_current_version_with_archives():
    env = {"DB_URL": "live", "DB_URL_v1": "old1", "DB_URL_v3": "old3"}
    assert current_version("DB_URL", env) == 3


# ---------------------------------------------------------------------------
# rotate_key
# ---------------------------------------------------------------------------

def test_rotate_key_archives_old_value():
    env = {"DB_URL": "postgres://old"}
    result = rotate_key("DB_URL", "postgres://new", env)
    assert result["DB_URL"] == "postgres://new"
    assert result["DB_URL_v1"] == "postgres://old"


def test_rotate_key_no_existing_value():
    result = rotate_key("DB_URL", "postgres://first", {})
    assert result["DB_URL"] == "postgres://first"
    # No archive entry because there was nothing to archive
    assert "DB_URL_v1" not in result


def test_rotate_key_increments_version():
    env = {"DB_URL": "v2val", "DB_URL_v1": "v1val"}
    result = rotate_key("DB_URL", "v3val", env)
    assert result["DB_URL_v2"] == "v2val"
    assert result["DB_URL_v1"] == "v1val"
    assert result["DB_URL"] == "v3val"


def test_rotate_key_prunes_oldest_beyond_keep():
    env = {
        "DB_URL": "current",
        "DB_URL_v1": "oldest",
        "DB_URL_v2": "middle",
        "DB_URL_v3": "recent",
    }
    result = rotate_key("DB_URL", "newest", env, keep=3)
    assert "DB_URL_v1" not in result
    assert "DB_URL_v2" in result
    assert "DB_URL_v3" in result
    assert "DB_URL_v4" in result


def test_rotate_key_does_not_mutate_original():
    env = {"DB_URL": "original"}
    rotate_key("DB_URL", "new", env)
    assert env == {"DB_URL": "original"}


def test_rotate_key_empty_key_raises():
    with pytest.raises(RotationError, match="must not be empty"):
        rotate_key("", "val", {})


def test_rotate_key_keep_less_than_one_raises():
    with pytest.raises(RotationError, match="keep must be"):
        rotate_key("KEY", "val", {}, keep=0)


# ---------------------------------------------------------------------------
# list_versions
# ---------------------------------------------------------------------------

def test_list_versions_empty():
    assert list_versions("DB_URL", {}) == []


def test_list_versions_sorted():
    env = {"DB_URL_v3": "c", "DB_URL_v1": "a", "DB_URL_v2": "b"}
    result = list_versions("DB_URL", env)
    assert result == [(1, "a"), (2, "b"), (3, "c")]


# ---------------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------------

def test_rollback_one_step():
    env = {"DB_URL": "current", "DB_URL_v1": "previous"}
    result = rollback("DB_URL", env)
    assert result["DB_URL"] == "previous"
    assert "DB_URL_v1" not in result


def test_rollback_two_steps():
    env = {"DB_URL": "c", "DB_URL_v1": "a", "DB_URL_v2": "b"}
    result = rollback("DB_URL", env, steps=2)
    assert result["DB_URL"] == "a"
    assert "DB_URL_v1" not in result
    assert "DB_URL_v2" in result


def test_rollback_not_enough_versions_raises():
    env = {"DB_URL": "current"}
    with pytest.raises(RotationError, match="only 0 version"):
        rollback("DB_URL", env)


def test_rollback_steps_zero_raises():
    with pytest.raises(RotationError, match="steps must be"):
        rollback("KEY", {}, steps=0)


def test_rollback_does_not_mutate_original():
    env = {"DB_URL": "current", "DB_URL_v1": "old"}
    rollback("DB_URL", env)
    assert env["DB_URL"] == "current"
    assert "DB_URL_v1" in env
