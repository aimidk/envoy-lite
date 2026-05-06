"""Tests for envoy_lite.redactor and envoy_lite.cli_redact."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envoy_lite.redactor import Redactor, redact, MASK


# ---------------------------------------------------------------------------
# Redactor unit tests
# ---------------------------------------------------------------------------

class TestRedactor:
    def test_default_password_is_sensitive(self):
        r = Redactor()
        assert r.is_sensitive("DB_PASSWORD") is True

    def test_default_token_is_sensitive(self):
        r = Redactor()
        assert r.is_sensitive("GITHUB_TOKEN") is True

    def test_default_api_key_is_sensitive(self):
        r = Redactor()
        assert r.is_sensitive("STRIPE_API_KEY") is True

    def test_non_sensitive_key(self):
        r = Redactor()
        assert r.is_sensitive("APP_NAME") is False

    def test_redact_value_masks_sensitive(self):
        r = Redactor()
        assert r.redact_value("DB_PASSWORD", "s3cr3t") == MASK

    def test_redact_value_passes_non_sensitive(self):
        r = Redactor()
        assert r.redact_value("APP_PORT", "8080") == "8080"

    def test_custom_mask(self):
        r = Redactor(mask="<hidden>")
        assert r.redact_value("SECRET", "x") == "<hidden>"

    def test_redact_dict_preserves_non_sensitive(self):
        r = Redactor()
        result = r.redact_dict({"APP_NAME": "myapp", "DB_PASSWORD": "pw"})
        assert result["APP_NAME"] == "myapp"
        assert result["DB_PASSWORD"] == MASK

    def test_extra_pattern_registered(self):
        r = Redactor(extra_patterns=[r"(?i)internal"])
        assert r.is_sensitive("INTERNAL_URL") is True
        assert r.is_sensitive("PUBLIC_URL") is False

    def test_add_pattern_runtime(self):
        r = Redactor()
        r.add_pattern(r"(?i)webhook")
        assert r.is_sensitive("WEBHOOK_SECRET") is True

    def test_convenience_redact_function(self):
        result = redact({"TOKEN": "abc", "HOST": "localhost"})
        assert result["TOKEN"] == MASK
        assert result["HOST"] == "localhost"


# ---------------------------------------------------------------------------
# CLI redact tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        textwrap.dedent("""\
        APP_NAME=myapp
        DB_PASSWORD=supersecret
        GITHUB_TOKEN=ghp_abc123
        PORT=3000
        """)
    )
    return p


def test_cli_redact_masks_secrets(env_file, capsys):
    from envoy_lite.cli_redact import cmd_redact, build_redact_parser
    parser = build_redact_parser()
    args = parser.parse_args(["--file", str(env_file)])
    rc = cmd_redact(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "supersecret" not in out
    assert "ghp_abc123" not in out
    assert "APP_NAME=myapp" in out
    assert "PORT=3000" in out


def test_cli_redact_show_keys_only(env_file, capsys):
    from envoy_lite.cli_redact import cmd_redact, build_redact_parser
    parser = build_redact_parser()
    args = parser.parse_args(["--file", str(env_file), "--show-keys-only"])
    rc = cmd_redact(args)
    out = capsys.readouterr().out
    assert rc == 0
    lines = out.strip().splitlines()
    assert "DB_PASSWORD" in lines
    assert "GITHUB_TOKEN" in lines
    assert "APP_NAME" not in lines


def test_cli_redact_missing_file(tmp_path, capsys):
    from envoy_lite.cli_redact import cmd_redact, build_redact_parser
    parser = build_redact_parser()
    args = parser.parse_args(["--file", str(tmp_path / "missing.env")])
    rc = cmd_redact(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().err
