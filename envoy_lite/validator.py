"""Schema-based validation for loaded environment variables."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Pattern


class ValidationError(Exception):
    """Raised when one or more env var validation rules fail."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("Validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


@dataclass
class VarRule:
    """Validation rule for a single environment variable."""

    required: bool = False
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None

    _compiled: Optional[Pattern[str]] = field(default=None, init=False, repr=False)

    def compiled_pattern(self) -> Optional[Pattern[str]]:
        if self.pattern is not None and self._compiled is None:
            self._compiled = re.compile(self.pattern)
        return self._compiled


class EnvValidator:
    """Validates a dict of env vars against a set of VarRule definitions."""

    def __init__(self, rules: Optional[Dict[str, VarRule]] = None) -> None:
        self._rules: Dict[str, VarRule] = rules or {}

    def add_rule(self, key: str, rule: VarRule) -> None:
        self._rules[key] = rule

    def validate(self, env: Dict[str, str], *, raise_on_error: bool = True) -> List[str]:
        """Return a list of error strings; raise ValidationError if raise_on_error."""
        errors: List[str] = []

        for key, rule in self._rules.items():
            value = env.get(key)

            if rule.required and value is None:
                errors.append(f"{key}: required but not set")
                continue

            if value is None:
                continue

            if rule.min_length is not None and len(value) < rule.min_length:
                errors.append(f"{key}: value too short (min {rule.min_length})")

            if rule.max_length is not None and len(value) > rule.max_length:
                errors.append(f"{key}: value too long (max {rule.max_length})")

            pat = rule.compiled_pattern()
            if pat is not None and not pat.fullmatch(value):
                errors.append(f"{key}: value {value!r} does not match pattern {rule.pattern!r}")

            if rule.allowed_values is not None and value not in rule.allowed_values:
                errors.append(f"{key}: value {value!r} not in allowed set {rule.allowed_values}")

        if errors and raise_on_error:
            raise ValidationError(errors)

        return errors
