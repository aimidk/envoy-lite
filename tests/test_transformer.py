"""Tests for envoy_lite.transformer."""
import pytest

from envoy_lite.transformer import (
    TransformError,
    apply_pipeline,
    apply_transformer,
    get_transformer,
    register_transformer,
    transform_dict,
)


# ---------------------------------------------------------------------------
# Built-in transformers
# ---------------------------------------------------------------------------

def test_upper_transformer():
    assert apply_transformer("upper", "hello") == "HELLO"


def test_lower_transformer():
    assert apply_transformer("lower", "WORLD") == "world"


def test_strip_transformer():
    assert apply_transformer("strip", "  hi  ") == "hi"


def test_strip_quotes_transformer():
    assert apply_transformer("strip_quotes", "'value'") == "value"
    assert apply_transformer("strip_quotes", '"value"') == "value"


def test_base64_roundtrip():
    original = "supersecret"
    encoded = apply_transformer("base64_encode", original)
    assert apply_transformer("base64_decode", encoded) == original


# ---------------------------------------------------------------------------
# get_transformer / register_transformer
# ---------------------------------------------------------------------------

def test_get_unknown_transformer_raises():
    with pytest.raises(TransformError, match="Unknown transformer"):
        get_transformer("nonexistent")


def test_register_custom_transformer():
    register_transformer("reverse", lambda v: v[::-1])
    assert apply_transformer("reverse", "abc") == "cba"


# ---------------------------------------------------------------------------
# apply_pipeline
# ---------------------------------------------------------------------------

def test_pipeline_empty_list_is_identity():
    assert apply_pipeline([], "Hello World") == "Hello World"


def test_pipeline_multiple_steps():
    result = apply_pipeline(["strip", "upper"], "  hello  ")
    assert result == "HELLO"


def test_pipeline_unknown_step_raises():
    with pytest.raises(TransformError):
        apply_pipeline(["upper", "bogus"], "value")


# ---------------------------------------------------------------------------
# transform_dict
# ---------------------------------------------------------------------------

def test_transform_dict_all_keys():
    env = {"A": "hello", "B": "world"}
    result = transform_dict(env, ["upper"])
    assert result == {"A": "HELLO", "B": "WORLD"}


def test_transform_dict_selected_keys():
    env = {"A": "hello", "B": "world"}
    result = transform_dict(env, ["upper"], keys=["A"])
    assert result["A"] == "HELLO"
    assert result["B"] == "world"  # untouched


def test_transform_dict_does_not_mutate_original():
    env = {"A": "hello"}
    transform_dict(env, ["upper"])
    assert env["A"] == "hello"


def test_transform_dict_missing_key_in_keys_list_is_ignored():
    env = {"A": "hello"}
    # "Z" not in env — should not raise
    result = transform_dict(env, ["upper"], keys=["Z"])
    assert result == {"A": "hello"}
