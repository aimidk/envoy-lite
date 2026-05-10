"""freezer.py — Freeze and restore environment variable snapshots to/from disk."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional


class FreezeError(Exception):
    """Raised when a freeze or thaw operation fails."""


def freeze(env: Dict[str, str], path: str | Path, *, overwrite: bool = False) -> Path:
    """Serialize *env* to a JSON file at *path*.

    Parameters
    ----------
    env:       Mapping of variable names to values to persist.
    path:      Destination file path.
    overwrite: When False (default) raise FreezeError if the file exists.

    Returns the resolved Path that was written.
    """
    dest = Path(path)
    if dest.exists() and not overwrite:
        raise FreezeError(
            f"Freeze file already exists: {dest}. Pass overwrite=True to replace it."
        )
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            json.dumps(dict(sorted(env.items())), indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise FreezeError(f"Could not write freeze file '{dest}': {exc}") from exc
    return dest


def thaw(path: str | Path) -> Dict[str, str]:
    """Load a frozen environment from *path* and return it as a plain dict.

    Raises FreezeError if the file is missing or contains invalid JSON.
    """
    src = Path(path)
    if not src.exists():
        raise FreezeError(f"Freeze file not found: {src}")
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FreezeError(f"Invalid JSON in freeze file '{src}': {exc}") from exc
    if not isinstance(data, dict):
        raise FreezeError(f"Freeze file must contain a JSON object, got {type(data).__name__}")
    return {str(k): str(v) for k, v in data.items()}


def apply_thaw(env: Dict[str, str], path: str | Path, *, override: bool = True) -> Dict[str, str]:
    """Merge a frozen snapshot into *env*.

    Parameters
    ----------
    env:      Base environment dict (not mutated).
    path:     Path to the freeze file.
    override: When True (default) frozen values overwrite existing keys.

    Returns a new merged dict.
    """
    frozen = thaw(path)
    if override:
        return {**env, **frozen}
    return {**frozen, **env}
