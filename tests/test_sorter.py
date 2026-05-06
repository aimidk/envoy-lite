"""Tests for envoy_lite.sorter."""

from __future__ import annotations

import pytest

from envoy_lite.sorter import (
    SortError,
    group_by_prefix,
    sort_and_group,
    sort_dict,
)


# ---------------------------------------------------------------------------
# sort_dict
# ---------------------------------------------------------------------------


def test_sort_dict_ascending():
    env = {"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}
    result = sort_dict(env)
    assert list(result.keys()) == ["APPLE", "MANGO", "ZEBRA"]


def test_sort_dict_descending():
    env = {"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}
    result = sort_dict(env, reverse=True)
    assert list(result.keys()) == ["ZEBRA", "MANGO", "APPLE"]


def test_sort_dict_case_insensitive_default():
    env = {"beta": "b", "ALPHA": "a", "gamma": "g"}
    result = sort_dict(env)
    assert list(result.keys()) == ["ALPHA", "beta", "gamma"]


def test_sort_dict_case_sensitive():
    # ASCII order: uppercase < lowercase
    env = {"beta": "b", "ALPHA": "a", "gamma": "g"}
    result = sort_dict(env, case_sensitive=True)
    assert list(result.keys()) == ["ALPHA", "beta", "gamma"]


def test_sort_dict_preserves_values():
    env = {"B": "two", "A": "one"}
    result = sort_dict(env)
    assert result["A"] == "one"
    assert result["B"] == "two"


def test_sort_dict_empty():
    assert sort_dict({}) == {}


# ---------------------------------------------------------------------------
# group_by_prefix
# ---------------------------------------------------------------------------


def test_group_by_prefix_basic():
    env = {"DB_HOST": "localhost", "AWS_KEY": "abc", "PORT": "5432"}
    groups = group_by_prefix(env, ["DB_", "AWS_"])
    assert "DB_" in groups
    assert "AWS_" in groups
    assert groups["DB_"] == {"DB_HOST": "localhost"}
    assert groups["AWS_"] == {"AWS_KEY": "abc"}
    assert groups["__other__"] == {"PORT": "5432"}


def test_group_by_prefix_no_others():
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    groups = group_by_prefix(env, ["DB_"])
    assert "__other__" not in groups


def test_group_by_prefix_first_match_wins():
    env = {"DB_AWS_KEY": "val"}
    groups = group_by_prefix(env, ["DB_", "AWS_"])
    assert "DB_AWS_KEY" in groups["DB_"]
    assert "AWS_" not in groups  # empty, omitted


def test_group_by_prefix_empty_prefixes_raises():
    with pytest.raises(SortError):
        group_by_prefix({"A": "1"}, [])


def test_group_by_prefix_empty_env():
    groups = group_by_prefix({}, ["DB_"])
    assert groups == {}


# ---------------------------------------------------------------------------
# sort_and_group
# ---------------------------------------------------------------------------


def test_sort_and_group_no_prefixes():
    env = {"Z": "z", "A": "a", "M": "m"}
    result = sort_and_group(env)
    assert list(result.keys()) == ["A", "M", "Z"]


def test_sort_and_group_with_prefixes_order():
    env = {
        "DB_NAME": "mydb",
        "DB_HOST": "localhost",
        "AWS_REGION": "us-east-1",
        "PORT": "8080",
    }
    result = sort_and_group(env, prefixes=["DB_", "AWS_"])
    keys = list(result.keys())
    # DB_ group comes first, then AWS_, then __other__
    db_idx = keys.index("DB_HOST")
    aws_idx = keys.index("AWS_REGION")
    port_idx = keys.index("PORT")
    assert db_idx < aws_idx < port_idx


def test_sort_and_group_internal_sort():
    env = {"DB_NAME": "n", "DB_HOST": "h", "DB_PORT": "p"}
    result = sort_and_group(env, prefixes=["DB_"])
    assert list(result.keys()) == ["DB_HOST", "DB_NAME", "DB_PORT"]
