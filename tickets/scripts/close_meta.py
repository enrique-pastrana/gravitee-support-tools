#!/usr/bin/env python3
"""Stamp a ticket's metadata.json as closed (atomic, computed, safe).

Usage:
    close_meta.py <ticket-number> [--status resolved|closed]
                  [--resolved-at ISO8601] [--kb-candidate] [--force]

The one deterministic write for closing a ticket, so the model never hand-edits
JSON nor hand-computes the elapsed time. In a single atomic write it:

  - sets status to the terminal value (default "resolved"; "closed" when the
    Zendesk ticket is archived-closed rather than solved). The caller maps the
    Zendesk status -> local status; this script just writes what it's told.
  - sets resolved_at (default: now, seconds precision; override for testing or
    to mirror the Zendesk solved time)
  - computes resolution_time_hours = whole hours between opened_at and
    resolved_at (rounded, never negative); left null if opened_at is
    missing/unparseable, with a warning
  - refreshes updated_at to resolved_at
  - with --kb-candidate, sets kb_candidate = true; without the flag the field is
    left untouched, so a previous "true" is never silently downgraded

Refuses if metadata.json is missing/invalid, or if status is already terminal
(resolved/closed) unless --force. Re-render the timeline header afterwards with
render_header.py so the header, /status and the metadata never drift.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

from ticket_paths import resolve_ticket_dir

TERMINAL_STATUSES = {"resolved", "closed"}


def parse_dt(raw: str) -> datetime | None:
    """Parse an ISO 8601 timestamp or a bare YYYY-MM-DD date, tz dropped.

    Returns a naive datetime (both sides of the diff are naive, so a small tz
    offset is irrelevant at hour granularity) or None if unparseable.
    """
    raw = raw.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            return None
    return dt.replace(tzinfo=None)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ticket")
    p.add_argument("--status", choices=sorted(TERMINAL_STATUSES),
                   default="resolved")
    p.add_argument("--resolved-at", default=None,
                   help="ISO 8601; defaults to now (seconds precision).")
    p.add_argument("--kb-candidate", action="store_true",
                   help="Mark kb_candidate=true (never downgrades a prior true).")
    p.add_argument("--force", action="store_true",
                   help="Close even if already resolved/closed.")
    args = p.parse_args()

    resolved_at = args.resolved_at or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    meta_path = resolve_ticket_dir(args.ticket) / "metadata.json"
    if not meta_path.is_file():
        print(f"error: {meta_path} not found", file=sys.stderr)
        return 1
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: {meta_path} not valid JSON: {exc}", file=sys.stderr)
        return 1

    if meta.get("status") in TERMINAL_STATUSES and not args.force:
        print(f"{args.ticket}: already {meta['status']}, skipped "
              "(pass --force to re-close)")
        return 0

    # Elapsed hours between opened_at and resolved_at, best-effort.
    hours: int | None = None
    opened_raw = meta.get("opened_at")
    resolved_dt = parse_dt(resolved_at)
    opened_dt = parse_dt(opened_raw) if opened_raw else None
    if opened_dt is None:
        print(f"warning: opened_at ({opened_raw!r}) missing/unparseable; "
              "leaving resolution_time_hours null", file=sys.stderr)
    elif resolved_dt is None:
        print(f"warning: --resolved-at ({resolved_at!r}) unparseable; "
              "leaving resolution_time_hours null", file=sys.stderr)
    else:
        delta_hours = round((resolved_dt - opened_dt).total_seconds() / 3600)
        if delta_hours < 0:
            print(f"warning: resolved_at is before opened_at; clamping "
                  "resolution_time_hours to 0", file=sys.stderr)
            delta_hours = 0
        hours = delta_hours

    meta["status"] = args.status
    meta["resolved_at"] = resolved_at
    meta["resolution_time_hours"] = hours
    meta["updated_at"] = resolved_at
    if args.kb_candidate:
        meta["kb_candidate"] = True

    rendered = json.dumps(meta, indent=2, ensure_ascii=False) + "\n"
    json.loads(rendered)  # sanity check before committing
    tmp = meta_path.with_suffix(".json.tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, meta_path)

    hours_str = "null" if hours is None else f"{hours}h"
    print(f"{args.ticket}: {args.status} "
          f"(resolved_at={resolved_at}, resolution_time_hours={hours_str})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
