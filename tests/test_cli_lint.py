"""Tests for envoy_lite.cli_lint."""
from __future__ import annotations

import argparse
import pytest

from envoy_lite.cli_lint import build_lint_parser, cmd_lint


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return str(p)


@pytest.fixture()
def bad_env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("NODOT\nfoo=1\nFOO=1\nFOO=2\n")
    return str(p)


def _args(file, strict=False, quiet=False):
    ns = argparse.Namespace(file=file, strict=strict, quiet=quiet)
    return ns


class TestBuildLintParser:
    def test_returns_parser(self):
        parser = build_lint_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_defaults(self):
        parser = build_lint_parser()
        args = parser.parse_args(["some.env"])
        assert args.file == "some.env"
        assert args.strict is False
        assert args.quiet is False

    def test_strict_flag(self):
        parser = build_lint_parser()
        args = parser.parse_args(["--strict", "some.env"])
        assert args.strict is True

    def test_quiet_flag(self):
        parser = build_lint_parser()
        args = parser.parse_args(["--quiet", "some.env"])
        assert args.quiet is True


def test_clean_file_returns_zero(env_file):
    assert cmd_lint(_args(env_file)) == 0


def test_missing_file_returns_two(tmp_path):
    assert cmd_lint(_args(str(tmp_path / "nope.env"))) == 2


def test_errors_return_one(bad_env_file):
    # NODOT line has no '=', which is an error
    assert cmd_lint(_args(bad_env_file)) == 1


def test_warnings_only_return_zero(tmp_path):
    p = tmp_path / ".env"
    p.write_text("foo=bar\n")  # lowercase key -> W001 only
    assert cmd_lint(_args(str(p))) == 0


def test_strict_warnings_return_one(tmp_path):
    p = tmp_path / ".env"
    p.write_text("foo=bar\n")  # lowercase key -> W001
    assert cmd_lint(_args(str(p), strict=True)) == 1


def test_quiet_suppresses_per_issue_output(tmp_path, capsys):
    p = tmp_path / ".env"
    p.write_text("foo=bar\n")
    cmd_lint(_args(str(p), quiet=True))
    captured = capsys.readouterr()
    # Should only have summary, not individual issue lines
    assert "W001" not in captured.out
    assert "error(s)" in captured.out


def test_non_quiet_shows_issues(tmp_path, capsys):
    p = tmp_path / ".env"
    p.write_text("foo=bar\n")
    cmd_lint(_args(str(p), quiet=False))
    captured = capsys.readouterr()
    assert "W001" in captured.out
