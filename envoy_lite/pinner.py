"""Snapshot and pin current environment variable values to a lockfile."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional


class PinError(Exception):
    """Raised when a pin operation fails."""


def pin_env(env: Dict[str, str], path: str | Path) -> None:
    """Write *env* as a JSON lockfile to *path*.

    The file is written atomically via a temp file so partial writes are
    never visible to readers.
    """
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(env, fh, indent=2, sort_keys=True)
            fh.write("\n")
        tmp.replace(path)
    except OSError as exc:
        raise PinError(f"Could not write pin file '{path}': {exc}") from exc


def load_pin(path: str | Path) -> Dict[str, str]:
    """Load a previously pinned lockfile and return it as a dict.

    Raises *PinError* if the file is missing or malformed.
    """
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise PinError(f"Pin file not found: '{path}'")
    except json.JSONDecodeError as exc:
        raise PinError(f"Pin file is not valid JSON: {exc}") from exc

    if not isinstance(data, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in data.items()
    ):
        raise PinError("Pin file must contain a flat JSON object of string values.")
    return data


def diff_pin(
    current: Dict[str, str], pinned: Dict[str, str]
) -> Dict[str, Dict[str, Optional[str]]]:
    """Return keys that differ between *current* and *pinned* env dicts.

    Each entry maps a key to ``{"current": ..., "pinned": ...}``.
    """
    all_keys = set(current) | set(pinned)
    result: Dict[str, Dict[str, Optional[str]]] = {}
    for key in sorted(all_keys):
        c_val = current.get(key)
        p_val = pinned.get(key)
        if c_val != p_val:
            result[key] = {"current": c_val, "pinned": p_val}
    return result
