"""Tests for envoy_lite.cli_scope."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from envoy_lite.cli_scope import build_scope_parser, cmd_scope


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        textwrap.dedent("""\
            APP__HOST=localhost
            APP__PORT=8080
            DB__HOST=db.local
            DB__PORT=5432
            PLAIN=ignored
        """)
    )
    return p


def _make_args(**kwargs):
    defaults = dict(
        file=None,
        scope=None,
        separator="__",
        no_strip=False,
        merge=None,
        format="dotenv",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestBuildScopeParser:
    def test_returns_parser(self):
        p = build_scope_parser()
        assert p is not None

    def test_defaults(self):
        p = build_scope_parser()
        args = p.parse_args(["myfile.env"])
        assert args.separator == "__"
        assert args.no_strip is False
        assert args.format == "dotenv"

    def test_scope_argument(self):
        p = build_scope_parser()
        args = p.parse_args(["myfile.env", "--scope", "APP"])
        assert args.scope == "APP"


def test_list_scopes_when_no_scope(env_file, capsys):
    args = _make_args(file=str(env_file))
    rc = cmd_scope(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "APP" in out
    assert "DB" in out


def test_scope_filter_dotenv_output(env_file, capsys):
    args = _make_args(file=str(env_file), scope="APP")
    rc = cmd_scope(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "HOST=localhost" in out
    assert "PORT=8080" in out


def test_scope_filter_json_output(env_file, capsys):
    args = _make_args(file=str(env_file), scope="APP", format="json")
    rc = cmd_scope(args)
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert data["HOST"] == "localhost"


def test_missing_file_returns_error(tmp_path, capsys):
    args = _make_args(file=str(tmp_path / "missing.env"), scope="APP")
    rc = cmd_scope(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_merge_flag(env_file, capsys):
    args = _make_args(file=str(env_file), merge=["APP", "DB"])
    rc = cmd_scope(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "HOST" in out


def test_no_strip_keeps_prefix(env_file, capsys):
    args = _make_args(file=str(env_file), scope="APP", no_strip=True)
    rc = cmd_scope(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "APP__HOST" in out
