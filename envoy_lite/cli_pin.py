"""CLI sub-command: pin / load-pin / diff-pin."""

from __future__ import annotations

import argparse
import sys

from envoy_lite.loader import load_env_file
from envoy_lite.pinner import PinError, diff_pin, load_pin, pin_env


def build_pin_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Manage environment variable pin (lock) files.")
    if parent is not None:
        parser = parent.add_parser("pin", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envoy-pin", **kwargs)

    sub = parser.add_subparsers(dest="pin_cmd", required=True)

    # envoy pin save
    save_p = sub.add_parser("save", help="Pin current .env values to a lockfile.")
    save_p.add_argument("--env-file", default=".env", metavar="FILE")
    save_p.add_argument("--pin-file", default=".env.lock", metavar="LOCKFILE")

    # envoy pin show
    show_p = sub.add_parser("show", help="Print contents of a pin file.")
    show_p.add_argument("--pin-file", default=".env.lock", metavar="LOCKFILE")

    # envoy pin diff
    diff_p = sub.add_parser("diff", help="Diff current .env against a pin file.")
    diff_p.add_argument("--env-file", default=".env", metavar="FILE")
    diff_p.add_argument("--pin-file", default=".env.lock", metavar="LOCKFILE")

    return parser


def cmd_pin(args: argparse.Namespace) -> int:
    try:
        if args.pin_cmd == "save":
            env = load_env_file(args.env_file)
            pin_env(env, args.pin_file)
            print(f"Pinned {len(env)} variable(s) to '{args.pin_file}'.")

        elif args.pin_cmd == "show":
            pinned = load_pin(args.pin_file)
            for key in sorted(pinned):
                print(f"{key}={pinned[key]}")

        elif args.pin_cmd == "diff":
            current = load_env_file(args.env_file)
            pinned = load_pin(args.pin_file)
            changes = diff_pin(current, pinned)
            if not changes:
                print("No differences.")
                return 0
            for key, vals in changes.items():
                c = vals["current"]
                p = vals["pinned"]
                if c is None:
                    print(f"- {key} (removed; pinned={p!r})")
                elif p is None:
                    print(f"+ {key}={c!r} (new; not in pin)")
                else:
                    print(f"~ {key}: current={c!r}  pinned={p!r}")
            return 1  # non-zero signals drift

    except PinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def main() -> None:  # pragma: no cover
    parser = build_pin_parser()
    args = parser.parse_args()
    sys.exit(cmd_pin(args))
