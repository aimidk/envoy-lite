"""Flatten nested dict structures into env-style KEY_SUBKEY pairs."""

from __future__ import annotations

from typing import Any, Dict, Optional


class FlattenError(Exception):
    """Raised when flattening fails due to invalid input."""


def flatten(
    data: Dict[str, Any],
    separator: str = "_",
    prefix: str = "",
    uppercase: bool = True,
) -> Dict[str, str]:
    """Recursively flatten *data* into a single-level dict of strings.

    Nested keys are joined with *separator*.  All keys are uppercased when
    *uppercase* is ``True`` (the default, consistent with env-var conventions).

    Args:
        data:       Possibly-nested mapping to flatten.
        separator:  String used to join key segments.  Defaults to ``"_"``.
        prefix:     Optional prefix prepended to every top-level key.
        uppercase:  When ``True`` (default) all keys are uppercased.

    Returns:
        A flat ``dict[str, str]`` suitable for use as environment variables.

    Raises:
        FlattenError: If *data* is not a dict, or if a key segment is empty.
    """
    if not isinstance(data, dict):
        raise FlattenError(f"Expected a dict, got {type(data).__name__}")
    if not separator:
        raise FlattenError("separator must be a non-empty string")

    result: Dict[str, str] = {}
    _flatten_recursive(data, separator=separator, prefix=prefix, uppercase=uppercase, out=result)
    return result


def _flatten_recursive(
    data: Dict[str, Any],
    separator: str,
    prefix: str,
    uppercase: bool,
    out: Dict[str, str],
) -> None:
    for key, value in data.items():
        if not isinstance(key, str):
            raise FlattenError(f"All keys must be strings; got {type(key).__name__}")
        segment = key.upper() if uppercase else key
        full_key = f"{prefix}{separator}{segment}" if prefix else segment
        if isinstance(value, dict):
            _flatten_recursive(
                value,
                separator=separator,
                prefix=full_key,
                uppercase=uppercase,
                out=out,
            )
        else:
            out[full_key] = str(value) if value is not None else ""


def unflatten(
    data: Dict[str, str],
    separator: str = "_",
) -> Dict[str, Any]:
    """Reverse of :func:`flatten` — reconstruct a nested dict from flat keys.

    Only the *first* occurrence of *separator* is used to split each key,
    so ``A_B_C`` becomes ``{"A": {"B_C": ...}}``.

    Args:
        data:       Flat mapping (as produced by :func:`flatten`).
        separator:  Separator that was used during flattening.

    Returns:
        A nested ``dict``.

    Raises:
        FlattenError: If *data* is not a dict or *separator* is empty.
    """
    if not isinstance(data, dict):
        raise FlattenError(f"Expected a dict, got {type(data).__name__}")
    if not separator:
        raise FlattenError("separator must be a non-empty string")

    result: Dict[str, Any] = {}
    for key, value in data.items():
        if separator in key:
            head, tail = key.split(separator, 1)
            nested = result.setdefault(head, {})
            if not isinstance(nested, dict):
                raise FlattenError(
                    f"Key conflict: '{head}' is both a leaf and a branch"
                )
            nested[tail] = value
        else:
            if key in result and isinstance(result[key], dict):
                raise FlattenError(
                    f"Key conflict: '{key}' is both a leaf and a branch"
                )
            result[key] = value
    return result
