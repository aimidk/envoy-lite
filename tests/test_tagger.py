"""Tests for envoy_lite.tagger."""
import pytest

from envoy_lite.tagger import TagError, TagRegistry


@pytest.fixture()
def reg() -> TagRegistry:
    return TagRegistry()


def test_tag_and_retrieve(reg):
    reg.tag("DB_HOST", "database", "required")
    assert reg.tags_for("DB_HOST") == ["database", "required"]


def test_tag_empty_key_raises(reg):
    with pytest.raises(TagError, match="non-empty"):
        reg.tag("", "foo")


def test_tag_no_tags_raises(reg):
    with pytest.raises(TagError, match="at least one tag"):
        reg.tag("KEY")


def test_untag_removes_specific_tag(reg):
    reg.tag("KEY", "a", "b")
    reg.untag("KEY", "a")
    assert reg.tags_for("KEY") == ["b"]


def test_untag_all_removes_key(reg):
    reg.tag("KEY", "only")
    reg.untag("KEY", "only")
    assert reg.tags_for("KEY") == []


def test_untag_unknown_tag_is_silent(reg):
    reg.tag("KEY", "a")
    reg.untag("KEY", "nonexistent")
    assert reg.tags_for("KEY") == ["a"]


def test_untag_unknown_key_is_silent(reg):
    reg.untag("MISSING", "foo")  # should not raise


def test_keys_for_tag(reg):
    reg.tag("A", "secret")
    reg.tag("B", "secret", "required")
    reg.tag("C", "required")
    assert reg.keys_for_tag("secret") == ["A", "B"]


def test_filter_dict_any_tag(reg):
    reg.tag("DB_HOST", "database")
    reg.tag("API_KEY", "secret")
    reg.tag("PORT", "network")
    env = {"DB_HOST": "localhost", "API_KEY": "abc", "PORT": "8080", "OTHER": "x"}
    result = reg.filter_dict(env, ["database", "secret"])
    assert set(result.keys()) == {"DB_HOST", "API_KEY"}


def test_filter_dict_match_all(reg):
    reg.tag("A", "x", "y")
    reg.tag("B", "x")
    env = {"A": "1", "B": "2"}
    result = reg.filter_dict(env, ["x", "y"], match_all=True)
    assert result == {"A": "1"}


def test_filter_dict_no_tags_raises(reg):
    with pytest.raises(TagError, match="at least one tag"):
        reg.filter_dict({"K": "v"}, [])


def test_all_tags(reg):
    reg.tag("A", "alpha", "beta")
    reg.tag("B", "gamma")
    assert reg.all_tags() == ["alpha", "beta", "gamma"]


def test_as_dict(reg):
    reg.tag("B", "z", "a")
    reg.tag("A", "m")
    result = reg.as_dict()
    assert list(result.keys()) == ["A", "B"]
    assert result["B"] == ["a", "z"]


def test_filter_unregistered_key_excluded(reg):
    reg.tag("KNOWN", "foo")
    env = {"KNOWN": "1", "UNKNOWN": "2"}
    result = reg.filter_dict(env, ["foo"])
    assert result == {"KNOWN": "1"}
