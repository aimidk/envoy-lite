"""Core .env file loader with support for variable expansion and comments."""

import os
import re
from pathlib import Path
from typing import Dict, Optional


VAR_EXPAND_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


def _expand_value(value: str, env: Dict[str, str]) -> str:
    """Expand ${VAR} or $VAR references within a value string."""
    def replacer(match: re.Match) -> str:
        key = match.group(1) or match.group(2)
        return env.get(key, os.environ.get(key, ""))

    return VAR_EXPAND_RE.sub(replacer, value)


def _parse_line(line: str) -> Optional[tuple[str, str]]:
    """Parse a single .env line into a (key, value) pair or None."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # Strip optional 'export ' prefix
    if line.startswith("export "):
        line = line[7:].strip()

    if "=" not in line:
        return None

    key, _, raw_value = line.partition("=")
    key = key.strip()
    raw_value = raw_value.strip()

    # Strip inline comments (only outside quotes)
    if raw_value and raw_value[0] not in ('"', "'"):
        raw_value = raw_value.split(" #")[0].strip()

    # Strip surrounding quotes
    if len(raw_value) >= 2 and raw_value[0] == raw_value[-1] and raw_value[0] in ('"', "'"):
        raw_value = raw_value[1:-1]

    if not key:
        return None

    return key, raw_value


def load_env_file(
    path: str | Path = ".env",
    override: bool = False,
    expand: bool = True,
) -> Dict[str, str]:
    """
    Load a .env file and return a dict of key/value pairs.

    Args:
        path: Path to the .env file.
        override: If True, overwrite existing os.environ entries.
        expand: If True, expand variable references in values.

    Returns:
        Dictionary of loaded environment variables.
    """
    env_path = Path(path)
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")

    loaded: Dict[str, str] = {}

    with env_path.open(encoding="utf-8") as fh:
        for line in fh:
            result = _parse_line(line)
            if result is None:
                continue
            key, value = result
            if expand:
                value = _expand_value(value, {**os.environ, **loaded})
            loaded[key] = value

    for key, value in loaded.items():
        if override or key not in os.environ:
            os.environ[key] = value

    return loaded
