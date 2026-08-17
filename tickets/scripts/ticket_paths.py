#!/usr/bin/env python3
"""Shared ticket-path resolution.

Numeric tickets are grouped by thousand: ticket 17545 lives in 17000/17545/,
ticket 16575 in 16000/16575/. Alphanumeric ids have no thousand-bucket and sit
flat at the root (ROOT/<id>/). These helpers are the single source of truth for
turning a ticket id into a path, so every script agrees on the layout.
"""
from __future__ import annotations

import os
from pathlib import Path

# Root of the TICKETS workspace. Portable by default: honour $TICKETS_ROOT if
# set, otherwise fall back to ~/TICKETS. This is the single source of truth —
# every other script imports ROOT / the resolvers from here.
ROOT = Path(os.environ.get("TICKETS_ROOT", Path.home() / "TICKETS"))


def thousand_bucket(ticket_id: str) -> str:
    """Thousand-bucket folder name for a ticket id.

    Numeric ids group by thousand: 17545 -> "17000", 999 -> "0".
    Non-numeric / alphanumeric ids have no bucket and live flat at the root
    (return "", so ROOT / "" / id == ROOT / id).
    """
    if ticket_id.isdigit():
        return f"{int(ticket_id) // 1000 * 1000}"
    return ""


def ticket_dir_for_create(ticket_id: str) -> Path:
    """Where a NEW ticket should be created (always the canonical nested path)."""
    return ROOT / thousand_bucket(ticket_id) / ticket_id


def resolve_ticket_dir(ticket_id: str) -> Path:
    """Locate an EXISTING ticket folder, whichever layout it uses.

    Prefers the canonical nested path; falls back to a flat root folder (for
    alphanumeric ids that have no thousand-bucket). Returns the nested path
    even if nothing exists yet, so callers get a sensible default to error on.
    """
    nested = ROOT / thousand_bucket(ticket_id) / ticket_id
    if nested.exists():
        return nested
    flat = ROOT / ticket_id
    if flat.exists():
        return flat
    return nested


if __name__ == "__main__":
    # Tiny CLI so commands can resolve a ticket folder with one short call:
    #   python3 ticket_paths.py <ticket-number>   ->  prints the absolute path
    # (no --peek-style flags; resolution is the whole job here).
    import sys

    if len(sys.argv) != 2:
        print("usage: ticket_paths.py <ticket-number>", file=sys.stderr)
        raise SystemExit(2)
    print(resolve_ticket_dir(sys.argv[1]))
