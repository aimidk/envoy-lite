"""Edge-case tests for envoy_lite.transformer."""
import pytest

from envoy_lite.transformer import (
    TransformError,
    apply_pipeline,
    apply_transformer,
    register_transformer,
    transform_dict,
)


def test_empty_string_upper():
    assert apply_transformer("upper", "") == ""


def test_empty_string_strip_quotes():
    assert apply_transformer("strip_quotes", "") == ""


def test_pipeline_preserves_order():
    # strip first, then upper — result should be "HELLO"
    assert apply_pipeline(["strip", "upper"], "  hello  ") == "HELLO"
    # upper first, then strip — same result here
    assert apply_pipeline(["upper", "strip"], "  hello  ") == "HELLO"


def test_pipeline_with_base64_roundtrip():
    value = "my_secret_value"
    encoded = apply_pipeline(["base64_encode"], value)
    decoded = apply_pipeline(["base64_decode"], encoded)
    assert decoded == value


def test_transformer_that_raises_wraps_in_transform_error():
    def bad(_v: str) -> str:
        raise RuntimeError("boom")

    register_transformer("_bad_test", bad)
    with pytest.raises(TransformError, match="boom"):
        apply_pipeline(["_bad_test"], "anything")


def test_transform_dict_empty_env():
    assert transform_dict({}, ["upper"]) == {}


def test_transform_dict_empty_pipeline():
    env = {"A": "hello", "B": "world"}
    assert transform_dict(env, []) == env


def test_register_overwrite_transformer():
    register_transformer("_overwrite_test", lambda v: "first")
    register_transformer("_overwrite_test", lambda v: "second")
    assert apply_transformer("_overwrite_test", "x") == "second"


def test_transform_dict_keys_none_transforms_all():
    env = {"X": "abc", "Y": "def"}
    result = transform_dict(env, ["upper"], keys=None)
    assert result == {"X": "ABC", "Y": "DEF"}
