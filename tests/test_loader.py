"""Tests for envoy_lite.loader module."""

import os
import textwrap
from pathlib import Path

import pytest

from envoy_lite.loader import load_env_file, _parse_line


# ---------------------------------------------------------------------------
# _parse_line unit tests
# ---------------------------------------------------------------------------


def test_parse_simple_pair():
    assert _parse_line("FOO=bar") == ("FOO", "bar")


def test_parse_quoted_double():
    assert _parse_line('DB_URL="postgres://localhost/dev"') == (
        "DB_URL",
        "postgres://localhost/dev",
    )


def test_parse_quoted_single():
    assert _parse_line("SECRET='my secret'") == ("SECRET", "my secret")


def test_parse_export_prefix():
    assert _parse_line("export API_KEY=abc123") == ("API_KEY", "abc123")


def test_parse_comment_line():
    assert _parse_line("# this is a comment") is None


def test_parse_empty_line():
    assert _parse_line("") is None
    assert _parse_line("   ") is None


def test_parse_inline_comment():
    assert _parse_line("PORT=8080 # default port") == ("PORT", "8080")


def test_parse_no_equals():
    assert _parse_line("JUST_A_KEY") is None


def test_parse_empty_value():
    """A key with no value after '=' should return an empty string."""
    assert _parse_line("EMPTY=") == ("EMPTY", "")


# ---------------------------------------------------------------------------
# load_env_file integration tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def env_file(tmp_path: Path):
    """Write a sample .env file and return its path."""
    content = textwrap.dedent("""\
        APP_NAME=envoy-lite
        PORT=4000
        BASE_URL=http://localhost:${PORT}
        # ignored comment
        export DEBUG=true
    """)
    p = tmp_path / ".env"
    p.write_text(content)
    return p


def test_load_returns_dict(env_file, monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    result = load_env_file(env_file)
    assert result["APP_NAME"] == "envoy-lite"
    assert result["PORT"] == "4000"


def test_load_expands_variables(env_file, monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    result = load_env_file(env_file)
    assert result["BASE_URL"] == "http://localhost:4000"


def test_load_sets_os_environ(env_file, monkeypatch):
    monkeypatch.delenv("APP_NAME", raising=False)
    load_env_file(env_file)
    assert os.environ["APP_NAME"] == "envoy-lite"


def test_load_no_override(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_VAR", "original")
    p = tmp_path / ".env"
    p.write_text("MY_VAR=new_value\n")
    load_env_file(p, override=False)
    assert os.environ["MY_VAR"] == "original"


def test_load_with_override(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_VAR", "original")
    p = tmp_path / ".env"
    p.write_text("MY_VAR=new_value\n")
    load_env_file(p, override=True)
    assert os.environ["MY_VAR"] == "new_value"


def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_env_file("/nonexistent/.env")


def test_load_returns_only_parsed_keys(env_file, monkeypatch):
    """load_env_file should not include comment lines or blank lines as keys."""
    monkeypatch.delenv("PORT", raising=False)
    result = load_env_file(env_file)
    for key in result:
        assert not key.startswith("#"), f"Comment ended up as key: {key!r}"
        assert key.strip(), "Blank line ended up as key"
