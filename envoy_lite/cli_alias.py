"""CLI entry-point for the aliaser feature."""
from __future__ import annotations

import argparse
import sys

from envoy_lite.aliaser import AliasRegistry, expand_aliases
from envoy_lite.loader import load_env_file


def build_alias_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envoy-alias",
        description="Expand alias keys to their canonical names in an env file.",
    )
    parser = parent.add_parser("alias", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "--map",
        metavar="ALIAS=CANONICAL",
        action="append",
        default=[],
        help="Alias mapping, e.g. DB_HOST=DATABASE_HOST (repeatable)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite canonical key if it already exists",
    )
    return parser


def cmd_alias(args: argparse.Namespace) -> int:
    registry = AliasRegistry()
    for mapping in args.map:
        if "=" not in mapping:
            print(f"error: invalid mapping '{mapping}', expected ALIAS=CANONICAL", file=sys.stderr)
            return 2
        alias, canonical = mapping.split("=", 1)
        try:
            registry.register(canonical.strip(), alias.strip())
        except Exception as exc:  # noqa: BLE001
            print(f"error: {exc}", file=sys.stderr)
            return 2

    try:
        env = load_env_file(args.env_file)
    except FileNotFoundError:
        print(f"error: file not found: {args.env_file}", file=sys.stderr)
        return 1

    result = expand_aliases(env, registry, overwrite=args.overwrite)
    for key, value in sorted(result.items()):
        print(f"{key}={value}")
    return 0


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = build_alias_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_alias(args))


if __name__ == "__main__":  # pragma: no cover
    main()
