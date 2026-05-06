"""Profile support: named sets of env files for different environments."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_PROFILES_DIR = "."
_PROFILE_FILE_PATTERN = ".env.{profile}"


class ProfileNotFoundError(FileNotFoundError):
    """Raised when a requested profile file does not exist."""


class ProfileManager:
    """Manages named environment profiles backed by .env.<name> files."""

    def __init__(
        self,
        profiles_dir: str = _DEFAULT_PROFILES_DIR,
        pattern: str = _PROFILE_FILE_PATTERN,
    ) -> None:
        self.profiles_dir = Path(profiles_dir)
        self.pattern = pattern
        self._registry: Dict[str, Path] = {}
        self._active: Optional[str] = None

    def _path_for(self, name: str) -> Path:
        filename = self.pattern.format(profile=name)
        return self.profiles_dir / filename

    def register(self, name: str, path: Optional[str] = None) -> None:
        """Register a profile, optionally with a custom path."""
        resolved = Path(path) if path else self._path_for(name)
        self._registry[name] = resolved

    def available(self) -> List[str]:
        """Return names of all profiles whose files exist on disk."""
        names: List[str] = []
        for name, path in self._registry.items():
            if path.exists():
                names.append(name)
        # Also discover unregistered files matching pattern
        if self.profiles_dir.is_dir():
            prefix = ".env."
            for entry in self.profiles_dir.iterdir():
                if entry.name.startswith(prefix):
                    candidate = entry.name[len(prefix):]
                    if candidate and candidate not in self._registry:
                        names.append(candidate)
        return sorted(set(names))

    def path_for(self, name: str) -> Path:
        """Return the file path for a profile, raising if not found."""
        path = self._registry.get(name) or self._path_for(name)
        if not path.exists():
            raise ProfileNotFoundError(
                f"Profile '{name}' not found at '{path}'"
            )
        return path

    def activate(self, name: str) -> Path:
        """Set the active profile and return its path."""
        path = self.path_for(name)
        self._active = name
        return path

    @property
    def active(self) -> Optional[str]:
        return self._active

    def active_path(self) -> Optional[Path]:
        if self._active is None:
            return None
        return self._registry.get(self._active) or self._path_for(self._active)
