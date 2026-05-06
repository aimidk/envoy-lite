"""Alphabetical and grouped sorting utilities for env var dictionaries."""

from __future__ import annotations

from typing import Dict, List, Optional


class SortError(Exception):
    """Raised when sorting cannot be completed."""


def sort_dict(
    env: Dict[str, str],
    *,
    reverse: bool = False,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return a new dict sorted alphabetically by key.

    Args:
        env: The environment variable mapping to sort.
        reverse: If True, sort in descending order.
        case_sensitive: If True, sort with uppercase before lowercase (ASCII order).

    Returns:
        A new dict with keys in sorted order.
    """
    key_fn = (lambda k: k) if case_sensitive else (lambda k: k.lower())
    sorted_keys = sorted(env.keys(), key=key_fn, reverse=reverse)
    return {k: env[k] for k in sorted_keys}


def group_by_prefix(
    env: Dict[str, str],
    prefixes: List[str],
    *,
    others_last: bool = True,
) -> Dict[str, Dict[str, str]]:
    """Partition env vars into groups based on key prefixes.

    Keys matching the first applicable prefix are placed in that group.
    Unmatched keys land in the ``"__other__"`` group.

    Args:
        env: The environment variable mapping.
        prefixes: Ordered list of prefix strings to group by.
        others_last: Unused keys are collected under ``"__other__"``.

    Returns:
        An ordered dict of {prefix: {key: value}} mappings.
    """
    if not prefixes:
        raise SortError("prefixes list must not be empty")

    groups: Dict[str, Dict[str, str]] = {p: {} for p in prefixes}
    groups["__other__"] = {}

    for key, value in env.items():
        matched = False
        for prefix in prefixes:
            if key.startswith(prefix):
                groups[prefix][key] = value
                matched = True
                break
        if not matched:
            groups["__other__"][key] = value

    # Remove empty prefix buckets but always keep __other__ if others_last
    result: Dict[str, Dict[str, str]] = {}
    for prefix in prefixes:
        if groups[prefix]:
            result[prefix] = groups[prefix]
    if others_last and groups["__other__"]:
        result["__other__"] = groups["__other__"]

    return result


def sort_and_group(
    env: Dict[str, str],
    prefixes: Optional[List[str]] = None,
    *,
    reverse: bool = False,
) -> Dict[str, str]:
    """Sort env vars, optionally grouping by prefix first.

    Groups are sorted internally; groups themselves appear in prefix order.
    """
    if prefixes:
        groups = group_by_prefix(env, prefixes)
        merged: Dict[str, str] = {}
        for group in groups.values():
            merged.update(sort_dict(group, reverse=reverse))
        return merged
    return sort_dict(env, reverse=reverse)
