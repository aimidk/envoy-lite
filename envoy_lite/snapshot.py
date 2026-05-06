"""Snapshot utilities — capture and diff environment variable states."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class EnvSnapshot:
    """Immutable snapshot of key/value environment pairs."""

    data: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_os_environ(cls) -> "EnvSnapshot":
        """Capture the current process environment."""
        return cls(data=dict(os.environ))

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "EnvSnapshot":
        return cls(data=dict(d))

    def diff(self, other: "EnvSnapshot") -> "EnvDiff":
        """Compute diff from *self* (old) to *other* (new)."""
        added: Dict[str, str] = {}
        removed: Dict[str, str] = {}
        changed: List[Tuple[str, str, str]] = []

        all_keys = set(self.data) | set(other.data)
        for key in sorted(all_keys):
            in_old = key in self.data
            in_new = key in other.data
            if in_new and not in_old:
                added[key] = other.data[key]
            elif in_old and not in_new:
                removed[key] = self.data[key]
            elif self.data[key] != other.data[key]:
                changed.append((key, self.data[key], other.data[key]))

        return EnvDiff(added=added, removed=removed, changed=changed)

    def __len__(self) -> int:
        return len(self.data)


@dataclass
class EnvDiff:
    """Result of comparing two EnvSnapshots."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: List[Tuple[str, str, str]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.added and not self.removed and not self.changed

    def summary(self) -> str:
        lines: List[str] = []
        for k, v in sorted(self.added.items()):
            lines.append(f"+ {k}={v}")
        for k, v in sorted(self.removed.items()):
            lines.append(f"- {k}={v}")
        for k, old, new in self.changed:
            lines.append(f"~ {k}: {old!r} -> {new!r}")
        return "\n".join(lines) if lines else "(no changes)"
