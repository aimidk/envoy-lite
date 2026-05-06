"""Merge multiple env files with configurable precedence."""

from __future__ import annotations

from typing import Dict, List, Optional

from envoy_lite.loader import load_env_file


class MergeConflict(Exception):
    """Raised when strict mode detects a key defined in multiple sources."""

    def __init__(self, key: str, sources: List[str]) -> None:
        self.key = key
        self.sources = sources
        super().__init__(
            f"Key '{key}' defined in multiple sources: {', '.join(sources)}"
        )


def merge_env_files(
    paths: List[str],
    *,
    override: bool = True,
    strict: bool = False,
    missing_ok: bool = False,
) -> Dict[str, str]:
    """Merge env files in order.

    Args:
        paths: Ordered list of .env file paths. Later files take precedence
               when *override* is True (default), otherwise earlier files win.
        override: If True, later files overwrite earlier values for the same key.
        strict: If True, raise :class:`MergeConflict` when any key appears in
                more than one file, regardless of *override*.
        missing_ok: If True, silently skip files that do not exist.

    Returns:
        Merged mapping of variable names to values.
    """
    if not paths:
        return {}

    # key -> list of (path, value) tuples
    seen: Dict[str, List[str]] = {}
    result: Dict[str, str] = {}

    for path in paths:
        try:
            env = load_env_file(path)
        except FileNotFoundError:
            if missing_ok:
                continue
            raise

        for key, value in env.items():
            if key in seen:
                seen[key].append(path)
                if strict:
                    raise MergeConflict(key, seen[key])
                if override:
                    result[key] = value
            else:
                seen[key] = [path]
                result[key] = value

    return result


def merge_with_os_environ(
    paths: List[str],
    os_environ: Optional[Dict[str, str]] = None,
    *,
    env_wins: bool = False,
    missing_ok: bool = False,
) -> Dict[str, str]:
    """Merge env files then layer os.environ on top (or below).

    Args:
        paths: Env file paths passed to :func:`merge_env_files`.
        os_environ: Mapping to treat as the OS environment; defaults to
                    ``os.environ`` when *None*.
        env_wins: If True, values from env files take precedence over the OS
                  environment; otherwise the OS environment wins.
        missing_ok: Forwarded to :func:`merge_env_files`.

    Returns:
        Merged mapping.
    """
    import os

    base = dict(os_environ if os_environ is not None else os.environ)
    file_vars = merge_env_files(paths, missing_ok=missing_ok)

    if env_wins:
        base.update(file_vars)
        return base
    else:
        file_vars.update(base)
        return file_vars
