"""Deduplication utilities for environment variable dictionaries."""

from __future__ import annotations

from typing import Dict, List, Tuple


class DeduplicateError(Exception):
    """Raised when deduplication encounters an unresolvable conflict."""


StrategyName = str  # 'first' | 'last' | 'error'


def deduplicate(
    pairs: List[Tuple[str, str]],
    strategy: StrategyName = "last",
) -> Dict[str, str]:
    """Collapse a list of (key, value) pairs that may contain duplicate keys.

    Parameters
    ----------
    pairs:
        Ordered sequence of key/value tuples, e.g. from parsing multiple files
        concatenated together.
    strategy:
        How to handle duplicate keys.
        - ``'last'``  – keep the last occurrence (default, mirrors shell behaviour).
        - ``'first'`` – keep the first occurrence.
        - ``'error'`` – raise :class:`DeduplicateError` on the first duplicate.

    Returns
    -------
    dict
        Deduplicated mapping preserving insertion order of the winning key.
    """
    if strategy not in ("first", "last", "error"):
        raise ValueError(f"Unknown strategy {strategy!r}; choose 'first', 'last', or 'error'.")

    result: Dict[str, str] = {}
    seen: Dict[str, int] = {}  # key -> index of first occurrence

    for idx, (key, value) in enumerate(pairs):
        if key in seen:
            if strategy == "error":
                raise DeduplicateError(
                    f"Duplicate key {key!r} found at positions {seen[key]} and {idx}."
                )
            if strategy == "last":
                result[key] = value
            # strategy == 'first': do nothing, keep original
        else:
            seen[key] = idx
            result[key] = value

    return result


def find_duplicates(pairs: List[Tuple[str, str]]) -> Dict[str, List[int]]:
    """Return a mapping of key -> list of positions where it appears more than once.

    Keys that appear exactly once are **not** included in the result.
    """
    positions: Dict[str, List[int]] = {}
    for idx, (key, _) in enumerate(pairs):
        positions.setdefault(key, []).append(idx)
    return {k: v for k, v in positions.items() if len(v) > 1}
