"""Tests for envoy_lite.templater."""

from __future__ import annotations

import pytest

from envoy_lite.templater import TemplateRenderError, render_file, render_string


ENV = {"NAME": "Alice", "GREETING": "Hello", "EMPTY": ""}


def test_no_placeholders_returns_original():
    assert render_string("plain text", ENV) == "plain text"


def test_simple_substitution():
    assert render_string("{{ GREETING }}, {{ NAME }}!", ENV) == "Hello, Alice!"


def test_placeholder_without_spaces():
    assert render_string("{{NAME}}", ENV) == "Alice"


def test_default_used_when_missing():
    result = render_string("{{ MISSING | world }}", ENV)
    assert result == "world"


def test_default_with_extra_spaces():
    result = render_string("{{  MISSING  |  fallback  }}", ENV)
    assert result == "fallback"


def test_env_value_takes_priority_over_default():
    result = render_string("{{ NAME | Bob }}", ENV)
    assert result == "Alice"


def test_missing_required_raises():
    with pytest.raises(TemplateRenderError, match="MISSING"):
        render_string("{{ MISSING }}", ENV)


def test_empty_value_substituted():
    assert render_string("[{{ EMPTY }}]", ENV) == "[]"


def test_multiple_same_placeholder():
    result = render_string("{{ NAME }} and {{ NAME }}", ENV)
    assert result == "Alice and Alice"


def test_render_file(tmp_path):
    tmpl = tmp_path / "tmpl.txt"
    tmpl.write_text("Hello {{ NAME }}!\n", encoding="utf-8")
    assert render_file(tmpl, ENV) == "Hello Alice!\n"


def test_render_file_missing_var_raises(tmp_path):
    tmpl = tmp_path / "tmpl.txt"
    tmpl.write_text("{{ UNDEFINED }}", encoding="utf-8")
    with pytest.raises(TemplateRenderError):
        render_file(tmpl, ENV)
