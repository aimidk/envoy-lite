"""Key aliasing — map one or more alias names to a canonical env key."""
from __future__ import annotations

from typing import Dict, List, Optional


class AliasError(Exception):
    """Raised when an alias operation fails."""


class AliasRegistry:
    """Maintains a mapping from alias names to canonical key names."""

    def __init__(self) -> None:
        # alias -> canonical
        self._map: Dict[str, str] = {}

    def register(self, canonical: str, *aliases: str) -> None:
        """Register one or more *aliases* that point to *canonical*."""
        if not canonical:
            raise AliasError("canonical key must not be empty")
        for alias in aliases:
            if not alias:
                raise AliasError("alias must not be empty")
            if alias == canonical:
                raise AliasError(f"alias '{alias}' must differ from canonical")
            self._map[alias] = canonical

    def resolve(self, key: str) -> str:
        """Return the canonical key for *key*, or *key* itself if not aliased."""
        return self._map.get(key, key)

    def aliases_for(self, canonical: str) -> List[str]:
        """Return all aliases registered for *canonical*."""
        return [a for a, c in self._map.items() if c == canonical]

    def all_aliases(self) -> Dict[str, str]:
        """Return a copy of the full alias -> canonical mapping."""
        return dict(self._map)


def expand_aliases(
    env: Dict[str, str],
    registry: AliasRegistry,
    *,
    overwrite: bool = False,
    missing_ok: bool = True,
) -> Dict[str, str]:
    """Return a new dict where each alias key is replaced by its canonical name.

    Parameters
    ----------
    env:        Source environment dictionary.
    registry:   :class:`AliasRegistry` providing alias->canonical mappings.
    overwrite:  When *True*, a canonical key already present in *env* is
                overwritten by the aliased value.  Defaults to *False*.
    missing_ok: When *False*, raise :class:`AliasError` if an alias key is
                found in *env* but its canonical key is absent and
                *overwrite* is *False*.  Has no effect when *overwrite* is
                *True*.  Defaults to *True*.
    """
    result = dict(env)
    for alias, canonical in registry.all_aliases().items():
        if alias not in result:
            continue
        value = result.pop(alias)
        if canonical in result and not overwrite:
            if not missing_ok:
                raise AliasError(
                    f"canonical key '{canonical}' already exists; "
                    f"set overwrite=True to replace it"
                )
            # keep existing canonical value, discard alias value
        else:
            result[canonical] = value
    return result
