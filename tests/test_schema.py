"""Tests for envoy_lite.schema."""

import json
import pytest

from envoy_lite.schema import SchemaLoadError, load_schema_dict, load_schema_file
from envoy_lite.validator import EnvValidator


# ---------------------------------------------------------------------------
# load_schema_dict
# ---------------------------------------------------------------------------

def test_load_schema_dict_returns_validator():
    data = {"PORT": {"required": True, "pattern": r"\d+"}}
    v = load_schema_dict(data)
    assert isinstance(v, EnvValidator)


def test_load_schema_dict_empty():
    v = load_schema_dict({})
    assert v.validate({}, raise_on_error=False) == []


def test_load_schema_dict_invalid_rule_type():
    with pytest.raises(SchemaLoadError, match="must be a mapping"):
        load_schema_dict({"BAD": "not-a-dict"})


def test_load_schema_dict_validates_correctly():
    data = {
        "DB_URL": {"required": True},
        "LOG_LEVEL": {"allowed_values": ["DEBUG", "INFO", "WARNING"]},
    }
    v = load_schema_dict(data)
    errors = v.validate({"DB_URL": "postgres://localhost", "LOG_LEVEL": "INFO"}, raise_on_error=False)
    assert errors == []


# ---------------------------------------------------------------------------
# load_schema_file — JSON
# ---------------------------------------------------------------------------

def test_load_schema_file_json(tmp_path):
    schema = {"API_KEY": {"required": True, "min_length": 8}}
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(schema), encoding="utf-8")

    v = load_schema_file(schema_file)
    errors = v.validate({"API_KEY": "short"}, raise_on_error=False)
    assert any("too short" in e for e in errors)


def test_load_schema_file_json_valid(tmp_path):
    schema = {"API_KEY": {"required": True}}
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(schema), encoding="utf-8")

    v = load_schema_file(schema_file)
    errors = v.validate({"API_KEY": "mysecretkey"}, raise_on_error=False)
    assert errors == []


def test_load_schema_file_missing(tmp_path):
    with pytest.raises(SchemaLoadError, match="not found"):
        load_schema_file(tmp_path / "nonexistent.json")


def test_load_schema_file_unsupported_extension(tmp_path):
    f = tmp_path / "schema.yaml"
    f.write_text("PORT:\n  required: true\n")
    with pytest.raises(SchemaLoadError, match="Unsupported schema format"):
        load_schema_file(f)


def test_load_schema_file_invalid_json(tmp_path):
    f = tmp_path / "schema.json"
    f.write_text("{bad json", encoding="utf-8")
    with pytest.raises(SchemaLoadError, match="Failed to parse"):
        load_schema_file(f)
