#!/usr/bin/env python3
"""Bump next_entry and refresh updated_at in a ticket's metadata.json.

Usage:
    bump_entry.py <ticket-number> [--peek]

Without --peek: bumps `next_entry` by 1, refreshes `updated_at` to now (ISO
8601 with seconds), prints the entry number just consumed (the value BEFORE
the bump, zero-padded to 3 digits).

With --peek: prints the current `next_entry` without modifying anything.

Refuses to act if metadata.json is missing or invalid.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from ticket_paths import resolve_ticket_dir


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ticket")
    p.add_argument("--peek", action="store_true")
    args = p.parse_args()

    meta_path = resolve_ticket_dir(args.ticket) / "metadata.json"
    if not meta_path.is_file():
        print(f"error: {meta_path} not found", file=sys.stderr)
        return 1

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: {meta_path} not valid JSON: {exc}", file=sys.stderr)
        return 1

    current = int(meta.get("next_entry", 1))

    if args.peek:
        print(f"{current:03d}")
        return 0

    meta["next_entry"] = current + 1
    meta["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"{current:03d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
