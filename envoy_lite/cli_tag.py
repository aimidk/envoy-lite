"""CLI sub-commands for the tagger module."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envoy_lite.tagger import TagRegistry


def _make_registry(tagged_pairs: List[str]) -> TagRegistry:
    """Build a TagRegistry from ``KEY:tag1,tag2`` strings."""
    reg = TagRegistry()
    for item in tagged_pairs:
        if ":" not in item:
            sys.exit(f"Invalid tag spec (expected KEY:tag1,tag2): {item!r}")
        key, _, raw_tags = item.partition(":")
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        if not tags:
            sys.exit(f"No tags found in spec: {item!r}")
        reg.tag(key, *tags)
    return reg


def build_tag_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(description="Tag and filter environment variables by metadata labels.")
    if parent is not None:
        p = parent.add_parser("tag", **kwargs)
    else:
        p = argparse.ArgumentParser(prog="envoy-tag", **kwargs)

    sub = p.add_subparsers(dest="tag_cmd", required=True)

    # -- filter sub-command --
    filt = sub.add_parser("filter", help="Print env vars that match given tags.")
    filt.add_argument("--file", "-f", default=".env", help="Env file to load.")
    filt.add_argument("--tag", "-t", dest="tags", action="append", default=[], metavar="TAG")
    filt.add_argument("--spec", "-s", dest="specs", action="append", default=[], metavar="KEY:tag1,tag2")
    filt.add_argument("--all", dest="match_all", action="store_true", default=False)
    filt.add_argument("--json", dest="as_json", action="store_true", default=False)

    # -- list sub-command --
    lst = sub.add_parser("list", help="List all registered tags for specs.")
    lst.add_argument("--spec", "-s", dest="specs", action="append", default=[], metavar="KEY:tag1,tag2")
    lst.add_argument("--json", dest="as_json", action="store_true", default=False)

    return p


def cmd_tag(args: argparse.Namespace) -> int:
    from envoy_lite.loader import load_env_file

    if args.tag_cmd == "filter":
        env = load_env_file(args.file)
        reg = _make_registry(args.specs)
        if not args.tags:
            sys.exit("At least one --tag is required for filter.")
        filtered = reg.filter_dict(env, args.tags, match_all=args.match_all)
        if args.as_json:
            print(json.dumps(filtered, indent=2))
        else:
            for k, v in sorted(filtered.items()):
                print(f"{k}={v}")
        return 0

    if args.tag_cmd == "list":
        reg = _make_registry(args.specs)
        data = reg.as_dict()
        if args.as_json:
            print(json.dumps(data, indent=2))
        else:
            for key, tags in data.items():
                print(f"{key}: {', '.join(tags)}")
        return 0

    return 1


def main() -> None:  # pragma: no cover
    p = build_tag_parser()
    args = p.parse_args()
    sys.exit(cmd_tag(args))


if __name__ == "__main__":  # pragma: no cover
    main()
