"""Edge-case tests for envoy_lite.rotator."""
from __future__ import annotations

import pytest

from envoy_lite.rotator import (
    RotationError,
    current_version,
    list_versions,
    rotate_key,
    rollback,
)


def test_rotate_key_with_underscore_in_name():
    """Keys that already contain underscores should version correctly."""
    env = {"MY_DB_URL": "old"}
    result = rotate_key("MY_DB_URL", "new", env)
    assert result["MY_DB_URL"] == "new"
    assert result["MY_DB_URL_v1"] == "old"


def test_rotate_key_keep_one_always_prunes_all_but_latest():
    env = {"K": "c", "K_v1": "a", "K_v2": "b"}
    result = rotate_key("K", "d", env, keep=1)
    archived = [k for k in result if k.startswith("K_v")]
    assert len(archived) == 1


def test_current_version_ignores_unrelated_keys():
    env = {"OTHER_v1": "x", "DB_URL_v2": "y"}
    assert current_version("OTHER", env) == 1
    assert current_version("DB_URL", env) == 2
    assert current_version("MISSING", env) == 0


def test_list_versions_ignores_live_key():
    """The live key (no version suffix) must not appear in list_versions."""
    env = {"DB_URL": "live", "DB_URL_v1": "old"}
    result = list_versions("DB_URL", env)
    assert all(isinstance(ver, int) for ver, _ in result)
    assert all(val != "live" for _, val in result)


def test_rollback_preserves_other_keys():
    env = {"DB_URL": "new", "DB_URL_v1": "old", "OTHER": "untouched"}
    result = rollback("DB_URL", env)
    assert result["OTHER"] == "untouched"


def test_rotate_then_rollback_round_trip():
    env = {"SECRET": "v1"}
    after_rotate = rotate_key("SECRET", "v2", env)
    assert after_rotate["SECRET"] == "v2"
    after_rollback = rollback("SECRET", after_rotate)
    assert after_rollback["SECRET"] == "v1"


def test_multiple_rotations_version_sequence():
    env: dict = {}
    env = rotate_key("TOKEN", "alpha", env)   # no archive (was absent)
    env = rotate_key("TOKEN", "beta", env)    # archives alpha as v1
    env = rotate_key("TOKEN", "gamma", env)   # archives beta as v2
    assert env["TOKEN"] == "gamma"
    versions = list_versions("TOKEN", env)
    assert len(versions) == 2
    assert versions[0] == (1, "alpha")
    assert versions[1] == (2, "beta")
