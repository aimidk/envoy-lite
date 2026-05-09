"""Edge-case tests for envoy_lite.tagger."""
import pytest

from envoy_lite.tagger import TagError, TagRegistry


def test_tag_idempotent():
    reg = TagRegistry()
    reg.tag("KEY", "foo")
    reg.tag("KEY", "foo")  # duplicate — should not duplicate in set
    assert reg.tags_for("KEY") == ["foo"]


def test_filter_empty_env_returns_empty():
    reg = TagRegistry()
    reg.tag("KEY", "foo")
    assert reg.filter_dict({}, ["foo"]) == {}


def test_filter_no_matching_keys_returns_empty():
    reg = TagRegistry()
    reg.tag("OTHER", "bar")
    env = {"OTHER": "1"}
    assert reg.filter_dict(env, ["foo"]) == {}


def test_multiple_tags_accumulate_across_calls():
    reg = TagRegistry()
    reg.tag("KEY", "a")
    reg.tag("KEY", "b")
    assert set(reg.tags_for("KEY")) == {"a", "b"}


def test_keys_for_tag_empty_when_none_match():
    reg = TagRegistry()
    reg.tag("A", "foo")
    assert reg.keys_for_tag("bar") == []


def test_all_tags_empty_registry():
    reg = TagRegistry()
    assert reg.all_tags() == []


def test_as_dict_empty_registry():
    reg = TagRegistry()
    assert reg.as_dict() == {}


def test_filter_match_all_with_single_tag_behaves_like_any():
    reg = TagRegistry()
    reg.tag("A", "x")
    env = {"A": "1"}
    result_any = reg.filter_dict(env, ["x"], match_all=False)
    result_all = reg.filter_dict(env, ["x"], match_all=True)
    assert result_any == result_all == {"A": "1"}


def test_tag_value_with_spaces_in_name():
    """Tag names with spaces are technically allowed (dict key)."""
    reg = TagRegistry()
    reg.tag("KEY", "my tag")
    assert "my tag" in reg.tags_for("KEY")


def test_untag_reduces_all_tags_leaves_empty_list():
    reg = TagRegistry()
    reg.tag("K", "a", "b", "c")
    reg.untag("K", "a", "b", "c")
    assert reg.tags_for("K") == []
    assert "K" not in reg.as_dict()
