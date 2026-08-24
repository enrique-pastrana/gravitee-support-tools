#!/usr/bin/env python3
"""Regenerate the header of a ticket's timeline.md from its metadata.json.

Usage:
    render_header.py <ticket-number>

metadata.json is the single source of truth: this rewrites the block at the top
of timeline.md (everything before the first `---`) from it, so the header can
never drift from the metadata. Everything from the first `---` onward — the
executive summary, the timeline, the KB draft — is preserved untouched.

The `status` field maps to a display label + emoji via STATUS_DISPLAY; an
unknown status renders as "⚪ <Capitalised>" rather than failing, so a new
status value still produces a sensible header.

Refuses to act if metadata.json or timeline.md is missing/invalid, or if
timeline.md has no `---` separator (it would be unsafe to rewrite).
"""
from __future__ import annotations

import json
import os
import sys

from ticket_paths import resolve_ticket_dir

# status value -> header display. The single source of truth for how a ticket's
# status is shown; commands that change status (close, resolve, …) set the
# metadata `status` and re-render, so the label stays consistent everywhere.
STATUS_DISPLAY = {
    "investigating": "🟡 Investigating",
    "waiting": "⏳ Waiting",
    "pending": "⏳ Pending",
    "on hold": "⏸️ On hold",
    "blocked": "🔴 Blocked",
    "resolved": "🟢 Resolved",
    "closed": "✅ Closed",
}


def status_display(status: str) -> str:
    return STATUS_DISPLAY.get(status, f"⚪ {status.capitalize()}")


def build_header(meta: dict) -> list[str]:
    """The header lines (down to, but not including, the blank line + `---`)."""
    def field(key: str) -> str:
        value = meta.get(key)
        return "TBD" if value in (None, "") else str(value)

    return [
        f"# TICKET-{field('ticket_id')}: {field('subject')}",
        "",
        f"**Customer:** {field('customer')}",
        f"**Priority:** {field('priority')}",
        f"**Product / version:** {field('product')} {field('version')}",
        f"**Opened:** {field('opened_at')}",
        f"**Status:** {status_display(meta.get('status', 'investigating'))}",
        f"**Zendesk:** {field('zendesk_url')}",
    ]


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <ticket-number>", file=sys.stderr)
        return 2

    ticket_dir = resolve_ticket_dir(sys.argv[1])
    meta_path = ticket_dir / "metadata.json"
    timeline_path = ticket_dir / "timeline.md"

    if not meta_path.is_file():
        print(f"error: {meta_path} not found", file=sys.stderr)
        return 1
    if not timeline_path.is_file():
        print(f"error: {timeline_path} not found", file=sys.stderr)
        return 1

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: {meta_path} not valid JSON: {exc}", file=sys.stderr)
        return 1

    lines = timeline_path.read_text(encoding="utf-8").splitlines()
    try:
        sep = next(i for i, line in enumerate(lines) if line.strip() == "---")
    except StopIteration:
        print(f"error: {timeline_path} has no '---' separator; refusing to "
              "rewrite the header", file=sys.stderr)
        return 1

    # New header + a blank line, then everything from the first '---' onward.
    new_lines = build_header(meta) + [""] + lines[sep:]
    rendered = "\n".join(new_lines) + "\n"

    tmp = timeline_path.with_suffix(".md.tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, timeline_path)

    print(f"rewrote header of {timeline_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
