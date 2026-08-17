#!/usr/bin/env python3
"""Initialise a new ticket folder under the TICKETS workspace ($TICKETS_ROOT, default ~/TICKETS).

Usage:
    init_ticket.py <number>

Creates:
    <thousand>/<number>/
        timeline.md     (from the plugin's templates/timeline.md)
        metadata.json   (from the plugin's templates/metadata.json)

Tickets are grouped by thousand: ticket 17545 lives in 17000/17545/,
ticket 16575 in 16000/16575/. The thousand folder is created on demand.
Alphanumeric / non-numeric ids fall back to the flat layout (ROOT/<id>/).

received/<date>/ folders are created on demand by attach.py the first time
a file arrives that day.

Refuses to overwrite an existing ticket folder.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from ticket_paths import ticket_dir_for_create

# Templates ship inside the plugin (scripts/ and templates/ are siblings under
# the plugin root), not with the ticket data — so resolve them relative to this
# file. Works wherever the user's TICKETS_ROOT lives.
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def render(text: str, ticket_id: str, today: str) -> str:
    return (
        text.replace("{{ticket_id}}", ticket_id)
        .replace("{{opened_at}}", today)
        .replace("{{date}}", today)
        .replace("{{subject}}", "TBD")
        .replace("{{customer}}", "TBD")
        .replace("{{product}}", "TBD")
        .replace("{{version}}", "TBD")
        .replace("{{priority}}", "TBD")
        .replace("{{zendesk_url}}", "TBD")
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <ticket-number>", file=sys.stderr)
        return 2

    ticket_id = argv[1].strip()
    if not ticket_id:
        print("error: empty ticket number", file=sys.stderr)
        return 2

    ticket_dir = ticket_dir_for_create(ticket_id)
    if ticket_dir.exists():
        print(f"error: {ticket_dir} already exists; refusing to overwrite",
              file=sys.stderr)
        return 1

    today_iso = datetime.now().strftime("%Y-%m-%d")

    ticket_dir.mkdir(parents=True)

    tpl_timeline = (TEMPLATES / "timeline.md").read_text(encoding="utf-8")
    (ticket_dir / "timeline.md").write_text(
        render(tpl_timeline, ticket_id, today_iso), encoding="utf-8"
    )

    tpl_meta = (TEMPLATES / "metadata.json").read_text(encoding="utf-8")
    meta_rendered = render(tpl_meta, ticket_id, today_iso)
    json.loads(meta_rendered)  # validate
    (ticket_dir / "metadata.json").write_text(meta_rendered, encoding="utf-8")

    print(str(ticket_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
