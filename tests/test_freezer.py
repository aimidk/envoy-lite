"""Tests for envoy_lite.freezer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy_lite.freezer import FreezeError, apply_thaw, freeze, thaw


# ---------------------------------------------------------------------------
# freeze()
# ---------------------------------------------------------------------------

def test_freeze_creates_file(tmp_path):
    dest = tmp_path / "snap.json"
    result = freeze({"A": "1", "B": "2"}, dest)
    assert result == dest
    assert dest.exists()


def test_freeze_content_is_sorted_json(tmp_path):
    dest = tmp_path / "snap.json"
    freeze({"Z": "last", "A": "first"}, dest)
    data = json.loads(dest.read_text())
    assert list(data.keys()) == ["A", "Z"]
    assert data["A"] == "first"


def test_freeze_raises_if_exists_without_overwrite(tmp_path):
    dest = tmp_path / "snap.json"
    dest.write_text("{}")
    with pytest.raises(FreezeError, match="already exists"):
        freeze({"X": "1"}, dest)


def test_freeze_overwrite_replaces_file(tmp_path):
    dest = tmp_path / "snap.json"
    freeze({"OLD": "val"}, dest)
    freeze({"NEW": "val"}, dest, overwrite=True)
    data = json.loads(dest.read_text())
    assert "NEW" in data
    assert "OLD" not in data


def test_freeze_creates_parent_dirs(tmp_path):
    dest = tmp_path / "nested" / "deep" / "snap.json"
    freeze({"K": "v"}, dest)
    assert dest.exists()


# ---------------------------------------------------------------------------
# thaw()
# ---------------------------------------------------------------------------

def test_thaw_roundtrip(tmp_path):
    env = {"FOO": "bar", "NUM": "42"}
    dest = tmp_path / "snap.json"
    freeze(env, dest)
    loaded = thaw(dest)
    assert loaded == env


def test_thaw_missing_file_raises(tmp_path):
    with pytest.raises(FreezeError, match="not found"):
        thaw(tmp_path / "ghost.json")


def test_thaw_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    with pytest.raises(FreezeError, match="Invalid JSON"):
        thaw(bad)


def test_thaw_non_object_raises(tmp_path):
    arr = tmp_path / "arr.json"
    arr.write_text("[1, 2, 3]")
    with pytest.raises(FreezeError, match="JSON object"):
        thaw(arr)


# ---------------------------------------------------------------------------
# apply_thaw()
# ---------------------------------------------------------------------------

def test_apply_thaw_override_true(tmp_path):
    dest = tmp_path / "snap.json"
    freeze({"SHARED": "frozen", "ONLY_FROZEN": "yes"}, dest)
    result = apply_thaw({"SHARED": "live", "ONLY_LIVE": "yes"}, dest, override=True)
    assert result["SHARED"] == "frozen"
    assert result["ONLY_LIVE"] == "yes"
    assert result["ONLY_FROZEN"] == "yes"


def test_apply_thaw_override_false(tmp_path):
    dest = tmp_path / "snap.json"
    freeze({"SHARED": "frozen"}, dest)
    result = apply_thaw({"SHARED": "live"}, dest, override=False)
    assert result["SHARED"] == "live"


def test_apply_thaw_does_not_mutate_original(tmp_path):
    dest = tmp_path / "snap.json"
    freeze({"NEW": "val"}, dest)
    original = {"OLD": "val"}
    apply_thaw(original, dest)
    assert "NEW" not in original
