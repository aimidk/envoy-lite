"""Tests for envoy_lite.sanitizer."""

from __future__ import annotations

import pytest

from envoy_lite.sanitizer import (
    SanitizeError,
    sanitize_dict,
    sanitize_key,
    sanitize_value,
)


# ---------------------------------------------------------------------------
# sanitize_key
# ---------------------------------------------------------------------------

class TestSanitizeKey:
    def test_uppercase_by_default(self):
        assert sanitize_key("my_var") == "MY_VAR"

    def test_hyphens_replaced(self):
        assert sanitize_key("MY-VAR") == "MY_VAR"

    def test_spaces_replaced(self):
        assert sanitize_key("MY VAR") == "MY_VAR"

    def test_dots_replaced(self):
        assert sanitize_key("MY.VAR") == "MY_VAR"

    def test_no_uppercase_when_disabled(self):
        result = sanitize_key("myVar", uppercase=False)
        assert result == "myVar"

    def test_custom_replacement_char(self):
        assert sanitize_key("MY-VAR", replacement="X") == "MYXVAR"

    def test_empty_replacement_removes_chars(self):
        assert sanitize_key("MY-VAR", replacement="") == "MYVAR"

    def test_empty_key_raises(self):
        with pytest.raises(SanitizeError, match="empty"):
            sanitize_key("")

    def test_invalid_replacement_raises(self):
        with pytest.raises(SanitizeError, match="replacement"):
            sanitize_key("MY-VAR", replacement="-")

    def test_already_valid_key_unchanged(self):
        assert sanitize_key("MY_VAR_123") == "MY_VAR_123"


# ---------------------------------------------------------------------------
# sanitize_value
# ---------------------------------------------------------------------------

class TestSanitizeValue:
    def test_plain_value_unchanged(self):
        assert sanitize_value("hello world") == "hello world"

    def test_control_chars_stripped_by_default(self):
        assert sanitize_value("hello\x00world") == "helloworld"

    def test_newline_stripped(self):
        assert sanitize_value("line1\nline2") == "line1line2"

    def test_tab_stripped(self):
        assert sanitize_value("col1\tcol2") == "col1col2"

    def test_control_replaced_with_custom_char(self):
        assert sanitize_value("a\x01b", replacement="?") == "a?b"

    def test_strip_control_false_preserves_chars(self):
        raw = "hello\x00world"
        assert sanitize_value(raw, strip_control=False) == raw

    def test_del_char_stripped(self):
        assert sanitize_value("ab\x7fcd") == "abcd"

    def test_empty_string_returns_empty(self):
        assert sanitize_value("") == ""


# ---------------------------------------------------------------------------
# sanitize_dict
# ---------------------------------------------------------------------------

class TestSanitizeDict:
    def test_basic_sanitisation(self):
        result = sanitize_dict({"my-key": "value"})
        assert result == {"MY_KEY": "value"}

    def test_value_control_chars_removed(self):
        result = sanitize_dict({"KEY": "val\x00ue"})
        assert result["KEY"] == "value"

    def test_collision_raises_by_default(self):
        with pytest.raises(SanitizeError, match="collision"):
            sanitize_dict({"my-key": "first", "my_key": "second"})

    def test_collision_last_keeps_final(self):
        result = sanitize_dict(
            {"my-key": "first", "my_key": "second"},
            on_collision="last",
        )
        assert result["MY_KEY"] == "second"

    def test_unknown_collision_strategy_raises(self):
        with pytest.raises(SanitizeError, match="unknown"):
            sanitize_dict({"KEY": "v"}, on_collision="ignore")

    def test_empty_dict_returns_empty(self):
        assert sanitize_dict({}) == {}

    def test_multiple_keys_all_sanitised(self):
        result = sanitize_dict({"a-b": "1", "c.d": "2"})
        assert result == {"A_B": "1", "C_D": "2"}
