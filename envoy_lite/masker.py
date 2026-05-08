"""Value masking utilities for partial redaction of sensitive env var values."""

from __future__ import annotations

import re
from typing import Dict, Optional


class MaskError(Exception):
    """Raised when masking cannot be applied."""


def mask_middle(value: str, visible: int = 4, char: str = "*") -> str:
    """Reveal *visible* chars at each end; replace the middle with *char*.

    If the value is too short to have a middle, the entire value is masked.
    """
    if visible < 0:
        raise MaskError("visible must be >= 0")
    if len(char) != 1:
        raise MaskError("char must be exactly one character")
    total_visible = visible * 2
    if len(value) <= total_visible:
        return char * len(value)
    middle_len = len(value) - total_visible
    return value[:visible] + char * middle_len + value[len(value) - visible:]


def mask_suffix(value: str, visible: int = 4, char: str = "*") -> str:
    """Reveal only the last *visible* characters; mask the prefix."""
    if visible < 0:
        raise MaskError("visible must be >= 0")
    if len(char) != 1:
        raise MaskError("char must be exactly one character")
    if len(value) <= visible:
        return value
    return char * (len(value) - visible) + value[len(value) - visible:]


def mask_pattern(value: str, pattern: str, replacement: str = "***") -> str:
    """Replace regex *pattern* matches within *value* with *replacement*."""
    try:
        return re.sub(pattern, replacement, value)
    except re.error as exc:
        raise MaskError(f"Invalid pattern '{pattern}': {exc}") from exc


def mask_dict(
    env: Dict[str, str],
    keys: Optional[list] = None,
    strategy: str = "suffix",
    visible: int = 4,
    char: str = "*",
) -> Dict[str, str]:
    """Return a copy of *env* with specified *keys* masked.

    strategy: 'suffix' | 'middle'
    If *keys* is None, all values are masked.
    """
    strategies = {"suffix": mask_suffix, "middle": mask_middle}
    if strategy not in strategies:
        raise MaskError(f"Unknown strategy '{strategy}'. Choose from: {list(strategies)}")
    fn = strategies[strategy]
    target_keys = set(keys) if keys is not None else set(env.keys())
    return {
        k: fn(v, visible=visible, char=char) if k in target_keys else v
        for k, v in env.items()
    }
