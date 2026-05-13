"""Tests for envoy_lite.comparator."""
from __future__ import annotations

import pytest

from envoy_lite.comparator import (
    CompareEntry,
    CompareReport,
    compare_dicts,
)


def test_compare_identical_dicts_all_unchanged():
    env = {"A": "1", "B": "2"}
    report = compare_dicts(env, env)
    assert all(e.status == "unchanged" for e in report.entries)
    assert len(report.unchanged) == 2


def test_compare_added_key():
    left = {"A": "1"}
    right = {"A": "1", "B": "2"}
    report = compare_dicts(left, right)
    assert len(report.added) == 1
    assert report.added[0].key == "B"
    assert report.added[0].left is None
    assert report.added[0].right == "2"


def test_compare_removed_key():
    left = {"A": "1", "B": "2"}
    right = {"A": "1"}
    report = compare_dicts(left, right)
    assert len(report.removed) == 1
    assert report.removed[0].key == "B"
    assert report.removed[0].right is None


def test_compare_changed_key():
    left = {"A": "old"}
    right = {"A": "new"}
    report = compare_dicts(left, right)
    assert len(report.changed) == 1
    entry = report.changed[0]
    assert entry.key == "A"
    assert entry.left == "old"
    assert entry.right == "new"


def test_has_differences_false_when_identical():
    env = {"X": "1"}
    report = compare_dicts(env, env)
    assert not report.has_differences()


def test_has_differences_true_when_changed():
    report = compare_dicts({"X": "1"}, {"X": "2"})
    assert report.has_differences()


def test_hide_unchanged_excludes_equal_keys():
    left = {"A": "1", "B": "2"}
    right = {"A": "1", "B": "99"}
    report = compare_dicts(left, right, include_unchanged=False)
    assert all(e.status != "unchanged" for e in report.entries)
    assert len(report.entries) == 1
    assert report.entries[0].key == "B"


def test_summary_format():
    left = {"A": "1", "B": "2", "C": "3"}
    right = {"A": "1", "B": "99", "D": "4"}
    report = compare_dicts(left, right)
    summary = report.summary()
    assert "+1 added" in summary
    assert "-1 removed" in summary
    assert "~1 changed" in summary
    assert "=1 unchanged" in summary


def test_entries_sorted_by_key():
    left = {"Z": "z", "A": "a", "M": "m"}
    right = {"Z": "z", "A": "a", "M": "m"}
    report = compare_dicts(left, right)
    keys = [e.key for e in report.entries]
    assert keys == sorted(keys)


def test_compare_entry_is_different():
    e_changed = CompareEntry("K", "old", "new", "changed")
    e_same = CompareEntry("K", "v", "v", "unchanged")
    assert e_changed.is_different()
    assert not e_same.is_different()


def test_empty_dicts_produce_empty_report():
    report = compare_dicts({}, {})
    assert report.entries == []
    assert not report.has_differences()
