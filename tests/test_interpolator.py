"""Tests for envoy_lite.interpolator."""
from __future__ import annotations

import pytest

from envoy_lite.interpolator import (
    InterpolationError,
    interpolate,
    interpolate_dict,
)


# ---------------------------------------------------------------------------
# interpolate — single string
# ---------------------------------------------------------------------------

class TestInterpolate:
    def test_no_tokens_returns_original(self):
        assert interpolate("hello world", {}) == "hello world"

    def test_simple_substitution(self):
        assert interpolate("${GREETING} world", {"GREETING": "hello"}) == "hello world"

    def test_multiple_tokens(self):
        env = {"A": "foo", "B": "bar"}
        assert interpolate("${A}-${B}", env) == "foo-bar"

    def test_missing_required_raises(self):
        with pytest.raises(InterpolationError, match="MISSING"):
            interpolate("${MISSING}", {})

    def test_default_operator_uses_default_when_unset(self):
        assert interpolate("${VAR:-fallback}", {}) == "fallback"

    def test_default_operator_uses_value_when_set(self):
        assert interpolate("${VAR:-fallback}", {"VAR": "real"}) == "real"

    def test_default_operator_uses_default_when_empty(self):
        assert interpolate("${VAR:-fallback}", {"VAR": ""}) == "fallback"

    def test_alternate_operator_uses_word_when_set(self):
        assert interpolate("${VAR:+alt}", {"VAR": "something"}) == "alt"

    def test_alternate_operator_empty_when_unset(self):
        assert interpolate("${VAR:+alt}", {}) == ""

    def test_alternate_operator_empty_when_value_empty(self):
        assert interpolate("${VAR:+alt}", {"VAR": ""}) == ""

    def test_empty_default_word(self):
        assert interpolate("${VAR:-}", {}) == ""

    def test_token_in_middle_of_string(self):
        assert interpolate("pre_${X}_post", {"X": "mid"}) == "pre_mid_post"

    def test_numeric_suffix_in_name(self):
        assert interpolate("${VAR2}", {"VAR2": "ok"}) == "ok"


# ---------------------------------------------------------------------------
# interpolate_dict — full mapping
# ---------------------------------------------------------------------------

class TestInterpolateDict:
    def test_simple_passthrough(self):
        result = interpolate_dict({"A": "1", "B": "2"})
        assert result == {"A": "1", "B": "2"}

    def test_forward_reference_resolution(self):
        # B is defined after A, but A should be available when resolving B.
        result = interpolate_dict({"A": "hello", "B": "${A} world"})
        assert result["B"] == "hello world"

    def test_base_env_seeds_resolution(self):
        result = interpolate_dict({"MSG": "${GREET} there"}, base_env={"GREET": "hi"})
        assert result["MSG"] == "hi there"

    def test_base_env_not_in_result(self):
        result = interpolate_dict({"X": "1"}, base_env={"Y": "2"})
        assert "Y" not in result

    def test_missing_variable_raises(self):
        with pytest.raises(InterpolationError):
            interpolate_dict({"A": "${NOPE}"})

    def test_default_in_dict(self):
        result = interpolate_dict({"A": "${MISSING:-default_val}"})
        assert result["A"] == "default_val"

    def test_chained_definitions(self):
        mapping = {"HOST": "localhost", "PORT": "5432", "DSN": "${HOST}:${PORT}/db"}
        result = interpolate_dict(mapping)
        assert result["DSN"] == "localhost:5432/db"
