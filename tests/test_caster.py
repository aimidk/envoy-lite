"""Tests for envoy_lite.caster."""

from __future__ import annotations

import pytest

from envoy_lite.caster import (
    CastError,
    cast_dict,
    cast_value,
    register_caster,
)


# ---------------------------------------------------------------------------
# cast_value — basic types
# ---------------------------------------------------------------------------

class TestCastValue:
    def test_str_passthrough(self):
        assert cast_value("K", "hello", "str") == "hello"

    def test_int_valid(self):
        assert cast_value("PORT", "8080", "int") == 8080

    def test_int_invalid_raises(self):
        with pytest.raises(CastError) as exc_info:
            cast_value("PORT", "abc", "int")
        assert "PORT" in str(exc_info.value)
        assert "int" in str(exc_info.value)

    def test_float_valid(self):
        result = cast_value("RATIO", "3.14", "float")
        assert abs(result - 3.14) < 1e-9

    def test_float_invalid_raises(self):
        with pytest.raises(CastError):
            cast_value("RATIO", "nope", "float")

    @pytest.mark.parametrize("raw", ["1", "true", "True", "yes", "YES", "on", "ON"])
    def test_bool_truthy(self, raw):
        assert cast_value("FLAG", raw, "bool") is True

    @pytest.mark.parametrize("raw", ["0", "false", "False", "no", "NO", "off", "OFF"])
    def test_bool_falsy(self, raw):
        assert cast_value("FLAG", raw, "bool") is False

    def test_bool_invalid_raises(self):
        with pytest.raises(CastError):
            cast_value("FLAG", "maybe", "bool")

    def test_json_object(self):
        result = cast_value("CFG", '{"a": 1}', "json")
        assert result == {"a": 1}

    def test_json_list(self):
        assert cast_value("ITEMS", "[1,2,3]", "json") == [1, 2, 3]

    def test_json_invalid_raises(self):
        with pytest.raises(CastError):
            cast_value("CFG", "{bad json}", "json")

    def test_unknown_type_raises(self):
        with pytest.raises(CastError) as exc_info:
            cast_value("X", "v", "uuid")
        assert "uuid" in str(exc_info.value)


# ---------------------------------------------------------------------------
# register_caster
# ---------------------------------------------------------------------------

def test_register_custom_caster():
    register_caster("csv", lambda v: v.split(","))
    result = cast_value("TAGS", "a,b,c", "csv")
    assert result == ["a", "b", "c"]


def test_register_caster_overrides_existing():
    register_caster("int", lambda v: int(v) * 2)
    assert cast_value("N", "5", "int") == 10
    # restore
    register_caster("int", int)


# ---------------------------------------------------------------------------
# cast_dict
# ---------------------------------------------------------------------------

class TestCastDict:
    def test_casts_matching_keys(self):
        env = {"PORT": "9000", "NAME": "app"}
        result = cast_dict(env, {"PORT": "int"})
        assert result["PORT"] == 9000
        assert result["NAME"] == "app"

    def test_missing_key_skipped_by_default(self):
        result = cast_dict({"A": "1"}, {"B": "int"})
        assert "B" not in result

    def test_missing_key_strict_raises(self):
        with pytest.raises(CastError):
            cast_dict({"A": "1"}, {"B": "int"}, strict=True)

    def test_original_dict_not_mutated(self):
        env = {"PORT": "80"}
        cast_dict(env, {"PORT": "int"})
        assert env["PORT"] == "80"

    def test_multiple_types(self):
        env = {"PORT": "443", "DEBUG": "true", "RATE": "0.5"}
        result = cast_dict(env, {"PORT": "int", "DEBUG": "bool", "RATE": "float"})
        assert result == {"PORT": 443, "DEBUG": True, "RATE": 0.5}
