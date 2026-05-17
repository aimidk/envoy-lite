"""Tests for envoy_lite.aliaser and envoy_lite.cli_alias."""
from __future__ import annotations

import pytest

from envoy_lite.aliaser import AliasError, AliasRegistry, expand_aliases


# ---------------------------------------------------------------------------
# AliasRegistry
# ---------------------------------------------------------------------------

def test_register_and_resolve():
    reg = AliasRegistry()
    reg.register("DATABASE_HOST", "DB_HOST")
    assert reg.resolve("DB_HOST") == "DATABASE_HOST"


def test_resolve_unknown_returns_key():
    reg = AliasRegistry()
    assert reg.resolve("UNKNOWN") == "UNKNOWN"


def test_register_multiple_aliases():
    reg = AliasRegistry()
    reg.register("DATABASE_HOST", "DB_HOST", "DBHOST")
    assert reg.resolve("DB_HOST") == "DATABASE_HOST"
    assert reg.resolve("DBHOST") == "DATABASE_HOST"


def test_aliases_for_returns_list():
    reg = AliasRegistry()
    reg.register("DATABASE_HOST", "DB_HOST", "DBHOST")
    result = sorted(reg.aliases_for("DATABASE_HOST"))
    assert result == ["DB_HOST", "DBHOST"]


def test_aliases_for_empty_when_none():
    reg = AliasRegistry()
    assert reg.aliases_for("MISSING") == []


def test_register_empty_canonical_raises():
    reg = AliasRegistry()
    with pytest.raises(AliasError, match="canonical"):
        reg.register("", "ALIAS")


def test_register_empty_alias_raises():
    reg = AliasRegistry()
    with pytest.raises(AliasError, match="alias"):
        reg.register("CANONICAL", "")


def test_register_alias_same_as_canonical_raises():
    reg = AliasRegistry()
    with pytest.raises(AliasError, match="differ"):
        reg.register("FOO", "FOO")


def test_all_aliases_returns_copy():
    reg = AliasRegistry()
    reg.register("C", "A", "B")
    mapping = reg.all_aliases()
    assert mapping == {"A": "C", "B": "C"}
    # mutating the returned dict must not affect the registry
    mapping["X"] = "Y"
    assert "X" not in reg.all_aliases()


# ---------------------------------------------------------------------------
# expand_aliases
# ---------------------------------------------------------------------------

def test_expand_replaces_alias_key():
    reg = AliasRegistry()
    reg.register("DATABASE_HOST", "DB_HOST")
    result = expand_aliases({"DB_HOST": "localhost"}, reg)
    assert result == {"DATABASE_HOST": "localhost"}
    assert "DB_HOST" not in result


def test_expand_preserves_non_alias_keys():
    reg = AliasRegistry()
    reg.register("DATABASE_HOST", "DB_HOST")
    result = expand_aliases({"DB_HOST": "localhost", "PORT": "5432"}, reg)
    assert result["PORT"] == "5432"


def test_expand_canonical_already_present_no_overwrite():
    """By default the existing canonical value is kept."""
    reg = AliasRegistry()
    reg.register("HOST", "DB_HOST")
    result = expand_aliases({"DB_HOST": "alias-val", "HOST": "canon-val"}, reg)
    assert result["HOST"] == "canon-val"
    assert "DB_HOST" not in result


def test_expand_canonical_already_present_overwrite():
    reg = AliasRegistry()
    reg.register("HOST", "DB_HOST")
    result = expand_aliases(
        {"DB_HOST": "alias-val", "HOST": "canon-val"}, reg, overwrite=True
    )
    assert result["HOST"] == "alias-val"


def test_expand_alias_not_in_env_is_ignored():
    reg = AliasRegistry()
    reg.register("DATABASE_HOST", "DB_HOST")
    result = expand_aliases({"PORT": "5432"}, reg)
    assert result == {"PORT": "5432"}


def test_expand_empty_env_returns_empty():
    reg = AliasRegistry()
    reg.register("HOST", "DB_HOST")
    assert expand_aliases({}, reg) == {}


def test_expand_does_not_mutate_original():
    reg = AliasRegistry()
    reg.register("HOST", "DB_HOST")
    original = {"DB_HOST": "localhost"}
    expand_aliases(original, reg)
    assert "DB_HOST" in original
