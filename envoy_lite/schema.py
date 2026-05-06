"""TOML/dict-based schema loader that produces an EnvValidator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from envoy_lite.validator import EnvValidator, VarRule

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


class SchemaLoadError(Exception):
    """Raised when a schema file cannot be parsed."""


def _rule_from_dict(data: Dict[str, Any]) -> VarRule:
    return VarRule(
        required=bool(data.get("required", False)),
        pattern=data.get("pattern"),
        allowed_values=data.get("allowed_values"),
        min_length=data.get("min_length"),
        max_length=data.get("max_length"),
    )


def load_schema_dict(data: Dict[str, Any]) -> EnvValidator:
    """Build an EnvValidator from a plain dict (e.g. already parsed TOML/JSON)."""
    validator = EnvValidator()
    for key, rule_data in data.items():
        if not isinstance(rule_data, dict):
            raise SchemaLoadError(f"Rule for {key!r} must be a mapping, got {type(rule_data).__name__}")
        validator.add_rule(key, _rule_from_dict(rule_data))
    return validator


def load_schema_file(path: str | Path) -> EnvValidator:
    """Load a .toml or .json schema file and return an EnvValidator."""
    path = Path(path)
    suffix = path.suffix.lower()

    if not path.exists():
        raise SchemaLoadError(f"Schema file not found: {path}")

    try:
        if suffix == ".json":
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        elif suffix == ".toml":
            if tomllib is None:
                raise SchemaLoadError("TOML support requires Python 3.11+ or 'tomli' package")
            with path.open("rb") as fh:
                data = tomllib.load(fh)
        else:
            raise SchemaLoadError(f"Unsupported schema format: {suffix!r} (use .json or .toml)")
    except (json.JSONDecodeError, Exception) as exc:
        raise SchemaLoadError(f"Failed to parse schema file {path}: {exc}") from exc

    return load_schema_dict(data)
