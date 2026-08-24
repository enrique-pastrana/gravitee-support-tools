#!/usr/bin/env python3
"""Get / set / clear the "current ticket" pointer.

The current ticket is the one a command acts on when no number is passed. It
lives as a one-line file at `$TICKETS_ROOT/.current-ticket` holding the bare
number, so it survives across sessions and independently of the shell's cwd.
This helper is the single source of truth for reading and writing it — never
hand-edit the file.

Usage:
    current_ticket.py get           # print the number, or nothing if unset
    current_ticket.py set <number>  # point at <number> (creates/overwrites)
    current_ticket.py clear         # forget the current ticket

Exit codes:
    get   -> 0 if a current ticket is set (number on stdout), 1 if unset.
    set   -> 0 on success; also notes on stderr whether the folder exists yet
             (a heads-up, not an error — the pointer can lead an existing or a
             not-yet-created ticket).
    clear -> 0 whether or not there was anything to clear.
"""
from __future__ import annotations

import os
import sys

from ticket_paths import ROOT, resolve_ticket_dir

POINTER = ROOT / ".current-ticket"


def read_current() -> str | None:
    """The current ticket number, or None if unset/empty."""
    try:
        value = POINTER.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    return value or None


def write_current(number: str) -> None:
    """Point the current ticket at `number`, atomically."""
    ROOT.mkdir(parents=True, exist_ok=True)
    tmp = POINTER.with_suffix(".current-ticket.tmp")
    tmp.write_text(number + "\n", encoding="utf-8")
    os.replace(tmp, POINTER)


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {"get", "set", "clear"}:
        print("usage: current_ticket.py get|set <number>|clear", file=sys.stderr)
        return 2
    action = sys.argv[1]

    if action == "get":
        current = read_current()
        if current is None:
            print("no current ticket set", file=sys.stderr)
            return 1
        print(current)
        return 0

    if action == "set":
        if len(sys.argv) != 3 or not sys.argv[2].strip():
            print("usage: current_ticket.py set <number>", file=sys.stderr)
            return 2
        number = sys.argv[2].strip()
        if number.split() != [number]:
            print(f"error: {number!r} is not a bare ticket number", file=sys.stderr)
            return 2
        write_current(number)
        exists = resolve_ticket_dir(number).exists()
        print(f"current ticket -> {number}")
        if not exists:
            print(f"note: {number} has no folder yet (create it with /new-ticket)",
                  file=sys.stderr)
        return 0

    # clear
    try:
        POINTER.unlink()
    except FileNotFoundError:
        pass
    print("current ticket cleared")
    return 0


if __name__ == "__main__":
    sys.exit(main())
