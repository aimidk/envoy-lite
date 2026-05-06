"""Command-line interface for envoy-lite."""

import argparse
import os
import subprocess
import sys

from envoy_lite import load


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-lite",
        description="Inject environment variables and secrets into a subprocess.",
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="env_file",
        default=".env",
        metavar="FILE",
        help="Path to the .env file (default: .env)",
    )
    parser.add_argument(
        "--override",
        action="store_true",
        default=False,
        help="Override existing environment variables (default: False)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print resolved variables without running a command",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run with the injected environment",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        resolved = load(path=args.env_file, override=args.override)
    except FileNotFoundError:
        print(f"envoy-lite: env file not found: {args.env_file}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"envoy-lite: error loading env file: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        for key, value in sorted(resolved.items()):
            print(f"{key}={value}")
        return 0

    command = [c for c in (args.command or []) if c != "--"]
    if not command:
        parser.print_help()
        return 1

    env = {**os.environ, **resolved}
    try:
        result = subprocess.run(command, env=env)  # noqa: S603
        return result.returncode
    except FileNotFoundError:
        print(f"envoy-lite: command not found: {command[0]}", file=sys.stderr)
        return 127


if __name__ == "__main__":
    sys.exit(main())
