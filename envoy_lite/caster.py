"""Type casting utilities for environment variable values."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict


class CastError(Exception):
    """Raised when a value cannot be cast to the requested type."""

    def __init__(self, key: str, value: str, target_type: str) -> None:
        self.key = key
        self.value = value
        self.target_type = target_type
        super().__init__(
            f"Cannot cast {key}={value!r} to {target_type}"
        )


_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def _cast_bool(value: str) -> bool:
    lower = value.strip().lower()
    if lower in _TRUE_VALUES:
        return True
    if lower in _FALSE_VALUES:
        return False
    raise ValueError(f"Cannot interpret {value!r} as bool")


_CASTERS: Dict[str, Callable[[str], Any]] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": _cast_bool,
    "json": json.loads,
}


def register_caster(name: str, fn: Callable[[str], Any]) -> None:
    """Register a custom caster under *name*."""
    _CASTERS[name] = fn


def cast_value(key: str, value: str, target_type: str) -> Any:
    """Cast *value* (string) to *target_type*.

    Parameters
    ----------
    key:
        Variable name — used only for error messages.
    value:
        Raw string value to cast.
    target_type:
        One of ``str``, ``int``, ``float``, ``bool``, ``json``, or any
        name registered via :func:`register_caster`.

    Raises
    ------
    CastError
        If the conversion fails or the type is unknown.
    """
    caster = _CASTERS.get(target_type)
    if caster is None:
        raise CastError(key, value, target_type)
    try:
        return caster(value)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise CastError(key, value, target_type) from exc


def cast_dict(
    env: Dict[str, str],
    schema: Dict[str, str],
    *,
    strict: bool = False,
) -> Dict[str, Any]:
    """Cast every key in *env* that appears in *schema*.

    Parameters
    ----------
    env:
        Raw string environment mapping.
    schema:
        Mapping of variable name → target type string.
    strict:
        If ``True``, raise :class:`CastError` for keys in *schema* that
        are absent from *env*.  Otherwise those keys are skipped.
    """
    result: Dict[str, Any] = dict(env)
    for key, target_type in schema.items():
        if key not in env:
            if strict:
                raise CastError(key, "", target_type)
            continue
        result[key] = cast_value(key, env[key], target_type)
    return result
