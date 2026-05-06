"""Redactor: mask sensitive variable values in output."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Optional

_DEFAULT_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth)"),
]

MASK = "***"


class Redactor:
    """Masks values whose key names match sensitive patterns."""

    def __init__(
        self,
        extra_patterns: Optional[Iterable[str]] = None,
        mask: str = MASK,
    ) -> None:
        self._patterns = list(_DEFAULT_PATTERNS)
        if extra_patterns:
            for p in extra_patterns:
                self._patterns.append(re.compile(p))
        self.mask = mask

    def is_sensitive(self, key: str) -> bool:
        """Return True if *key* matches any sensitive pattern."""
        return any(p.search(key) for p in self._patterns)

    def redact_value(self, key: str, value: str) -> str:
        """Return the masked string if *key* is sensitive, else *value*."""
        return self.mask if self.is_sensitive(key) else value

    def redact_dict(self, env: Dict[str, str]) -> Dict[str, str]:
        """Return a new dict with sensitive values replaced by the mask."""
        return {k: self.redact_value(k, v) for k, v in env.items()}

    def add_pattern(self, pattern: str) -> None:
        """Register an additional sensitive-key pattern at runtime."""
        self._patterns.append(re.compile(pattern))


_default_redactor = Redactor()


def redact(env: Dict[str, str], redactor: Optional[Redactor] = None) -> Dict[str, str]:
    """Convenience wrapper: redact *env* using *redactor* (or the default)."""
    r = redactor if redactor is not None else _default_redactor
    return r.redact_dict(env)
