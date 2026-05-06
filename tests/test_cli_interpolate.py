"""Tests for envoy_lite.cli_interpolate."""
from __future__ import annotations

import argparse
import os
import textwrap
from pathlib import Path

import pytest

from envoy_lite.cli_interpolate import build_interpolate_parser, cmd_interpolate


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        textwrap.dedent(
            """\
            HOST=localhost
            PORT=5432
            DSN=${HOST}:${PORT}/mydb
            LABEL=${APP_NAME:-envoy}
            """
        )
    )
    return p


def _make_args(file: str, no_os_env: bool = True, strict: bool = False) -> argparse.Namespace:
    return argparse.Namespace(file=file, no_os_env=no_os_env, strict=strict, func=cmd_interpolate)


class TestBuildInterpolateParser:
    def test_returns_parser(self):
        root = argparse.ArgumentParser()
        sub = root.add_subparsers()
        p = build_interpolate_parser(sub)
        assert p is not None

    def test_defaults(self):
        root = argparse.ArgumentParser()
        sub = root.add_subparsers()
        build_interpolate_parser(sub)
        args = root.parse_args(["interpolate"])
        assert args.file == ".env"
        assert args.no_os_env is False
        assert args.strict is False


class TestCmdInterpolate:
    def test_missing_file_returns_1(self, tmp_path: Path):
        args = _make_args(str(tmp_path / "nonexistent.env"))
        assert cmd_interpolate(args) == 1

    def test_outputs_sorted_keys(self, env_file: Path, capsys: pytest.CaptureFixture):
        args = _make_args(str(env_file))
        rc = cmd_interpolate(args)
        assert rc == 0
        out = capsys.readouterr().out
        lines = out.strip().splitlines()
        keys = [line.split("=")[0] for line in lines]
        assert keys == sorted(keys)

    def test_dsn_interpolated(self, env_file: Path, capsys: pytest.CaptureFixture):
        args = _make_args(str(env_file))
        cmd_interpolate(args)
        out = capsys.readouterr().out
        assert "DSN=localhost:5432/mydb" in out

    def test_default_operator_no_os_env(self, env_file: Path, capsys: pytest.CaptureFixture):
        args = _make_args(str(env_file), no_os_env=True)
        cmd_interpolate(args)
        out = capsys.readouterr().out
        assert "LABEL=envoy" in out

    def test_os_env_seeds_default(self, env_file: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("APP_NAME", "myapp")
        args = _make_args(str(env_file), no_os_env=False)
        cmd_interpolate(args)
        out = capsys.readouterr().out
        assert "LABEL=myapp" in out

    def test_strict_mode_missing_var_returns_1(self, tmp_path: Path, capsys: pytest.CaptureFixture):
        p = tmp_path / ".env"
        p.write_text("X=${UNDEFINED_VAR}\n")
        args = _make_args(str(p), no_os_env=True, strict=True)
        rc = cmd_interpolate(args)
        assert rc == 1
        assert "interpolation error" in capsys.readouterr().err

    def test_non_strict_missing_var_warns_returns_0(self, tmp_path: Path, capsys: pytest.CaptureFixture):
        p = tmp_path / ".env"
        p.write_text("X=${UNDEFINED_VAR}\n")
        args = _make_args(str(p), no_os_env=True, strict=False)
        rc = cmd_interpolate(args)
        assert rc == 0
        assert "warning" in capsys.readouterr().err
