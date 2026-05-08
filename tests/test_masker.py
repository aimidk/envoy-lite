"""Tests for envoy_lite.masker and envoy_lite.cli_mask."""

from __future__ import annotations

import argparse
import os
import pytest

from envoy_lite.masker import MaskError, mask_dict, mask_middle, mask_pattern, mask_suffix


# ---------------------------------------------------------------------------
# mask_middle
# ---------------------------------------------------------------------------

def test_mask_middle_basic():
    assert mask_middle("abcdefgh", visible=2) == "ab****gh"


def test_mask_middle_too_short_fully_masked():
    assert mask_middle("ab", visible=2) == "**"


def test_mask_middle_custom_char():
    result = mask_middle("hello world", visible=3, char="-")
    assert result.startswith("hel")
    assert result.endswith("rld")
    assert "-" in result


def test_mask_middle_negative_visible_raises():
    with pytest.raises(MaskError):
        mask_middle("value", visible=-1)


def test_mask_middle_bad_char_raises():
    with pytest.raises(MaskError):
        mask_middle("value", char="**")


# ---------------------------------------------------------------------------
# mask_suffix
# ---------------------------------------------------------------------------

def test_mask_suffix_basic():
    result = mask_suffix("mysecrettoken", visible=4)
    assert result.endswith("oken")
    assert result.startswith("*")


def test_mask_suffix_value_shorter_than_visible():
    assert mask_suffix("abc", visible=4) == "abc"


def test_mask_suffix_negative_visible_raises():
    with pytest.raises(MaskError):
        mask_suffix("value", visible=-1)


# ---------------------------------------------------------------------------
# mask_pattern
# ---------------------------------------------------------------------------

def test_mask_pattern_replaces_match():
    assert mask_pattern("user:secret123", r"secret\d+") == "user:***"


def test_mask_pattern_no_match_unchanged():
    assert mask_pattern("hello", r"\d+") == "hello"


def test_mask_pattern_invalid_regex_raises():
    with pytest.raises(MaskError):
        mask_pattern("value", r"[invalid")


# ---------------------------------------------------------------------------
# mask_dict
# ---------------------------------------------------------------------------

def test_mask_dict_all_keys_by_default():
    env = {"A": "longvalue", "B": "another"}
    masked = mask_dict(env, visible=2)
    assert masked["A"] != "longvalue"
    assert masked["B"] != "another"


def test_mask_dict_specific_keys_only():
    env = {"SECRET": "topsecret", "PLAIN": "visible"}
    masked = mask_dict(env, keys=["SECRET"], visible=3)
    assert masked["PLAIN"] == "visible"
    assert masked["SECRET"] != "topsecret"


def test_mask_dict_middle_strategy():
    env = {"TOKEN": "abcdefghij"}
    masked = mask_dict(env, strategy="middle", visible=2)
    assert masked["TOKEN"].startswith("ab")
    assert masked["TOKEN"].endswith("ij")


def test_mask_dict_unknown_strategy_raises():
    with pytest.raises(MaskError, match="Unknown strategy"):
        mask_dict({"K": "v"}, strategy="rot13")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_KEY=supersecretkey\nHOST=localhost\n")
    return str(p)


def test_cli_mask_output(env_file, capsys):
    from envoy_lite.cli_mask import cmd_mask

    ns = argparse.Namespace(
        file=env_file, keys=None, strategy="suffix", visible=4, char="*"
    )
    rc = cmd_mask(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "API_KEY=" in out
    assert "supersecretkey" not in out


def test_cli_mask_missing_file(tmp_path, capsys):
    from envoy_lite.cli_mask import cmd_mask

    ns = argparse.Namespace(
        file=str(tmp_path / "ghost.env"),
        keys=None, strategy="suffix", visible=4, char="*",
    )
    rc = cmd_mask(ns)
    assert rc == 1
    assert "not found" in capsys.readouterr().err
