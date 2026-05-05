"""Secret injection: resolve secret:// URIs from env values."""

import os
import re
from typing import Callable, Dict


SECRET_URI_RE = re.compile(r"^secret://([a-zA-Z0-9_-]+)/(.+)$")

# Registry of secret backends keyed by provider name
_BACKENDS: Dict[str, Callable[[str], str]] = {}


def register_backend(name: str, resolver: Callable[[str], str]) -> None:
    """Register a secret backend resolver function."""
    _BACKENDS[name] = resolver


def _file_backend(path: str) -> str:
    """Built-in file:// style backend — reads secret from a local file path."""
    from pathlib import Path

    secret_path = Path(path)
    if not secret_path.exists():
        raise FileNotFoundError(f"Secret file not found: {secret_path}")
    return secret_path.read_text(encoding="utf-8").strip()


register_backend("file", _file_backend)


def resolve_secret(value: str) -> str:
    """
    Resolve a secret:// URI to its actual value.

    URI format: secret://<provider>/<path-or-key>

    Returns the original value unchanged if it is not a secret URI.
    """
    match = SECRET_URI_RE.match(value)
    if not match:
        return value

    provider, key = match.group(1), match.group(2)
    resolver = _BACKENDS.get(provider)
    if resolver is None:
        raise ValueError(
            f"Unknown secret provider '{provider}'. "
            f"Registered providers: {list(_BACKENDS.keys())}"
        )
    return resolver(key)


def inject_secrets(env: Dict[str, str]) -> Dict[str, str]:
    """
    Iterate over an env dict and resolve any secret:// values in-place.

    Also updates os.environ with resolved values.

    Returns:
        Dict with secrets resolved.
    """
    resolved: Dict[str, str] = {}
    for key, value in env.items():
        resolved_value = resolve_secret(value)
        resolved[key] = resolved_value
        os.environ[key] = resolved_value
    return resolved
