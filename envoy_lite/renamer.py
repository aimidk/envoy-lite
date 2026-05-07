"""Key renaming utilities for env var dictionaries."""

from __future__ import annotations

import re
from typing import Dict, Callable, Optional


class RenameError(Exception):
    """Raised when a renaming operation fails."""


def rename_key(
    env: Dict[str, str],
    old_key: str,
    new_key: str,
    *,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Return a new dict with *old_key* renamed to *new_key*.

    Raises RenameError if *old_key* is not present or *new_key* already
    exists and *overwrite* is False.
    """
    if old_key not in env:
        raise RenameError(f"Key not found: {old_key!r}")
    if new_key in env and not overwrite:
        raise RenameError(
            f"Target key {new_key!r} already exists; pass overwrite=True to replace it"
        )
    result = dict(env)
    result[new_key] = result.pop(old_key)
    return result


def rename_prefix(
    env: Dict[str, str],
    old_prefix: str,
    new_prefix: str,
    *,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Return a new dict where every key starting with *old_prefix* has that
    prefix replaced by *new_prefix*.

    Raises RenameError on collision unless *overwrite* is True.
    """
    result: Dict[str, str] = {}
    renamed: Dict[str, str] = {}

    for key, value in env.items():
        if key.startswith(old_prefix):
            new_key = new_prefix + key[len(old_prefix):]
            renamed[new_key] = value
        else:
            result[key] = value

    for new_key, value in renamed.items():
        if new_key in result and not overwrite:
            raise RenameError(
                f"Rename collision: {new_key!r} already exists; pass overwrite=True"
            )
        result[new_key] = value

    return result


def apply_rename_map(
    env: Dict[str, str],
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
    skip_missing: bool = False,
) -> Dict[str, str]:
    """Apply a batch rename defined by *mapping* (old_key -> new_key).

    If *skip_missing* is True, keys absent from *env* are silently ignored;
    otherwise a RenameError is raised.
    """
    result = dict(env)
    for old_key, new_key in mapping.items():
        if old_key not in result:
            if skip_missing:
                continue
            raise RenameError(f"Key not found: {old_key!r}")
        result = rename_key(result, old_key, new_key, overwrite=overwrite)
    return result
