"""CLI sub-command: validate an env file against a schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from envoy_lite.loader import load_env_file
from envoy_lite.schema import SchemaLoadError, load_schema_file
from envoy_lite.validator import ValidationError


def build_validate_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "validate",
        help="Validate an env file against a JSON/TOML schema.",
    )
    p.add_argument(
        "schema",
        metavar="SCHEMA",
        help="Path to .json or .toml schema file.",
    )
    p.add_argument(
        "-f",
        "--file",
        default=".env",
        metavar="FILE",
        help="Env file to validate (default: .env).",
    )
    p.add_argument(
        "--no-raise",
        action="store_true",
        help="Print errors instead of exiting with non-zero status.",
    )
    p.set_defaults(func=cmd_validate)
    return p


def cmd_validate(args: argparse.Namespace) -> int:
    """Run validation; return exit code."""
    env_path = Path(args.file)
    schema_path = Path(args.schema)

    try:
        env = load_env_file(env_path)
    except FileNotFoundError:
        print(f"error: env file not found: {env_path}", file=sys.stderr)
        return 1

    try:
        validator = load_schema_file(schema_path)
    except SchemaLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    errors: List[str] = validator.validate(env, raise_on_error=False)

    if not errors:
        print(f"✓ {env_path} is valid against {schema_path}")
        return 0

    print(f"✗ Validation failed for {env_path}:")
    for err in errors:
        print(f"  - {err}")

    return 0 if args.no_raise else 1


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envoy-validate")
    subs = parser.add_subparsers(dest="command")
    build_validate_parser(subs)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
