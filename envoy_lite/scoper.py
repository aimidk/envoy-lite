"""Scope filtering: restrict env dicts to a named scope prefix with optional stripping."""

from __future__ import annotations

import re
from typing import Dict, List, Optional


class ScopeError(Exception):
    """Raised when a scoping operation fails."""


def scope_filter(
    env: Dict[str, str],
    scope: str,
    *,
    strip_prefix: bool = True,
    separator: str = "__",
) -> Dict[str, str]:
    """Return only keys that belong to *scope*, optionally stripping the prefix.

    Args:
        env: Source environment dictionary.
        scope: Scope name (case-insensitive match against key prefix).
        strip_prefix: When True the ``SCOPE__`` prefix is removed from keys.
        separator: String that separates scope from the rest of the key.

    Returns:
        Filtered (and optionally re-keyed) dictionary.

    Raises:
        ScopeError: If *scope* is empty or *separator* is empty.
    """
    if not scope:
        raise ScopeError("scope must not be empty")
    if not separator:
        raise ScopeError("separator must not be empty")

    prefix = scope.upper() + separator
    result: Dict[str, str] = {}
    for key, value in env.items():
        if key.upper().startswith(prefix):
            new_key = key[len(prefix):] if strip_prefix else key
            result[new_key] = value
    return result


def list_scopes(
    env: Dict[str, str],
    separator: str = "__",
) -> List[str]:
    """Return a sorted list of unique scope names present in *env*.

    A scope is the uppercase segment before the first *separator*.

    Args:
        env: Source environment dictionary.
        separator: String that separates scope from the rest of the key.

    Returns:
        Sorted list of unique scope names (uppercase).
    """
    scopes: set = set()
    for key in env:
        if separator in key:
            scopes.add(key.split(separator, 1)[0].upper())
    return sorted(scopes)


def merge_scopes(
    env: Dict[str, str],
    scopes: List[str],
    *,
    separator: str = "__",
    strip_prefix: bool = True,
    last_wins: bool = True,
) -> Dict[str, str]:
    """Merge multiple scopes into a single dict.

    Args:
        env: Source environment dictionary.
        scopes: Ordered list of scope names to merge.
        separator: Scope/key separator.
        strip_prefix: Strip scope prefix from result keys.
        last_wins: If True, later scopes override earlier ones.

    Returns:
        Merged dictionary.
    """
    result: Dict[str, str] = {}
    for scope in scopes:
        filtered = scope_filter(env, scope, strip_prefix=strip_prefix, separator=separator)
        if last_wins:
            result.update(filtered)
        else:
            for k, v in filtered.items():
                result.setdefault(k, v)
    return result
