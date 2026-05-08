"""Tests for envoy_lite.grouper and envoy_lite.cli_group."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envoy_lite.grouper import (
    GroupError,
    filter_by_prefix,
    filter_by_suffix,
    filter_by_pattern,
    group_by_prefixes,
)


SAMPLE = {
    "APP_HOST": "localhost",
    "APP_PORT": "8080",
    "DB_HOST": "db.local",
    "DB_PORT": "5432",
    "SECRET_KEY": "abc123",
}


# ---------------------------------------------------------------------------
# filter_by_prefix
# ---------------------------------------------------------------------------

def test_filter_by_prefix_basic():
    result = filter_by_prefix(SAMPLE, "APP_")
    assert result == {"APP_HOST": "localhost", "APP_PORT": "8080"}


def test_filter_by_prefix_strip():
    result = filter_by_prefix(SAMPLE, "APP_", strip=True)
    assert result == {"HOST": "localhost", "PORT": "8080"}


def test_filter_by_prefix_no_match():
    assert filter_by_prefix(SAMPLE, "NOPE_") == {}


def test_filter_by_prefix_empty_raises():
    with pytest.raises(GroupError, match="non-empty"):
        filter_by_prefix(SAMPLE, "")


# ---------------------------------------------------------------------------
# filter_by_suffix
# ---------------------------------------------------------------------------

def test_filter_by_suffix_basic():
    result = filter_by_suffix(SAMPLE, "_HOST")
    assert result == {"APP_HOST": "localhost", "DB_HOST": "db.local"}


def test_filter_by_suffix_strip():
    result = filter_by_suffix(SAMPLE, "_HOST", strip=True)
    assert result == {"APP": "localhost", "DB": "db.local"}


def test_filter_by_suffix_empty_raises():
    with pytest.raises(GroupError, match="non-empty"):
        filter_by_suffix(SAMPLE, "")


# ---------------------------------------------------------------------------
# filter_by_pattern
# ---------------------------------------------------------------------------

def test_filter_by_pattern_exact():
    result = filter_by_pattern(SAMPLE, r"APP_.*")
    assert set(result.keys()) == {"APP_HOST", "APP_PORT"}


def test_filter_by_pattern_invalid_raises():
    with pytest.raises(GroupError, match="invalid pattern"):
        filter_by_pattern(SAMPLE, r"[unclosed")


def test_filter_by_pattern_no_match():
    assert filter_by_pattern(SAMPLE, r"NOTHING") == {}


# ---------------------------------------------------------------------------
# group_by_prefixes
# ---------------------------------------------------------------------------

def test_group_by_prefixes_basic():
    groups = group_by_prefixes(SAMPLE, ["APP_", "DB_"])
    assert set(groups["APP_"].keys()) == {"APP_HOST", "APP_PORT"}
    assert set(groups["DB_"].keys()) == {"DB_HOST", "DB_PORT"}
    assert groups["other"] == {"SECRET_KEY": "abc123"}


def test_group_by_prefixes_strip():
    groups = group_by_prefixes(SAMPLE, ["APP_"], strip=True)
    assert "HOST" in groups["APP_"]
    assert "PORT" in groups["APP_"]


def test_group_by_prefixes_no_other_key():
    groups = group_by_prefixes(SAMPLE, ["APP_"], other_key=None)
    assert "other" not in groups
    assert "SECRET_KEY" not in groups.get("APP_", {})


def test_group_by_prefixes_empty_raises():
    with pytest.raises(GroupError, match="at least one prefix"):
        group_by_prefixes(SAMPLE, [])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent("""\
        APP_HOST=localhost
        APP_PORT=8080
        DB_URL=postgres://localhost/mydb
    """))
    return p


def _make_args(env_file: Path, **kwargs):
    import argparse
    defaults = dict(
        env_file=str(env_file),
        prefix=None,
        suffix=None,
        pattern=None,
        strip=False,
        format="dotenv",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_group_prefix_dotenv(env_file: Path, capsys):
    from envoy_lite.cli_group import cmd_group
    args = _make_args(env_file, prefix="APP_")
    rc = cmd_group(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "APP_HOST=localhost" in out
    assert "DB_URL" not in out


def test_cmd_group_prefix_json(env_file: Path, capsys):
    from envoy_lite.cli_group import cmd_group
    args = _make_args(env_file, prefix="APP_", format="json")
    rc = cmd_group(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "APP_HOST" in data


def test_cmd_group_missing_file(tmp_path: Path, capsys):
    from envoy_lite.cli_group import cmd_group
    args = _make_args(tmp_path / "missing.env", prefix="APP_")
    rc = cmd_group(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_cmd_group_bad_pattern(env_file: Path, capsys):
    from envoy_lite.cli_group import cmd_group
    args = _make_args(env_file, pattern=r"[bad")
    rc = cmd_group(args)
    assert rc == 2


def test_build_group_parser_returns_parser():
    from envoy_lite.cli_group import build_group_parser
    parser = build_group_parser()
    assert parser is not None
