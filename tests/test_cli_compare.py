"""Tests for envoy_lite.cli_compare."""
from __future__ import annotations

import argparse
import os

import pytest

from envoy_lite.cli_compare import build_compare_parser, cmd_compare


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path, content):
    path.write_text(content)
    return str(path)


def _make_args(left, right, hide_unchanged=False, only=None):
    ns = argparse.Namespace(
        left=left,
        right=right,
        hide_unchanged=hide_unchanged,
        only=only,
    )
    return ns


class TestBuildCompareParser:
    def test_returns_parser(self):
        p = build_compare_parser()
        assert isinstance(p, argparse.ArgumentParser)

    def test_defaults(self):
        p = build_compare_parser()
        args = p.parse_args(["a.env", "b.env"])
        assert args.left == "a.env"
        assert args.right == "b.env"
        assert args.hide_unchanged is False
        assert args.only is None

    def test_hide_unchanged_flag(self):
        p = build_compare_parser()
        args = p.parse_args(["a.env", "b.env", "--hide-unchanged"])
        assert args.hide_unchanged is True

    def test_only_choices(self):
        p = build_compare_parser()
        for choice in ("added", "removed", "changed"):
            args = p.parse_args(["a.env", "b.env", "--only", choice])
            assert args.only == choice


def test_cmd_compare_no_diff_returns_0(env_dir, capsys):
    f = _write(env_dir / "a.env", "A=1\nB=2\n")
    args = _make_args(f, f)
    rc = cmd_compare(args)
    assert rc == 0


def test_cmd_compare_with_diff_returns_1(env_dir, capsys):
    left = _write(env_dir / "left.env", "A=1\n")
    right = _write(env_dir / "right.env", "A=2\n")
    args = _make_args(left, right)
    rc = cmd_compare(args)
    assert rc == 1


def test_cmd_compare_prints_added(env_dir, capsys):
    left = _write(env_dir / "left.env", "A=1\n")
    right = _write(env_dir / "right.env", "A=1\nB=2\n")
    args = _make_args(left, right)
    cmd_compare(args)
    out = capsys.readouterr().out
    assert "+ B" in out


def test_cmd_compare_prints_removed(env_dir, capsys):
    left = _write(env_dir / "left.env", "A=1\nB=2\n")
    right = _write(env_dir / "right.env", "A=1\n")
    args = _make_args(left, right)
    cmd_compare(args)
    out = capsys.readouterr().out
    assert "- B" in out


def test_cmd_compare_only_filter(env_dir, capsys):
    left = _write(env_dir / "left.env", "A=1\nB=old\n")
    right = _write(env_dir / "right.env", "A=1\nB=new\nC=3\n")
    args = _make_args(left, right, only="changed")
    cmd_compare(args)
    out = capsys.readouterr().out
    assert "B" in out
    assert "C" not in out
    assert "A" not in out


def test_cmd_compare_prints_summary(env_dir, capsys):
    left = _write(env_dir / "left.env", "A=1\n")
    right = _write(env_dir / "right.env", "A=2\n")
    args = _make_args(left, right)
    cmd_compare(args)
    out = capsys.readouterr().out
    assert "changed" in out
