"""Tests for envoy_lite.cli_rotate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envoy_lite.cli_rotate import (
    build_rotate_parser,
    cmd_list,
    cmd_rollback,
    cmd_rotate,
)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_URL=postgres://old\n")
    return p


def _make_args(subcmd: str, key: str, env_path: Path, **kwargs) -> argparse.Namespace:
    base = argparse.Namespace(file=str(env_path), subcmd=subcmd, key=key)
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


class TestBuildRotateParser:
    def test_returns_parser(self):
        p = build_rotate_parser()
        assert isinstance(p, argparse.ArgumentParser)

    def test_rotate_subcommand_exists(self):
        p = build_rotate_parser()
        args = p.parse_args(["rotate", "MY_KEY", "newval"])
        assert args.subcmd == "rotate"
        assert args.key == "MY_KEY"
        assert args.value == "newval"

    def test_rollback_subcommand_exists(self):
        p = build_rotate_parser()
        args = p.parse_args(["rollback", "MY_KEY"])
        assert args.subcmd == "rollback"
        assert args.steps == 1

    def test_list_subcommand_exists(self):
        p = build_rotate_parser()
        args = p.parse_args(["list", "MY_KEY"])
        assert args.subcmd == "list"

    def test_rotate_keep_default(self):
        p = build_rotate_parser()
        args = p.parse_args(["rotate", "K", "v"])
        assert args.keep == 3


class TestCmdRotate:
    def test_rotate_writes_file(self, env_file: Path):
        args = _make_args("rotate", "DB_URL", env_file, value="postgres://new", keep=3, dry_run=False)
        rc = cmd_rotate(args)
        assert rc == 0
        content = env_file.read_text()
        assert "DB_URL=postgres://new" in content
        assert "DB_URL_v1=postgres://old" in content

    def test_rotate_dry_run_no_write(self, env_file: Path, capsys):
        original = env_file.read_text()
        args = _make_args("rotate", "DB_URL", env_file, value="postgres://new", keep=3, dry_run=True)
        rc = cmd_rotate(args)
        assert rc == 0
        assert env_file.read_text() == original
        out = capsys.readouterr().out
        assert "DB_URL=postgres://new" in out

    def test_rotate_missing_file_returns_1(self, tmp_path: Path):
        args = _make_args("rotate", "K", tmp_path / "missing.env", value="v", keep=3, dry_run=False)
        assert cmd_rotate(args) == 1


class TestCmdRollback:
    def test_rollback_restores_value(self, env_file: Path):
        # First rotate to create an archive entry
        env_file.write_text("DB_URL=new\nDB_URL_v1=old\n")
        args = _make_args("rollback", "DB_URL", env_file, steps=1, dry_run=False)
        rc = cmd_rollback(args)
        assert rc == 0
        content = env_file.read_text()
        assert "DB_URL=old" in content

    def test_rollback_no_versions_returns_1(self, env_file: Path, capsys):
        args = _make_args("rollback", "DB_URL", env_file, steps=1, dry_run=False)
        rc = cmd_rollback(args)
        assert rc == 1
        assert "error" in capsys.readouterr().err

    def test_rollback_missing_file_returns_1(self, tmp_path: Path):
        args = _make_args("rollback", "K", tmp_path / "nope.env", steps=1, dry_run=False)
        assert cmd_rollback(args) == 1


class TestCmdList:
    def test_list_no_versions(self, env_file: Path, capsys):
        args = _make_args("list", "DB_URL", env_file)
        rc = cmd_list(args)
        assert rc == 0
        assert "No archived" in capsys.readouterr().out

    def test_list_with_versions(self, env_file: Path, capsys):
        env_file.write_text("DB_URL=current\nDB_URL_v1=prev\n")
        args = _make_args("list", "DB_URL", env_file)
        rc = cmd_list(args)
        assert rc == 0
        assert "v1: prev" in capsys.readouterr().out

    def test_list_missing_file_returns_1(self, tmp_path: Path):
        args = _make_args("list", "K", tmp_path / "nope.env")
        assert cmd_list(args) == 1
