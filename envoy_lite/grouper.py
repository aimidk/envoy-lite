"""Group and filter environment variables by prefix, suffix, or pattern."""

from __future__ import annotations

import re
from typing import Dict, List, Optional


class GroupError(Exception):
    """Raised when grouping parameters are invalid."""


def filter_by_prefix(env: Dict[str, str], prefix: str, *, strip: bool = False) -> Dict[str, str]:
    """Return keys that start with *prefix*.

    If *strip* is True the prefix is removed from the returned keys.
    """
    if not prefix:
        raise GroupError("prefix must be a non-empty string")
    result: Dict[str, str] = {}
    for key, value in env.items():
        if key.startswith(prefix):
            new_key = key[len(prefix):] if strip else key
            result[new_key] = value
    return result


def filter_by_suffix(env: Dict[str, str], suffix: str, *, strip: bool = False) -> Dict[str, str]:
    """Return keys that end with *suffix*.

    If *strip* is True the suffix is removed from the returned keys.
    """
    if not suffix:
        raise GroupError("suffix must be a non-empty string")
    result: Dict[str, str] = {}
    for key, value in env.items():
        if key.endswith(suffix):
            new_key = key[: -len(suffix)] if strip else key
            result[new_key] = value
    return result


def filter_by_pattern(env: Dict[str, str], pattern: str) -> Dict[str, str]:
    """Return keys whose names fully match the regex *pattern*."""
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise GroupError(f"invalid pattern {pattern!r}: {exc}") from exc
    return {k: v for k, v in env.items() if compiled.fullmatch(k)}


def group_by_prefixes(
    env: Dict[str, str],
    prefixes: List[str],
    *,
    strip: bool = False,
    other_key: Optional[str] = "other",
) -> Dict[str, Dict[str, str]]:
    """Partition *env* into groups keyed by each prefix.

    Keys that do not match any prefix are placed under *other_key*.
    Pass ``other_key=None`` to discard unmatched keys.
    """
    if not prefixes:
        raise GroupError("at least one prefix is required")

    groups: Dict[str, Dict[str, str]] = {p: {} for p in prefixes}
    if other_key is not None:
        groups[other_key] = {}

    for key, value in env.items():
        matched = False
        for prefix in prefixes:
            if key.startswith(prefix):
                stored_key = key[len(prefix):] if strip else key
                groups[prefix][stored_key] = value
                matched = True
                break
        if not matched and other_key is not None:
            groups[other_key][key] = value

    return groups
