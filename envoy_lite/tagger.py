"""Tag environment variables with arbitrary metadata labels."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional


class TagError(Exception):
    """Raised when a tagging operation fails."""


class TagRegistry:
    """Associates string tags with environment variable keys."""

    def __init__(self) -> None:
        # key -> set of tags
        self._tags: Dict[str, set] = {}

    def tag(self, key: str, *tags: str) -> None:
        """Add one or more tags to *key*."""
        if not key:
            raise TagError("key must be a non-empty string")
        if not tags:
            raise TagError("at least one tag must be provided")
        self._tags.setdefault(key, set()).update(tags)

    def untag(self, key: str, *tags: str) -> None:
        """Remove tags from *key*. Unknown tags are silently ignored."""
        if key in self._tags:
            self._tags[key].difference_update(tags)
            if not self._tags[key]:
                del self._tags[key]

    def tags_for(self, key: str) -> List[str]:
        """Return sorted list of tags for *key*."""
        return sorted(self._tags.get(key, set()))

    def keys_for_tag(self, tag: str) -> List[str]:
        """Return sorted list of keys that carry *tag*."""
        return sorted(k for k, ts in self._tags.items() if tag in ts)

    def filter_dict(
        self,
        env: Dict[str, str],
        tags: Iterable[str],
        match_all: bool = False,
    ) -> Dict[str, str]:
        """Return subset of *env* whose keys match the given *tags*.

        Args:
            env: Source mapping of env vars.
            tags: Tags to match against.
            match_all: If True, keys must carry ALL supplied tags;
                       if False (default), ANY tag is sufficient.
        """
        tag_set = set(tags)
        if not tag_set:
            raise TagError("at least one tag must be supplied to filter_dict")
        result: Dict[str, str] = {}
        for key, value in env.items():
            key_tags = self._tags.get(key, set())
            if match_all:
                if tag_set <= key_tags:
                    result[key] = value
            else:
                if tag_set & key_tags:
                    result[key] = value
        return result

    def all_tags(self) -> List[str]:
        """Return sorted list of every distinct tag currently registered."""
        seen: set = set()
        for ts in self._tags.values():
            seen.update(ts)
        return sorted(seen)

    def as_dict(self) -> Dict[str, List[str]]:
        """Serialisable snapshot: key -> sorted list of tags."""
        return {k: sorted(v) for k, v in sorted(self._tags.items())}
