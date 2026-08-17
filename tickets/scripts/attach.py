#!/usr/bin/env python3
"""Move a file into a ticket folder, prefixing it with the entry number.

Usage:
    attach.py <ticket-number> <entry-number> <source-path> [--kind KIND] [--date YYYY-MM-DD]

Where KIND is one of: received, result.
  - received: file received from the customer (default). Routed to
              received/<date>/NNN_<basename>.
  - result:   evidence produced during a local reproduction. Routed to
              reproduction/results/NNN_<basename>.

By default <date> is today's date (local). Override with --date for files
that arrived on a different day.

Filename is normalised: lowercased, spaces and special chars → `_`.
Prints the destination path on success.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from ticket_paths import resolve_ticket_dir

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalise(name: str) -> str:
    stem = Path(name).stem
    ext = Path(name).suffix.lower()
    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9._-]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    if not stem:
        stem = "file"
    return f"{stem}{ext}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ticket")
    p.add_argument("entry", type=int)
    p.add_argument("source")
    p.add_argument("--kind", choices=["received", "result"], default="received")
    p.add_argument("--date", default=None,
                   help="Date folder under received/ (YYYY-MM-DD). Defaults to today.")
    args = p.parse_args()

    src = Path(args.source).expanduser()
    if not src.is_file():
        print(f"error: source not found: {src}", file=sys.stderr)
        return 1

    ticket_dir = resolve_ticket_dir(args.ticket)
    if not ticket_dir.is_dir():
        print(f"error: ticket folder not found: {ticket_dir}", file=sys.stderr)
        return 1

    if args.kind == "result":
        dest_dir = ticket_dir / "reproduction" / "results"
    else:
        date_str = args.date or datetime.now().strftime("%Y-%m-%d")
        if not DATE_RE.match(date_str):
            print(f"error: --date must be YYYY-MM-DD, got: {date_str}", file=sys.stderr)
            return 2
        dest_dir = ticket_dir / "received" / date_str

    dest_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"{args.entry:03d}_"
    dest_name = prefix + normalise(src.name)
    dest = dest_dir / dest_name

    if dest.exists():
        print(f"error: destination already exists: {dest}", file=sys.stderr)
        return 1

    shutil.move(str(src), str(dest))
    print(str(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
