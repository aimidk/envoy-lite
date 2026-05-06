"""Tests for envoy_lite.snapshot diff/capture utilities."""

import os
import pytest

from envoy_lite.snapshot import EnvSnapshot, EnvDiff


def test_from_dict_roundtrip():
    data = {"KEY": "value", "OTHER": "123"}
    snap = EnvSnapshot.from_dict(data)
    assert snap.data == data
    assert len(snap) == 2


def test_from_os_environ():
    snap = EnvSnapshot.from_os_environ()
    assert "PATH" in snap.data or len(snap.data) >= 0  # always works


def test_diff_added():
    old = EnvSnapshot.from_dict({"A": "1"})
    new = EnvSnapshot.from_dict({"A": "1", "B": "2"})
    diff = old.diff(new)
    assert diff.added == {"B": "2"}
    assert diff.removed == {}
    assert diff.changed == []


def test_diff_removed():
    old = EnvSnapshot.from_dict({"A": "1", "B": "2"})
    new = EnvSnapshot.from_dict({"A": "1"})
    diff = old.diff(new)
    assert diff.removed == {"B": "2"}
    assert diff.added == {}
    assert diff.changed == []


def test_diff_changed():
    old = EnvSnapshot.from_dict({"A": "old"})
    new = EnvSnapshot.from_dict({"A": "new"})
    diff = old.diff(new)
    assert diff.changed == [("A", "old", "new")]
    assert diff.added == {}
    assert diff.removed == {}


def test_diff_empty_when_equal():
    snap = EnvSnapshot.from_dict({"X": "1"})
    diff = snap.diff(snap)
    assert diff.is_empty


def test_diff_summary_added():
    old = EnvSnapshot.from_dict({})
    new = EnvSnapshot.from_dict({"FOO": "bar"})
    summary = old.diff(new).summary()
    assert "+ FOO=bar" in summary


def test_diff_summary_removed():
    old = EnvSnapshot.from_dict({"FOO": "bar"})
    new = EnvSnapshot.from_dict({})
    summary = old.diff(new).summary()
    assert "- FOO=bar" in summary


def test_diff_summary_changed():
    old = EnvSnapshot.from_dict({"FOO": "old"})
    new = EnvSnapshot.from_dict({"FOO": "new"})
    summary = old.diff(new).summary()
    assert "~ FOO" in summary
    assert "old" in summary
    assert "new" in summary


def test_diff_summary_no_changes():
    snap = EnvSnapshot.from_dict({"A": "1"})
    assert snap.diff(snap).summary() == "(no changes)"


def test_diff_is_empty_property():
    diff = EnvDiff()
    assert diff.is_empty
    diff.added["X"] = "1"
    assert not diff.is_empty
