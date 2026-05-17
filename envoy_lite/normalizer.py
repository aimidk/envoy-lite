"""Key and value normalization utilities for envoy-lite."""

from __future__ import annotations

import re
from typing import Dict, Optional


class NormalizeError(Exception):
    """Raised when normalization cannot be applied."""


_INVALID_KEY_CHARS = re.compile(r"[^A-Z0-9_]")
_LEADING_DIGIT = re.compile(r"^[0-9]")


def normalize_key(key: str, *, uppercase: bool = True, strip: bool = True) -> str:
    """Normalize an environment variable key.

    - Strips surrounding whitespace (if *strip* is True).
    - Converts to uppercase (if *uppercase* is True).
    - Replaces spaces and hyphens with underscores.
    - Removes any remaining characters that are not A-Z, 0-9, or '_'.

    Raises :class:`NormalizeError` if the resulting key is empty or starts
    with a digit.
    """
    if strip:
        key = key.strip()
    if uppercase:
        key = key.upper()
    key = key.replace(" ", "_").replace("-", "_")
    key = _INVALID_KEY_CHARS.sub("", key)
    if not key:
        raise NormalizeError("Key is empty after normalization.")
    if _LEADING_DIGIT.match(key):
        raise NormalizeError(f"Normalized key '{key}' starts with a digit.")
    return key


def normalize_value(value: str, *, strip: bool = True, collapse_whitespace: bool = False) -> str:
    """Normalize an environment variable value.

    - Strips surrounding whitespace (if *strip* is True).
    - Collapses internal runs of whitespace to a single space
      (if *collapse_whitespace* is True).
    """
    if strip:
        value = value.strip()
    if collapse_whitespace:
        value = re.sub(r"\s+", " ", value)
    return value


def normalize_dict(
    env: Dict[str, str],
    *,
    uppercase: bool = True,
    strip_keys: bool = True,
    strip_values: bool = True,
    collapse_whitespace: bool = False,
    skip_errors: bool = False,
) -> Dict[str, str]:
    """Return a new dict with all keys and values normalized.

    If *skip_errors* is True, keys that fail normalization are silently
    dropped; otherwise :class:`NormalizeError` is re-raised.
    """
    result: Dict[str, str] = {}
    for raw_key, raw_value in env.items():
        try:
            norm_key = normalize_key(raw_key, uppercase=uppercase, strip=strip_keys)
        except NormalizeError:
            if skip_errors:
                continue
            raise
        norm_value = normalize_value(
            raw_value, strip=strip_values, collapse_whitespace=collapse_whitespace
        )
        result[norm_key] = norm_value
    return result
