"""Tests for envoy_lite.differ and envoy_lite.cli_diff."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from envoy_lite.differ import DiffResult, diff_dicts, diff_files
from envoy_lite.cli_diff import build_diff_parser, cmd_diff


# ---------------------------------------------------------------------------
# diff_dicts
# ---------------------------------------------------------------------------

def test_diff_dicts_no_changes():
    r = diff_dicts({"A": "1"}, {"A": "1"})
    assert not r.has_changes


def test_diff_dicts_added():
    r = diff_dicts({}, {"NEW": "val"})
    assert r.added == {"NEW": "val"}
    assert not r.removed and not r.changed


def test_diff_dicts_removed():
    r = diff_dicts({"OLD": "x"}, {})
    assert r.removed == {"OLD": "x"}
    assert not r.added and not r.changed


def test_diff_dicts_changed():
    r = diff_dicts({"K": "old"}, {"K": "new"})
    assert r.changed == {"K": ("old", "new")}
    assert not r.added and not r.removed


def test_diff_dicts_mixed():
    base = {"A": "1", "B": "2"}
    other = {"B": "99", "C": "3"}
    r = diff_dicts(base, other)
    assert r.removed == {"A": "1"}
    assert r.added == {"C": "3"}
    assert r.changed == {"B": ("2", "99")}


# ---------------------------------------------------------------------------
# DiffResult.summary
# ---------------------------------------------------------------------------

def test_summary_no_changes():
    r = DiffResult()
    assert r.summary() == "(no changes)"


def test_summary_contains_markers():
    r = DiffResult(added={"X": "1"}, removed={"Y": "2"}, changed={"Z": ("a", "b")})
    s = r.summary()
    assert "+ X=1" in s
    assert "- Y=2" in s
    assert "~ Z" in s


# ---------------------------------------------------------------------------
# diff_files
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path: Path):
    return tmp_path


def test_diff_files_detects_change(env_dir: Path):
    base = env_dir / "base.env"
    other = env_dir / "other.env"
    base.write_text("FOO=bar\nBAZ=qux\n")
    other.write_text("FOO=bar\nBAZ=changed\n")
    r = diff_files(str(base), str(other))
    assert r.changed == {"BAZ": ("qux", "changed")}


def test_diff_files_missing_raises(env_dir: Path):
    with pytest.raises(FileNotFoundError):
        diff_files(str(env_dir / "nope.env"), str(env_dir / "also_nope.env"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_args(base, other, exit_code=False, override=True):
    parser = build_diff_parser()
    argv = [base, other]
    if exit_code:
        argv.append("--exit-code")
    if not override:
        argv.append("--no-override")
    return parser.parse_args(argv)


def test_cmd_diff_no_changes(env_dir: Path, capsys):
    f = env_dir / "a.env"
    f.write_text("K=V\n")
    args = _make_args(str(f), str(f))
    rc = cmd_diff(args)
    assert rc == 0
    assert "(no changes)" in capsys.readouterr().out


def test_cmd_diff_exit_code_on_change(env_dir: Path):
    a = env_dir / "a.env"
    b = env_dir / "b.env"
    a.write_text("K=1\n")
    b.write_text("K=2\n")
    args = _make_args(str(a), str(b), exit_code=True)
    assert cmd_diff(args) == 1


def test_cmd_diff_missing_file_returns_2(env_dir: Path, capsys):
    args = _make_args(str(env_dir / "x.env"), str(env_dir / "y.env"))
    rc = cmd_diff(args)
    assert rc == 2
    assert "error" in capsys.readouterr().err
