"""Tests for envoy_lite.scoper."""

from __future__ import annotations

import pytest

from envoy_lite.scoper import ScopeError, list_scopes, merge_scopes, scope_filter


ENV = {
    "APP__HOST": "localhost",
    "APP__PORT": "8080",
    "DB__HOST": "db.local",
    "DB__PORT": "5432",
    "PLAIN_KEY": "value",
    "APP__DEBUG": "true",
}


# ---------------------------------------------------------------------------
# scope_filter
# ---------------------------------------------------------------------------

def test_scope_filter_returns_matching_keys():
    result = scope_filter(ENV, "APP")
    assert set(result.keys()) == {"HOST", "PORT", "DEBUG"}


def test_scope_filter_strips_prefix_by_default():
    result = scope_filter(ENV, "DB")
    assert "HOST" in result
    assert "PORT" in result


def test_scope_filter_no_strip_keeps_prefix():
    result = scope_filter(ENV, "APP", strip_prefix=False)
    assert "APP__HOST" in result
    assert "APP__PORT" in result


def test_scope_filter_case_insensitive_scope():
    result = scope_filter(ENV, "app")
    assert set(result.keys()) == {"HOST", "PORT", "DEBUG"}


def test_scope_filter_no_match_returns_empty():
    result = scope_filter(ENV, "CACHE")
    assert result == {}


def test_scope_filter_empty_scope_raises():
    with pytest.raises(ScopeError, match="empty"):
        scope_filter(ENV, "")


def test_scope_filter_empty_separator_raises():
    with pytest.raises(ScopeError, match="separator"):
        scope_filter(ENV, "APP", separator="")


def test_scope_filter_custom_separator():
    env = {"APP.HOST": "h", "APP.PORT": "p", "OTHER": "x"}
    result = scope_filter(env, "APP", separator=".")
    assert result == {"HOST": "h", "PORT": "p"}


def test_scope_filter_plain_keys_excluded():
    result = scope_filter(ENV, "APP")
    assert "PLAIN_KEY" not in result


# ---------------------------------------------------------------------------
# list_scopes
# ---------------------------------------------------------------------------

def test_list_scopes_returns_sorted_unique():
    scopes = list_scopes(ENV)
    assert scopes == ["APP", "DB"]


def test_list_scopes_empty_env():
    assert list_scopes({}) == []


def test_list_scopes_no_scoped_keys():
    assert list_scopes({"FOO": "bar", "BAZ": "qux"}) == []


def test_list_scopes_custom_separator():
    env = {"X.A": "1", "Y.B": "2", "PLAIN": "3"}
    assert list_scopes(env, separator=".") == ["X", "Y"]


# ---------------------------------------------------------------------------
# merge_scopes
# ---------------------------------------------------------------------------

def test_merge_scopes_last_wins():
    env = {"A__KEY": "from_a", "B__KEY": "from_b"}
    result = merge_scopes(env, ["A", "B"], last_wins=True)
    assert result["KEY"] == "from_b"


def test_merge_scopes_first_wins():
    env = {"A__KEY": "from_a", "B__KEY": "from_b"}
    result = merge_scopes(env, ["A", "B"], last_wins=False)
    assert result["KEY"] == "from_a"


def test_merge_scopes_combines_unique_keys():
    result = merge_scopes(ENV, ["APP", "DB"])
    assert "HOST" in result  # DB__HOST overwrites APP__HOST (last_wins=True)
    assert "DEBUG" in result  # only in APP


def test_merge_scopes_empty_list():
    assert merge_scopes(ENV, []) == {}
