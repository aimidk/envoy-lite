"""Audit log — record env load events and diffs for traceability."""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional

from envoy_lite.snapshot import EnvDiff


@dataclass
class AuditEntry:
    timestamp: str
    filepath: str
    event: str  # "load" | "reload" | "error"
    keys_loaded: int = 0
    diff_summary: Optional[str] = None
    error: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class AuditLog:
    """In-memory audit log for env load events."""

    def __init__(self, max_entries: int = 200):
        self._entries: List[AuditEntry] = []
        self.max_entries = max_entries

    def _now(self) -> str:
        return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

    def record_load(self, filepath: str, keys_loaded: int) -> AuditEntry:
        entry = AuditEntry(
            timestamp=self._now(),
            filepath=filepath,
            event="load",
            keys_loaded=keys_loaded,
        )
        self._append(entry)
        return entry

    def record_reload(self, filepath: str, keys_loaded: int, diff: EnvDiff) -> AuditEntry:
        entry = AuditEntry(
            timestamp=self._now(),
            filepath=filepath,
            event="reload",
            keys_loaded=keys_loaded,
            diff_summary=diff.summary(),
        )
        self._append(entry)
        return entry

    def record_error(self, filepath: str, error: str) -> AuditEntry:
        entry = AuditEntry(
            timestamp=self._now(),
            filepath=filepath,
            event="error",
            error=error,
        )
        self._append(entry)
        return entry

    def _append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]

    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

    def dump_json(self) -> str:
        """Return all entries as a JSON array string."""
        return json.dumps([asdict(e) for e in self._entries], indent=2)


# Module-level default audit log instance
default_audit_log = AuditLog()
