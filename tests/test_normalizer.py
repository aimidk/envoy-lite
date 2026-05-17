"""Tests for envoy_lite.normalizer."""

from __future__ import annotations

import pytest

from envoy_lite.normalizer import (
    NormalizeError,
    normalize_dict,
    normalize_key,
    normalize_value,
)


# ---------------------------------------------------------------------------
# normalize_key
# ---------------------------------------------------------------------------

class TestNormalizeKey:
    def test_lowercase_converted_to_upper(self):
        assert normalize_key("my_var") == "MY_VAR"

    def test_hyphens_replaced_with_underscore(self):
        assert normalize_key("MY-VAR") == "MY_VAR"

    def test_spaces_replaced_with_underscore(self):
        assert normalize_key("MY VAR") == "MY_VAR"

    def test_surrounding_whitespace_stripped(self):
        assert normalize_key("  MY_VAR  ") == "MY_VAR"

    def test_invalid_chars_removed(self):
        assert normalize_key("MY.VAR!") == "MYVAR"

    def test_empty_after_normalization_raises(self):
        with pytest.raises(NormalizeError, match="empty"):
            normalize_key("!!!")  # all invalid chars

    def test_leading_digit_raises(self):
        with pytest.raises(NormalizeError, match="digit"):
            normalize_key("1_VAR")

    def test_no_uppercase_flag(self):
        assert normalize_key("my_var", uppercase=False) == "my_var"

    def test_no_strip_flag(self):
        # Without strip the spaces become underscores rather than being removed
        result = normalize_key(" MY_VAR ", strip=False)
        assert result == "_MY_VAR_"


# ---------------------------------------------------------------------------
# normalize_value
# ---------------------------------------------------------------------------

class TestNormalizeValue:
    def test_strip_default(self):
        assert normalize_value("  hello  ") == "hello"

    def test_no_strip(self):
        assert normalize_value("  hello  ", strip=False) == "  hello  "

    def test_collapse_whitespace(self):
        assert normalize_value("hello   world", collapse_whitespace=True) == "hello world"

    def test_collapse_with_newline(self):
        assert normalize_value("hello\n\tworld", collapse_whitespace=True) == "hello world"

    def test_no_collapse_preserves_internal_spaces(self):
        assert normalize_value("hello   world") == "hello   world"


# ---------------------------------------------------------------------------
# normalize_dict
# ---------------------------------------------------------------------------

class TestNormalizeDict:
    def test_basic_normalization(self):
        result = normalize_dict({"my-var": "  value  "})
        assert result == {"MY_VAR": "value"}

    def test_multiple_keys(self):
        result = normalize_dict({"foo": "1", "bar": "2"})
        assert set(result.keys()) == {"FOO", "BAR"}

    def test_collapse_whitespace_option(self):
        result = normalize_dict({"KEY": "a  b"}, collapse_whitespace=True)
        assert result["KEY"] == "a b"

    def test_skip_errors_drops_bad_key(self):
        result = normalize_dict({"!!!": "val", "GOOD": "ok"}, skip_errors=True)
        assert "GOOD" in result
        assert len(result) == 1

    def test_no_skip_errors_raises(self):
        with pytest.raises(NormalizeError):
            normalize_dict({"!!!": "val"}, skip_errors=False)

    def test_empty_dict_returns_empty(self):
        assert normalize_dict({}) == {}

    def test_no_uppercase_option(self):
        result = normalize_dict({"my_var": "val"}, uppercase=False)
        assert "my_var" in result
