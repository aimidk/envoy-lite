"""Value transformation pipeline for environment variables."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional


class TransformError(Exception):
    """Raised when a transformation fails."""


# Registry of named transformers
_TRANSFORMERS: Dict[str, Callable[[str], str]] = {}


def register_transformer(name: str, fn: Callable[[str], str]) -> None:
    """Register a named transformer function."""
    _TRANSFORMERS[name] = fn


def get_transformer(name: str) -> Callable[[str], str]:
    """Return a registered transformer or raise TransformError."""
    if name not in _TRANSFORMERS:
        raise TransformError(f"Unknown transformer: {name!r}")
    return _TRANSFORMERS[name]


def apply_transformer(name: str, value: str) -> str:
    """Apply a single named transformer to *value*."""
    return get_transformer(name)(value)


def apply_pipeline(names: List[str], value: str) -> str:
    """Apply a sequence of transformers left-to-right."""
    result = value
    for name in names:
        try:
            result = get_transformer(name)(result)
        except TransformError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise TransformError(
                f"Transformer {name!r} raised an error: {exc}"
            ) from exc
    return result


def transform_dict(
    env: Dict[str, str],
    pipeline: List[str],
    keys: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Apply *pipeline* to selected keys (or all keys if *keys* is None)."""
    target_keys = set(keys) if keys is not None else set(env)
    return {
        k: (apply_pipeline(pipeline, v) if k in target_keys else v)
        for k, v in env.items()
    }


# ---------- built-in transformers ----------

register_transformer("upper", str.upper)
register_transformer("lower", str.lower)
register_transformer("strip", str.strip)
register_transformer("strip_quotes", lambda v: v.strip("'\"" ))
register_transformer("base64_encode", lambda v: __import__("base64").b64encode(v.encode()).decode())
register_transformer("base64_decode", lambda v: __import__("base64").b64decode(v.encode()).decode())
