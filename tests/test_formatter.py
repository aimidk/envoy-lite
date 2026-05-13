"""Tests for envoy_lite.formatter."""

from __future__ import annotations

import pytest

from envoy_lite.formatter import (
    FormatError,
    _longest_key,
    format_dict,
    format_pair,
)


# ---------------------------------------------------------------------------
# _longest_key
# ---------------------------------------------------------------------------

def test_longest_key_empty():
    assert _longest_key([]) == 0


def test_longest_key_single():
    assert _longest_key(["FOO"]) == 3


def test_longest_key_multiple():
    assert _longest_key(["A", "LONG_KEY", "MED"]) == 8


# ---------------------------------------------------------------------------
# format_pair — plain
# ---------------------------------------------------------------------------

def test_format_pair_plain_default():
    assert format_pair("FOO", "bar") == "FOO=bar"


def test_format_pair_plain_explicit():
    assert format_pair("X", "1", style="plain") == "X=1"


def test_format_pair_plain_ignores_pad():
    assert format_pair("A", "z", style="plain", pad=10) == "A=z"


# ---------------------------------------------------------------------------
# format_pair — aligned
# ---------------------------------------------------------------------------

def test_format_pair_aligned_pads_key():
    result = format_pair("FOO", "bar", style="aligned", pad=6)
    assert result == "FOO   =bar"


def test_format_pair_aligned_exact_width():
    result = format_pair("FOO", "bar", style="aligned", pad=3)
    assert result == "FOO=bar"


# ---------------------------------------------------------------------------
# format_pair — export
# ---------------------------------------------------------------------------

def test_format_pair_export_prefix():
    assert format_pair("FOO", "bar", style="export") == "export FOO=bar"


# ---------------------------------------------------------------------------
# format_pair — invalid style
# ---------------------------------------------------------------------------

def test_format_pair_invalid_style_raises():
    with pytest.raises(FormatError, match="Unknown style"):
        format_pair("K", "v", style="yaml")


# ---------------------------------------------------------------------------
# format_dict
# ---------------------------------------------------------------------------

def test_format_dict_empty_returns_empty_list():
    assert format_dict({}) == []


def test_format_dict_plain_sorted():
    env = {"ZEBRA": "z", "APPLE": "a"}
    lines = format_dict(env, style="plain", sort=True)
    assert lines == ["APPLE=a", "ZEBRA=z"]


def test_format_dict_plain_unsorted_preserves_order():
    env = {"ZEBRA": "z", "APPLE": "a"}
    lines = format_dict(env, style="plain", sort=False)
    assert lines == ["ZEBRA=z", "APPLE=a"]


def test_format_dict_aligned_auto_pad():
    env = {"SHORT": "1", "VERY_LONG_KEY": "2"}
    lines = format_dict(env, style="aligned", sort=True)
    width = len("VERY_LONG_KEY")
    assert lines[0] == f"{'SHORT':<{width}}=1"
    assert lines[1] == f"{'VERY_LONG_KEY':<{width}}=2"


def test_format_dict_aligned_custom_pad():
    env = {"A": "1"}
    lines = format_dict(env, style="aligned", pad=5)
    assert lines == ["A    =1"]


def test_format_dict_export_style():
    env = {"FOO": "bar"}
    lines = format_dict(env, style="export")
    assert lines == ["export FOO=bar"]


def test_format_dict_invalid_style_raises():
    with pytest.raises(FormatError, match="Unknown style"):
        format_dict({"K": "v"}, style="toml")
