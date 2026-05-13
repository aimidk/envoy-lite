"""CLI sub-commands for key rotation."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy_lite.loader import load_env_file
from envoy_lite.rotator import RotationError, list_versions, rollback, rotate_key


def build_rotate_parser(
    parser: Optional[argparse.ArgumentParser] = None,
) -> argparse.ArgumentParser:
    p = parser or argparse.ArgumentParser(
        prog="envoy-rotate",
        description="Rotate or roll back environment variable keys.",
    )
    p.add_argument("--file", "-f", default=".env", help="env file to read (default: .env)")
    sub = p.add_subparsers(dest="subcmd", required=True)

    rot = sub.add_parser("rotate", help="Rotate a key to a new value")
    rot.add_argument("key", help="Variable name to rotate")
    rot.add_argument("value", help="New value")
    rot.add_argument("--keep", type=int, default=3, help="Archived versions to keep (default: 3)")
    rot.add_argument("--dry-run", action="store_true", help="Print result without writing")

    rb = sub.add_parser("rollback", help="Roll back a key by N archived versions")
    rb.add_argument("key", help="Variable name to roll back")
    rb.add_argument("--steps", type=int, default=1, help="Steps to roll back (default: 1)")
    rb.add_argument("--dry-run", action="store_true", help="Print result without writing")

    ls = sub.add_parser("list", help="List archived versions of a key")
    ls.add_argument("key", help="Variable name")

    return p


def _print_env(env: dict) -> None:
    for k, v in sorted(env.items()):
        print(f"{k}={v}")


def cmd_rotate(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        updated = rotate_key(args.key, args.value, env, keep=args.keep)
    except RotationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        _print_env(updated)
        return 0

    with open(args.file, "w") as fh:
        for k, v in sorted(updated.items()):
            fh.write(f"{k}={v}\n")
    print(f"Rotated {args.key} (keep={args.keep})")
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        updated = rollback(args.key, env, steps=args.steps)
    except RotationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        _print_env(updated)
        return 0

    with open(args.file, "w") as fh:
        for k, v in sorted(updated.items()):
            fh.write(f"{k}={v}\n")
    print(f"Rolled back {args.key} by {args.steps} step(s)")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    versions = list_versions(args.key, env)
    if not versions:
        print(f"No archived versions found for '{args.key}'.")
        return 0
    for ver, val in versions:
        print(f"v{ver}: {val}")
    return 0


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    p = build_rotate_parser()
    args = p.parse_args(argv)
    dispatch = {"rotate": cmd_rotate, "rollback": cmd_rollback, "list": cmd_list}
    sys.exit(dispatch[args.subcmd](args))
