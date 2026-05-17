"""Trimmer: remove keys from an env dict by exact match, prefix, or pattern."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Optional


class TrimError(Exception):
    """Raised when a trim operation fails."""


def trim_keys(
    env: Dict[str, str],
    keys: Iterable[str],
    *,
    strict: bool = False,
) -> Dict[str, str]:
    """Remove exact *keys* from *env*.

    Args:
        env: Source mapping.
        keys: Iterable of key names to remove.
        strict: If True, raise TrimError when a key is not present.

    Returns:
        New dict with the specified keys removed.
    """
    result = dict(env)
    for key in keys:
        if key not in result:
            if strict:
                raise TrimError(f"Key not found: {key!r}")
        else:
            del result[key]
    return result


def trim_by_prefix(
    env: Dict[str, str],
    prefix: str,
    *,
    case_sensitive: bool = True,
) -> Dict[str, str]:
    """Remove all keys that start with *prefix*.

    Args:
        env: Source mapping.
        prefix: Prefix string to match.
        case_sensitive: When False, comparison is done in lower-case.

    Returns:
        New dict with matching keys removed.
    """
    if not prefix:
        raise TrimError("prefix must not be empty")
    cmp_prefix = prefix if case_sensitive else prefix.lower()
    return {
        k: v
        for k, v in env.items()
        if (k if case_sensitive else k.lower()) != cmp_prefix
        and not (k if case_sensitive else k.lower()).startswith(cmp_prefix)
    }


def trim_by_pattern(
    env: Dict[str, str],
    pattern: str,
    *,
    flags: int = 0,
) -> Dict[str, str]:
    """Remove all keys whose names match the regex *pattern*.

    Args:
        env: Source mapping.
        pattern: Regular-expression pattern string.
        flags: Optional ``re`` flags (e.g. ``re.IGNORECASE``).

    Returns:
        New dict with matching keys removed.
    """
    try:
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        raise TrimError(f"Invalid pattern {pattern!r}: {exc}") from exc
    return {k: v for k, v in env.items() if not compiled.search(k)}
