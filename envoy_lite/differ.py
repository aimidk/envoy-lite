"""Diff two env files or dicts and report added, removed, and changed keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_lite.loader import load_env_file


@dataclass
class DiffResult:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines: List[str] = []
        for k, v in sorted(self.added.items()):
            lines.append(f"+ {k}={v}")
        for k, v in sorted(self.removed.items()):
            lines.append(f"- {k}={v}")
        for k, (old, new) in sorted(self.changed.items()):
            lines.append(f"~ {k}: {old!r} -> {new!r}")
        return "\n".join(lines) if lines else "(no changes)"


def diff_dicts(base: Dict[str, str], other: Dict[str, str]) -> DiffResult:
    """Compare two env dicts and return a DiffResult."""
    result = DiffResult()
    all_keys = set(base) | set(other)
    for key in all_keys:
        in_base = key in base
        in_other = key in other
        if in_base and not in_other:
            result.removed[key] = base[key]
        elif in_other and not in_base:
            result.added[key] = other[key]
        elif base[key] != other[key]:
            result.changed[key] = (base[key], other[key])
    return result


def diff_files(base_path: str, other_path: str, override: bool = False) -> DiffResult:
    """Load two env files and diff them."""
    base = load_env_file(base_path, override=override)
    other = load_env_file(other_path, override=override)
    return diff_dicts(base, other)
