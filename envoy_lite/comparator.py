"""Compare two env dicts and produce a structured comparison report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class CompareError(Exception):
    """Raised when comparison cannot be performed."""


@dataclass
class CompareEntry:
    key: str
    left: Optional[str]
    right: Optional[str]
    status: str  # 'added' | 'removed' | 'changed' | 'unchanged'

    def is_different(self) -> bool:
        return self.status != "unchanged"


@dataclass
class CompareReport:
    entries: List[CompareEntry] = field(default_factory=list)

    @property
    def added(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.status == "added"]

    @property
    def removed(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.status == "removed"]

    @property
    def changed(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.status == "changed"]

    @property
    def unchanged(self) -> List[CompareEntry]:
        return [e for e in self.entries if e.status == "unchanged"]

    def has_differences(self) -> bool:
        return any(e.is_different() for e in self.entries)

    def summary(self) -> str:
        return (
            f"+{len(self.added)} added, "
            f"-{len(self.removed)} removed, "
            f"~{len(self.changed)} changed, "
            f"={len(self.unchanged)} unchanged"
        )


def compare_dicts(
    left: Dict[str, str],
    right: Dict[str, str],
    *,
    include_unchanged: bool = True,
) -> CompareReport:
    """Compare two env dicts and return a CompareReport."""
    all_keys = sorted(set(left) | set(right))
    entries: List[CompareEntry] = []

    for key in all_keys:
        in_left = key in left
        in_right = key in right

        if in_left and not in_right:
            entries.append(CompareEntry(key, left[key], None, "removed"))
        elif in_right and not in_left:
            entries.append(CompareEntry(key, None, right[key], "added"))
        elif left[key] != right[key]:
            entries.append(CompareEntry(key, left[key], right[key], "changed"))
        elif include_unchanged:
            entries.append(CompareEntry(key, left[key], right[key], "unchanged"))

    return CompareReport(entries=entries)
