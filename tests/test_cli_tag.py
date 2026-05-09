"""Tests for envoy_lite.cli_tag."""
import json
import pytest
from unittest.mock import patch

from envoy_lite.cli_tag import build_tag_parser, cmd_tag


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nAPI_KEY=secret123\nPORT=5432\n")
    return str(p)


def _make_args(parser, argv):
    return parser.parse_args(argv)


class TestBuildTagParser:
    def test_returns_parser(self):
        p = build_tag_parser()
        assert p is not None

    def test_filter_subcommand_exists(self):
        p = build_tag_parser()
        args = p.parse_args(["filter", "--file", ".env", "--tag", "foo"])
        assert args.tag_cmd == "filter"

    def test_list_subcommand_exists(self):
        p = build_tag_parser()
        args = p.parse_args(["list"])
        assert args.tag_cmd == "list"

    def test_filter_defaults(self):
        p = build_tag_parser()
        args = p.parse_args(["filter", "--tag", "x"])
        assert args.file == ".env"
        assert args.match_all is False
        assert args.as_json is False


def test_cmd_tag_filter_plain(env_file, capsys):
    p = build_tag_parser()
    args = p.parse_args(
        ["filter", "--file", env_file,
         "--spec", "DB_HOST:database",
         "--spec", "PORT:database",
         "--tag", "database"]
    )
    rc = cmd_tag(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DB_HOST=localhost" in out
    assert "PORT=5432" in out
    assert "API_KEY" not in out


def test_cmd_tag_filter_json(env_file, capsys):
    p = build_tag_parser()
    args = p.parse_args(
        ["filter", "--file", env_file,
         "--spec", "API_KEY:secret",
         "--tag", "secret",
         "--json"]
    )
    cmd_tag(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data == {"API_KEY": "secret123"}


def test_cmd_tag_filter_no_tags_exits(env_file):
    p = build_tag_parser()
    args = p.parse_args(["filter", "--file", env_file, "--spec", "X:foo"])
    # tags list is empty — should exit
    with pytest.raises(SystemExit):
        cmd_tag(args)


def test_cmd_tag_list_plain(capsys):
    p = build_tag_parser()
    args = p.parse_args(["list", "--spec", "DB_HOST:database,required"])
    rc = cmd_tag(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "database" in out


def test_cmd_tag_list_json(capsys):
    p = build_tag_parser()
    args = p.parse_args(["list", "--spec", "KEY:alpha,beta", "--json"])
    cmd_tag(args)
    data = json.loads(capsys.readouterr().out)
    assert data == {"KEY": ["alpha", "beta"]}


def test_invalid_spec_exits(env_file):
    p = build_tag_parser()
    args = p.parse_args(["filter", "--file", env_file, "--spec", "NOCONN", "--tag", "x"])
    with pytest.raises(SystemExit):
        cmd_tag(args)
