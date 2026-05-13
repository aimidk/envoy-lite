"""Key rotation: rename keys with a version suffix and archive old values."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


class RotationError(Exception):
    """Raised when a rotation operation fails."""


_VERSION_RE = re.compile(r"^(.+?)_(v\d+)$")


def _versioned(key: str, version: int) -> str:
    """Return *key* with a version suffix, e.g. 'DB_URL_v2'."""
    return f"{key}_v{version}"


def current_version(key: str, env: Dict[str, str]) -> int:
    """Return the highest existing version number for *key* (0 if none)."""
    pattern = re.compile(rf"^{re.escape(key)}_v(\d+)$")
    versions = [
        int(m.group(1)) for k in env if (m := pattern.match(k))
    ]
    return max(versions, default=0)


def rotate_key(
    key: str,
    new_value: str,
    env: Dict[str, str],
    *,
    keep: int = 3,
) -> Dict[str, str]:
    """Rotate *key* to *new_value*.

    The current value is archived as ``<key>_v<N>`` and the live key is
    updated.  At most *keep* archived versions are retained (oldest pruned).

    Returns a **new** dict with the changes applied.
    """
    if not key:
        raise RotationError("key must not be empty")
    if keep < 1:
        raise RotationError("keep must be >= 1")

    result = dict(env)
    next_ver = current_version(key, env) + 1

    # Archive current live value (if present)
    if key in result:
        result[_versioned(key, next_ver)] = result[key]

    result[key] = new_value

    # Prune oldest archived versions beyond *keep*
    pattern = re.compile(rf"^{re.escape(key)}_v(\d+)$")
    archived: List[Tuple[int, str]] = sorted(
        ((int(m.group(1)), k) for k in list(result) if (m := pattern.match(k))),
        key=lambda t: t[0],
    )
    while len(archived) > keep:
        _, old_key = archived.pop(0)
        del result[old_key]

    return result


def list_versions(key: str, env: Dict[str, str]) -> List[Tuple[int, str]]:
    """Return archived versions of *key* sorted oldest-first.

    Each element is ``(version_number, value)``.
    """
    pattern = re.compile(rf"^{re.escape(key)}_v(\d+)$")
    versions = [
        (int(m.group(1)), env[k])
        for k in env
        if (m := pattern.match(k))
    ]
    return sorted(versions, key=lambda t: t[0])


def rollback(
    key: str,
    env: Dict[str, str],
    *,
    steps: int = 1,
) -> Dict[str, str]:
    """Roll *key* back by *steps* archived versions.

    The target archived entry becomes the live value and is removed from
    the archive.  Raises :class:`RotationError` if there are not enough
    archived versions.
    """
    if steps < 1:
        raise RotationError("steps must be >= 1")
    versions = list_versions(key, env)
    if len(versions) < steps:
        raise RotationError(
            f"cannot roll back {steps} step(s): only {len(versions)} version(s) archived"
        )
    target_ver, target_val = versions[-steps]
    result = dict(env)
    result[key] = target_val
    del result[_versioned(key, target_ver)]
    return result
