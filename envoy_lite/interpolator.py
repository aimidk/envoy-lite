"""Variable interpolation engine for envoy-lite.

Supports ${VAR}, ${VAR:-default}, and ${VAR:+alternate} syntax
when expanding values against a reference environment dict.
"""
from __future__ import annotations

import re
from typing import Dict, Optional

_INTERPOLATION_RE = re.compile(
    r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::(?P<op>[-+])(?P<word>[^}]*))?\}"
)


class InterpolationError(ValueError):
    """Raised when a required variable is missing during interpolation."""


def _resolve_token(
    name: str,
    op: Optional[str],
    word: Optional[str],
    env: Dict[str, str],
) -> str:
    """Return the replacement string for a single interpolation token."""
    value = env.get(name)

    if op is None:
        if value is None:
            raise InterpolationError(
                f"Variable '{name}' is not defined and has no default."
            )
        return value

    if op == "-":
        # ${VAR:-default} — use *word* when VAR is unset or empty
        return value if value else (word or "")

    if op == "+":
        # ${VAR:+alternate} — use *word* when VAR is set and non-empty
        return (word or "") if value else ""

    raise InterpolationError(f"Unknown interpolation operator: '{op}'")  # pragma: no cover


def interpolate(template: str, env: Dict[str, str]) -> str:
    """Replace all interpolation tokens in *template* using *env*.

    Args:
        template: A string potentially containing ``${...}`` tokens.
        env: Mapping of variable names to their current values.

    Returns:
        The fully interpolated string.

    Raises:
        InterpolationError: If a required variable is absent from *env*.
    """
    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        return _resolve_token(
            m.group("name"),
            m.group("op"),
            m.group("word"),
            env,
        )

    return _INTERPOLATION_RE.sub(_replace, template)


def interpolate_dict(
    mapping: Dict[str, str],
    base_env: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Interpolate every value in *mapping*, resolving references in order.

    Already-resolved entries are available to later entries, mirroring
    shell behaviour where variables defined earlier in a file are visible
    to later ones.

    Args:
        mapping: Ordered dict of raw key→value pairs.
        base_env: Optional pre-existing environment to seed resolution.

    Returns:
        New dict with all values interpolated.
    """
    resolved: Dict[str, str] = dict(base_env or {})
    result: Dict[str, str] = {}
    for key, raw in mapping.items():
        value = interpolate(raw, resolved)
        resolved[key] = value
        result[key] = value
    return result
