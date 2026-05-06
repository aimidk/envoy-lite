"""Tests for envoy_lite.validator."""

import pytest

from envoy_lite.validator import EnvValidator, ValidationError, VarRule


# ---------------------------------------------------------------------------
# VarRule helpers
# ---------------------------------------------------------------------------

def test_var_rule_defaults():
    rule = VarRule()
    assert rule.required is False
    assert rule.pattern is None
    assert rule.allowed_values is None


def test_compiled_pattern_cached():
    rule = VarRule(pattern=r"\d+")
    p1 = rule.compiled_pattern()
    p2 = rule.compiled_pattern()
    assert p1 is p2  # same object — cached


# ---------------------------------------------------------------------------
# EnvValidator.validate — happy paths
# ---------------------------------------------------------------------------

def test_validate_empty_rules_always_passes():
    validator = EnvValidator()
    errors = validator.validate({"FOO": "bar"}, raise_on_error=False)
    assert errors == []


def test_validate_required_present():
    validator = EnvValidator({"DB_URL": VarRule(required=True)})
    errors = validator.validate({"DB_URL": "postgres://localhost/db"}, raise_on_error=False)
    assert errors == []


def test_validate_pattern_match():
    validator = EnvValidator({"PORT": VarRule(pattern=r"\d{4,5}")})
    errors = validator.validate({"PORT": "8080"}, raise_on_error=False)
    assert errors == []


def test_validate_allowed_values_ok():
    rule = VarRule(allowed_values=["dev", "staging", "prod"])
    validator = EnvValidator({"ENV": rule})
    errors = validator.validate({"ENV": "staging"}, raise_on_error=False)
    assert errors == []


# ---------------------------------------------------------------------------
# EnvValidator.validate — error cases
# ---------------------------------------------------------------------------

def test_validate_required_missing():
    validator = EnvValidator({"SECRET_KEY": VarRule(required=True)})
    errors = validator.validate({}, raise_on_error=False)
    assert any("SECRET_KEY" in e and "required" in e for e in errors)


def test_validate_pattern_mismatch():
    validator = EnvValidator({"PORT": VarRule(pattern=r"\d+")})
    errors = validator.validate({"PORT": "not-a-number"}, raise_on_error=False)
    assert len(errors) == 1
    assert "PORT" in errors[0]


def test_validate_allowed_values_fail():
    rule = VarRule(allowed_values=["dev", "prod"])
    validator = EnvValidator({"ENV": rule})
    errors = validator.validate({"ENV": "test"}, raise_on_error=False)
    assert len(errors) == 1


def test_validate_min_length_fail():
    validator = EnvValidator({"TOKEN": VarRule(min_length=10)})
    errors = validator.validate({"TOKEN": "short"}, raise_on_error=False)
    assert any("too short" in e for e in errors)


def test_validate_max_length_fail():
    validator = EnvValidator({"LABEL": VarRule(max_length=5)})
    errors = validator.validate({"LABEL": "toolongvalue"}, raise_on_error=False)
    assert any("too long" in e for e in errors)


def test_validate_raises_validation_error():
    validator = EnvValidator({"DB_URL": VarRule(required=True)})
    with pytest.raises(ValidationError) as exc_info:
        validator.validate({})
    assert exc_info.value.errors


def test_validation_error_message_contains_details():
    validator = EnvValidator({"DB_URL": VarRule(required=True)})
    with pytest.raises(ValidationError) as exc_info:
        validator.validate({})
    assert "DB_URL" in str(exc_info.value)


def test_add_rule_dynamically():
    validator = EnvValidator()
    validator.add_rule("API_KEY", VarRule(required=True))
    errors = validator.validate({}, raise_on_error=False)
    assert any("API_KEY" in e for e in errors)
