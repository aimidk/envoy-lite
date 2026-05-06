"""Export loaded environment variables to various shell-compatible formats."""

from __future__ import annotations

from typing import Dict, Iterable, Literal

Format = Literal["export", "dotenv", "json", "csv"]


class UnsupportedFormatError(ValueError):
    """Raised when an unknown export format is requested."""


def _quote_value(value: str) -> str:
    """Wrap *value* in double-quotes, escaping inner double-quotes."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def to_export_shell(env: Dict[str, str]) -> str:
    """Return POSIX ``export KEY=VALUE`` lines."""
    lines = [f"export {k}={_quote_value(v)}" for k, v in sorted(env.items())]
    return "\n".join(lines)


def to_dotenv(env: Dict[str, str]) -> str:
    """Return plain ``KEY=VALUE`` lines compatible with .env files."""
    lines = [f"{k}={_quote_value(v)}" for k, v in sorted(env.items())]
    return "\n".join(lines)


def to_json(env: Dict[str, str]) -> str:
    """Return a pretty-printed JSON object."""
    import json

    return json.dumps(dict(sorted(env.items())), indent=2)


def to_csv(env: Dict[str, str]) -> str:
    """Return ``key,value`` CSV rows (header included)."""
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["key", "value"])
    for k, v in sorted(env.items()):
        writer.writerow([k, v])
    return buf.getvalue().rstrip("\n")


_FORMATTERS = {
    "export": to_export_shell,
    "dotenv": to_dotenv,
    "json": to_json,
    "csv": to_csv,
}


def export_env(
    env: Dict[str, str],
    fmt: Format = "dotenv",
    keys: Iterable[str] | None = None,
) -> str:
    """Render *env* in the requested *fmt*.

    Parameters
    ----------
    env:  Mapping of variable names to values.
    fmt:  One of ``'export'``, ``'dotenv'``, ``'json'``, ``'csv'``.
    keys: Optional allowlist of keys to include.  All keys are included when
          *keys* is ``None``.
    """
    if fmt not in _FORMATTERS:
        raise UnsupportedFormatError(
            f"Unknown format {fmt!r}. Choose from: {', '.join(_FORMATTERS)}"
        )
    if keys is not None:
        env = {k: env[k] for k in keys if k in env}
    return _FORMATTERS[fmt](env)
