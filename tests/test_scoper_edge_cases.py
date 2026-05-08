"""Edge-case tests for envoy_lite.scoper."""

from __future__ import annotations

import pytest

from envoy_lite.scoper import ScopeError, list_scopes, merge_scopes, scope_filter


def test_scope_with_multiple_separators_in_key():
    """Only the first separator is used as the scope boundary."""
    env = {"APP__SUB__KEY": "deep"}
    result = scope_filter(env, "APP")
    # stripped key should still contain the second separator
    assert "SUB__KEY" in result
    assert result["SUB__KEY"] == "deep"


def test_scope_filter_value_preserved_exactly():
    env = {"NS__VAR": "hello world"}
    result = scope_filter(env, "NS")
    assert result["VAR"] == "hello world"


def test_scope_filter_empty_value():
    env = {"NS__EMPTY": ""}
    result = scope_filter(env, "NS")
    assert result["EMPTY"] == ""


def test_list_scopes_deduplicates():
    env = {"APP__A": "1", "APP__B": "2", "APP__C": "3"}
    scopes = list_scopes(env)
    assert scopes.count("APP") == 1


def test_merge_scopes_no_strip():
    env = {"A__X": "1", "B__X": "2"}
    result = merge_scopes(env, ["A", "B"], strip_prefix=False)
    # Both full keys should be present
    assert "A__X" in result
    assert "B__X" in result


def test_scope_filter_numeric_value():
    env = {"SVC__TIMEOUT": "30"}
    result = scope_filter(env, "SVC")
    assert result["TIMEOUT"] == "30"


def test_merge_empty_scopes_with_real_env():
    env = {"APP__KEY": "val"}
    # merging with a non-existent scope should just return empty contribution
    result = merge_scopes(env, ["APP", "MISSING"])
    assert result == {"KEY": "val"}


def test_list_scopes_separator_not_present():
    env = {"NOSCOPE": "value"}
    assert list_scopes(env) == []
