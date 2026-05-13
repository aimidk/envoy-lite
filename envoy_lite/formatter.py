"""Key/value formatter for env dicts — controls output style and alignment."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional


class FormatError(Exception):
    """Raised when formatting cannot be completed."""


_VALID_STYLES = ("plain", "aligned", "export")


def _longest_key(keys: Iterable[str]) -> int:
    """Return the length of the longest key, or 0 if empty."""
    try:
        return max(len(k) for k in keys)
    except ValueError:
        return 0


def format_pair(key: str, value: str, *, style: str = "plain", pad: int = 0) -> str:
    """Format a single key/value pair.

    Args:
        key:   The variable name.
        value: The variable value.
        style: One of ``plain``, ``aligned``, or ``export``.
        pad:   Minimum width for the key column (used by ``aligned``).

    Returns:
        A formatted string (no trailing newline).

    Raises:
        FormatError: If *style* is not recognised.
    """
    if style not in _VALID_STYLES:
        raise FormatError(
            f"Unknown style {style!r}. Choose from: {', '.join(_VALID_STYLES)}"
        )
    if style == "export":
        return f"export {key}={value}"
    if style == "aligned":
        return f"{key:<{pad}}={value}"
    # plain
    return f"{key}={value}"


def format_dict(
    env: Dict[str, str],
    *,
    style: str = "plain",
    sort: bool = True,
    pad: Optional[int] = None,
) -> List[str]:
    """Format an entire env dict into a list of lines.

    Args:
        env:   Mapping of variable names to values.
        style: Formatting style (``plain``, ``aligned``, ``export``).
        sort:  Whether to sort keys alphabetically before formatting.
        pad:   Override the key-column width for ``aligned`` style.
               Defaults to the longest key length.

    Returns:
        A list of formatted strings, one per variable.

    Raises:
        FormatError: If *style* is not recognised.
    """
    if style not in _VALID_STYLES:
        raise FormatError(
            f"Unknown style {style!r}. Choose from: {', '.join(_VALID_STYLES)}"
        )

    keys = sorted(env) if sort else list(env)

    column_width: int = pad if pad is not None else _longest_key(keys)

    return [
        format_pair(k, env[k], style=style, pad=column_width)
        for k in keys
    ]
