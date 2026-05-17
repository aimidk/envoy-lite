"""Tests for envoy_lite.flattener."""

import pytest

from envoy_lite.flattener import FlattenError, flatten, unflatten


# ---------------------------------------------------------------------------
# flatten()
# ---------------------------------------------------------------------------

class TestFlatten:
    def test_flat_dict_unchanged_keys(self):
        result = flatten({"host": "localhost", "port": "5432"})
        assert result == {"HOST": "localhost", "PORT": "5432"}

    def test_nested_dict_joined_with_separator(self):
        result = flatten({"db": {"host": "localhost", "port": "5432"}})
        assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}

    def test_deeply_nested(self):
        result = flatten({"a": {"b": {"c": "deep"}}})
        assert result == {"A_B_C": "deep"}

    def test_custom_separator(self):
        result = flatten({"db": {"host": "x"}}, separator="__")
        assert result == {"DB__HOST": "x"}

    def test_prefix_prepended(self):
        result = flatten({"host": "x"}, prefix="APP")
        assert result == {"APP_HOST": "x"}

    def test_uppercase_false_preserves_case(self):
        result = flatten({"Host": "x"}, uppercase=False)
        assert result == {"Host": "x"}

    def test_none_value_becomes_empty_string(self):
        result = flatten({"key": None})
        assert result == {"KEY": ""}

    def test_integer_value_stringified(self):
        result = flatten({"port": 5432})
        assert result == {"PORT": "5432"}

    def test_non_dict_raises(self):
        with pytest.raises(FlattenError, match="Expected a dict"):
            flatten(["not", "a", "dict"])  # type: ignore[arg-type]

    def test_empty_separator_raises(self):
        with pytest.raises(FlattenError, match="separator"):
            flatten({"a": "b"}, separator="")

    def test_non_string_key_raises(self):
        with pytest.raises(FlattenError, match="keys must be strings"):
            flatten({1: "value"})  # type: ignore[dict-item]

    def test_empty_dict_returns_empty(self):
        assert flatten({}) == {}

    def test_mixed_flat_and_nested(self):
        result = flatten({"name": "envoy", "db": {"host": "localhost"}})
        assert result == {"NAME": "envoy", "DB_HOST": "localhost"}


# ---------------------------------------------------------------------------
# unflatten()
# ---------------------------------------------------------------------------

class TestUnflatten:
    def test_flat_dict_unchanged(self):
        result = unflatten({"HOST": "localhost", "PORT": "5432"})
        assert result == {"HOST": "localhost", "PORT": "5432"}

    def test_single_level_nesting(self):
        result = unflatten({"DB_HOST": "localhost", "DB_PORT": "5432"})
        assert result == {"DB": {"HOST": "localhost", "PORT": "5432"}}

    def test_custom_separator(self):
        result = unflatten({"DB__HOST": "x"}, separator="__")
        assert result == {"DB": {"HOST": "x"}}

    def test_empty_dict_returns_empty(self):
        assert unflatten({}) == {}

    def test_non_dict_raises(self):
        with pytest.raises(FlattenError, match="Expected a dict"):
            unflatten("not a dict")  # type: ignore[arg-type]

    def test_empty_separator_raises(self):
        with pytest.raises(FlattenError, match="separator"):
            unflatten({"A": "b"}, separator="")

    def test_roundtrip(self):
        original = {"db": {"host": "localhost", "port": "5432"}, "name": "app"}
        flat = flatten(original)
        restored = unflatten(flat)
        assert restored == {k.upper(): v for k, v in {
            "DB": {"HOST": "localhost", "PORT": "5432"},
            "NAME": "app",
        }.items()}

    def test_key_conflict_leaf_and_branch_raises(self):
        # "A" appears both as a direct key and as the prefix of "A_B"
        with pytest.raises(FlattenError, match="conflict"):
            unflatten({"A": "leaf", "A_B": "branch"})
