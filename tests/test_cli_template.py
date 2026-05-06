"""Tests for envoy_lite.cli_template."""

from __future__ import annotations

import pytest

from envoy_lite.cli_template import build_template_parser, cmd_template


@pytest.fixture()
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP=envoy\nVERSION=1.0\n", encoding="utf-8")
    return f


@pytest.fixture()
def tmpl_file(tmp_path):
    t = tmp_path / "config.tmpl"
    t.write_text("app={{ APP }} version={{ VERSION }}\n", encoding="utf-8")
    return t


def _make_args(template, env_file=".env", output=None):
    ns = build_template_parser().parse_args([])
    ns.template = str(template)
    ns.env_file = str(env_file)
    ns.output = str(output) if output else None
    return ns


class TestBuildTemplateParser:
    def test_returns_parser(self):
        import argparse
        assert isinstance(build_template_parser(), argparse.ArgumentParser)

    def test_defaults(self):
        p = build_template_parser()
        args = p.parse_args(["some_template.txt"])
        assert args.env_file == ".env"
        assert args.output is None


def test_renders_to_stdout(env_file, tmpl_file, capsys):
    args = _make_args(tmpl_file, env_file)
    rc = cmd_template(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "envoy" in out
    assert "1.0" in out


def test_renders_to_file(env_file, tmpl_file, tmp_path):
    out_file = tmp_path / "rendered.txt"
    args = _make_args(tmpl_file, env_file, output=out_file)
    rc = cmd_template(args)
    assert rc == 0
    content = out_file.read_text(encoding="utf-8")
    assert "app=envoy" in content


def test_missing_var_returns_error(env_file, tmp_path, capsys):
    tmpl = tmp_path / "bad.tmpl"
    tmpl.write_text("{{ UNDEFINED_VAR }}", encoding="utf-8")
    args = _make_args(tmpl, env_file)
    rc = cmd_template(args)
    assert rc == 1
    assert "UNDEFINED_VAR" in capsys.readouterr().err


def test_default_placeholder_works(env_file, tmp_path, capsys):
    tmpl = tmp_path / "default.tmpl"
    tmpl.write_text("{{ MISSING | fallback }}", encoding="utf-8")
    args = _make_args(tmpl, env_file)
    rc = cmd_template(args)
    assert rc == 0
    assert "fallback" in capsys.readouterr().out
