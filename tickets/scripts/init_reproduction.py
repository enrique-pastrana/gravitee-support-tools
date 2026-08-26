#!/usr/bin/env python3
"""Initialise a reproduction/ folder inside an existing ticket.

Usage:
    init_reproduction.py <ticket-number>

Creates:
    <number>/reproduction/
        steps.md
        environment.md
        configs/
        results/

Refuses to overwrite an existing reproduction folder.
"""
from __future__ import annotations

import getpass
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from ticket_paths import resolve_ticket_dir

# Templates ship with the scripts (under _system/), not with the ticket data,
# so resolve them relative to this file — works even if TICKETS_ROOT is elsewhere.
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def render(text: str, ticket_id: str, meta: dict, today: str) -> str:
    return (
        text.replace("{{ticket_id}}", ticket_id)
        .replace("{{date}}", today)
        .replace("{{subject}}", str(meta.get("subject", "TBD")))
        .replace("{{customer}}", str(meta.get("customer", "TBD")))
        .replace("{{product}}", str(meta.get("product", "TBD")))
        .replace("{{version}}", str(meta.get("version", "TBD")))
        .replace("{{priority}}", str(meta.get("priority", "TBD")))
        .replace("{{zendesk_url}}", str(meta.get("zendesk_url", "TBD")))
        .replace("{{engineer}}", engineer_name())
    )


def engineer_name() -> str:
    """Name for the repro's Engineer field: $TICKETS_ENGINEER, else OS login."""
    name = os.environ.get("TICKETS_ENGINEER")
    if name:
        return name
    try:
        return getpass.getuser()
    except Exception:
        return "TBD"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <ticket-number>", file=sys.stderr)
        return 2

    ticket_id = argv[1].strip()
    ticket_dir = resolve_ticket_dir(ticket_id)
    if not ticket_dir.is_dir():
        print(f"error: ticket folder {ticket_dir} does not exist",
              file=sys.stderr)
        return 1

    repro_dir = ticket_dir / "reproduction"
    if repro_dir.exists():
        print(f"error: {repro_dir} already exists; refusing to overwrite",
              file=sys.stderr)
        return 1

    meta_path = ticket_dir / "metadata.json"
    meta = {}
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"warning: {meta_path} is not valid JSON; using empty meta",
                  file=sys.stderr)

    today_iso = datetime.now().strftime("%Y-%m-%d")
    repro_dir.mkdir()
    (repro_dir / "configs").mkdir()
    (repro_dir / "results").mkdir()

    for name in ("reproduction-steps.md", "reproduction-environment.md"):
        target_name = name.replace("reproduction-", "")
        tpl = (TEMPLATES / name).read_text(encoding="utf-8")
        (repro_dir / target_name).write_text(
            render(tpl, ticket_id, meta, today_iso), encoding="utf-8"
        )

    print(str(repro_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
