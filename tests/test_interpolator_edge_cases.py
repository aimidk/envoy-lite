"""Edge-case and integration tests for envoy_lite.interpolator."""
from __future__ import annotations

import pytest

from envoy_lite.interpolator import (
    InterpolationError,
    interpolate,
    interpolate_dict,
)


class TestEdgeCases:
    def test_adjacent_tokens(self):
        env = {"A": "foo", "B": "bar"}
        assert interpolate("${A}${B}", env) == "foobar"

    def test_token_value_contains_dollar(self):
        """Resolved values are NOT re-interpolated (no double expansion)."""
        env = {"A": "${B}", "B": "oops"}
        # Only the literal text is substituted; the value of A is used verbatim.
        result = interpolate("${A}", env)
        assert result == "${B}"

    def test_underscore_only_name(self):
        assert interpolate("${_}", {"_": "ok"}) == "ok"

    def test_long_default_word(self):
        word = "a" * 80
        assert interpolate(f"${{X:-{word}}}", {}) == word

    def test_empty_template(self):
        assert interpolate("", {}) == ""

    def test_no_dollar_sign_passthrough(self):
        assert interpolate("plain text", {"X": "y"}) == "plain text"

    def test_partial_syntax_not_matched(self):
        """$VAR without braces is not substituted."""
        assert interpolate("$VAR", {"VAR": "nope"}) == "$VAR"


class TestInterpolateDictIntegration:
    def test_empty_mapping(self):
        assert interpolate_dict({}) == {}

    def test_value_referencing_itself_raises(self):
        """Self-reference: VAR is not yet in resolved when it is processed."""
        with pytest.raises(InterpolationError):
            interpolate_dict({"VAR": "${VAR}"})

    def test_base_env_overridden_by_mapping(self):
        """A key in *mapping* shadows the same key from *base_env*."""
        result = interpolate_dict({"A": "new"}, base_env={"A": "old"})
        assert result["A"] == "new"

    def test_later_entry_sees_earlier_resolved_value(self):
        mapping = {
            "BASE": "http://localhost",
            "PORT": "8080",
            "URL": "${BASE}:${PORT}/api",
        }
        result = interpolate_dict(mapping)
        assert result["URL"] == "http://localhost:8080/api"

    def test_alternate_op_integration(self):
        mapping = {"DEBUG": "true", "LOG_LEVEL": "${DEBUG:+verbose}"}
        result = interpolate_dict(mapping)
        assert result["LOG_LEVEL"] == "verbose"
