"""sanitizer.py — Strip, replace, or remove unsafe characters from env var keys and values."""

from __future__ import annotations

import re
from typing import Dict, Optional


class SanitizeError(Exception):
    """Raised when a sanitization operation cannot be completed."""


_SAFE_KEY_RE = re.compile(r"[^A-Z0-9_]")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_key(
    key: str,
    *,
    replacement: str = "_",
    uppercase: bool = True,
) -> str:
    """Return *key* with any character outside ``[A-Z0-9_]`` replaced.

    Args:
        key: The raw environment variable name.
        replacement: Character used to replace invalid characters (default ``_``).
        uppercase: When *True* (default) the key is uppercased before sanitising.

    Raises:
        SanitizeError: If *replacement* itself is not a valid key character.
    """
    if replacement and _SAFE_KEY_RE.search(replacement):
        raise SanitizeError(
            f"replacement {replacement!r} contains characters not allowed in a key"
        )
    if not key:
        raise SanitizeError("key must not be empty")
    if uppercase:
        key = key.upper()
    return _SAFE_KEY_RE.sub(replacement, key)


def sanitize_value(
    value: str,
    *,
    strip_control: bool = True,
    replacement: str = "",
) -> str:
    """Return *value* with control characters removed or replaced.

    Args:
        value: The raw environment variable value.
        strip_control: When *True* (default) control characters (0x00-0x1f, 0x7f)
            are replaced with *replacement*.
        replacement: Substitution string for removed characters (default empty).

    Returns:
        Sanitised string.
    """
    if strip_control:
        return _CONTROL_RE.sub(replacement, value)
    return value


def sanitize_dict(
    env: Dict[str, str],
    *,
    key_replacement: str = "_",
    uppercase_keys: bool = True,
    strip_control: bool = True,
    on_collision: str = "error",
) -> Dict[str, str]:
    """Sanitise every key and value in *env*.

    Args:
        env: Mapping of raw env var names to values.
        key_replacement: Passed to :func:`sanitize_key`.
        uppercase_keys: Passed to :func:`sanitize_key`.
        strip_control: Passed to :func:`sanitize_value`.
        on_collision: What to do when two keys normalise to the same string.
            ``"error"`` (default) raises :class:`SanitizeError`;
            ``"last"`` keeps the last value encountered.

    Returns:
        New dict with sanitised keys and values.

    Raises:
        SanitizeError: On key collision when *on_collision* is ``"error"``.
    """
    if on_collision not in ("error", "last"):
        raise SanitizeError(f"unknown on_collision strategy: {on_collision!r}")

    result: Dict[str, str] = {}
    for raw_key, raw_value in env.items():
        clean_key = sanitize_key(raw_key, replacement=key_replacement, uppercase=uppercase_keys)
        clean_value = sanitize_value(raw_value, strip_control=strip_control)
        if clean_key in result and on_collision == "error":
            raise SanitizeError(
                f"key collision after sanitisation: {raw_key!r} -> {clean_key!r}"
            )
        result[clean_key] = clean_value
    return result
