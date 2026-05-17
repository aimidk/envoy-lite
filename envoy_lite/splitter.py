"""Split an env dict into multiple files based on a predicate or prefix list."""
from __future__ import annotations

import json
import os
from typing import Callable, Dict, List, Optional, Tuple


class SplitError(Exception):
    """Raised when a split operation cannot be completed."""


def split_by_prefix(
    env: Dict[str, str],
    prefixes: List[str],
    *,
    strip_prefix: bool = False,
    include_unmatched: bool = True,
) -> Dict[str, Dict[str, str]]:
    """Partition *env* into buckets keyed by prefix.

    Keys that match no prefix land in the ``"__unmatched__"`` bucket when
    *include_unmatched* is ``True``; otherwise they are silently dropped.

    Args:
        env: Source environment mapping.
        prefixes: Ordered list of prefix strings to match against.
        strip_prefix: When ``True`` the prefix is removed from each key in its
            bucket.
        include_unmatched: Collect keys that match no prefix under the special
            ``"__unmatched__"`` key.

    Returns:
        A dict mapping each prefix (and optionally ``"__unmatched__"``) to its
        subset of *env*.
    """
    if not prefixes:
        raise SplitError("prefixes list must not be empty")

    buckets: Dict[str, Dict[str, str]] = {p: {} for p in prefixes}
    unmatched: Dict[str, str] = {}

    for key, value in env.items():
        matched = False
        for prefix in prefixes:
            if key.startswith(prefix):
                bucket_key = key[len(prefix):] if strip_prefix else key
                buckets[prefix][bucket_key] = value
                matched = True
                break
        if not matched and include_unmatched:
            unmatched[key] = value

    if include_unmatched:
        buckets["__unmatched__"] = unmatched

    return buckets


def split_by_predicate(
    env: Dict[str, str],
    predicate: Callable[[str, str], str],
) -> Dict[str, Dict[str, str]]:
    """Partition *env* into buckets determined by *predicate*.

    Args:
        env: Source environment mapping.
        predicate: Callable ``(key, value) -> bucket_name``.  Keys that map to
            the same bucket name are grouped together.

    Returns:
        A dict mapping bucket names to their subset of *env*.
    """
    buckets: Dict[str, Dict[str, str]] = {}
    for key, value in env.items():
        bucket = predicate(key, value)
        buckets.setdefault(bucket, {})[key] = value
    return buckets


def write_splits(
    buckets: Dict[str, Dict[str, str]],
    output_dir: str,
    *,
    fmt: str = "dotenv",
) -> List[str]:
    """Write each bucket to a file inside *output_dir*.

    Args:
        buckets: Mapping of bucket name -> env dict (as returned by the split
            helpers).
        output_dir: Directory to write files into (created if absent).
        fmt: ``"dotenv"`` or ``"json"``.

    Returns:
        List of file paths that were written.
    """
    if fmt not in ("dotenv", "json"):
        raise SplitError(f"unsupported format: {fmt!r}; choose 'dotenv' or 'json'")

    os.makedirs(output_dir, exist_ok=True)
    written: List[str] = []

    for name, mapping in buckets.items():
        safe_name = name.strip("_").replace("__", "_") or "unmatched"
        ext = ".env" if fmt == "dotenv" else ".json"
        path = os.path.join(output_dir, safe_name + ext)

        with open(path, "w", encoding="utf-8") as fh:
            if fmt == "json":
                json.dump(mapping, fh, indent=2, sort_keys=True)
                fh.write("\n")
            else:
                for k, v in sorted(mapping.items()):
                    fh.write(f"{k}={v}\n")

        written.append(path)

    return written
