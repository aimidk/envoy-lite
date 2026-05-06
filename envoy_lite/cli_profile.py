"""CLI sub-commands for profile management."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy_lite.profile import ProfileManager, ProfileNotFoundError
from envoy_lite.loader import load_env_file


def _make_manager(args: argparse.Namespace) -> ProfileManager:
    return ProfileManager(profiles_dir=getattr(args, "profiles_dir", "."))


def cmd_list(args: argparse.Namespace) -> int:
    mgr = _make_manager(args)
    profiles = mgr.available()
    if not profiles:
        print("No profiles found.", file=sys.stderr)
        return 1
    for name in profiles:
        print(name)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    mgr = _make_manager(args)
    try:
        path = mgr.path_for(args.name)
    except ProfileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    env = load_env_file(str(path))
    for key in sorted(env):
        print(f"{key}={env[key]}")
    return 0


def cmd_activate(args: argparse.Namespace) -> int:
    mgr = _make_manager(args)
    try:
        path = mgr.activate(args.name)
    except ProfileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Activated profile '{args.name}' -> {path}")
    return 0


def build_profile_parser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    profile_p = subparsers.add_parser("profile", help="Manage env profiles")
    profile_p.add_argument(
        "--profiles-dir", default=".", metavar="DIR",
        help="Directory containing .env.<name> files (default: .)",
    )
    sub = profile_p.add_subparsers(dest="profile_cmd", required=True)

    sub.add_parser("list", help="List available profiles")

    show_p = sub.add_parser("show", help="Print variables for a profile")
    show_p.add_argument("name", help="Profile name")

    activate_p = sub.add_parser("activate", help="Activate a profile")
    activate_p.add_argument("name", help="Profile name")


def dispatch_profile(args: argparse.Namespace) -> int:
    dispatch = {
        "list": cmd_list,
        "show": cmd_show,
        "activate": cmd_activate,
    }
    handler = dispatch.get(args.profile_cmd)
    if handler is None:
        print(f"Unknown profile command: {args.profile_cmd}", file=sys.stderr)
        return 2
    return handler(args)
