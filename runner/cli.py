#!/usr/bin/env python3
"""Small CLI for task-pack discovery and runner scaffolding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runner.adapters.registry import build_registry
from runner.task_pack import discover_task_packs


def cmd_list_task_packs(args: argparse.Namespace) -> int:
    """List discovered task packs as JSON."""

    task_packs = discover_task_packs(args.root)
    payload = [
        {
            "id": pack.task_id,
            "title": pack.title,
            "task_type": pack.task_type,
            "review_mode": pack.review_mode,
            "source_ref": pack.source_ref,
        }
        for pack in task_packs
    ]
    print(json.dumps(payload, indent=2))
    return 0


def cmd_list_adapters(_: argparse.Namespace) -> int:
    """List registered adapters."""

    registry = build_registry()
    payload = sorted(registry)
    print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the runner CLI parser."""

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    packs = subparsers.add_parser("list-task-packs")
    packs.add_argument(
        "--root",
        default=str(REPO_ROOT / "task-packs"),
    )
    packs.set_defaults(func=cmd_list_task_packs)

    adapters = subparsers.add_parser("list-adapters")
    adapters.set_defaults(func=cmd_list_adapters)

    return parser


def main() -> int:
    """Run the CLI."""

    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
