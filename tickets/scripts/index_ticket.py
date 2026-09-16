#!/usr/bin/env python3
"""Index a single ticket's timeline.md into the local vectordb.

Usage:
    python3 index_ticket.py <ticket-number> [--api-url http://localhost:8000]

Only `timeline.md` is indexed — it is the curated, distilled investigation (root
cause, finding, workaround). Raw logs and attachments under `received/` are left
out on purpose: they add noise and degrade rag_search ranking.

Source/path: source="tickets", path="<ticket>/timeline.md", metadata
kind="support-ticket" (distinct from the KB's kind="kb-article"). The whole
document is sent once and the /ingest endpoint chunks it server-side, upserting
by (source, path, chunk_hash) — so re-running after edits updates changed
chunks and prunes stale ones, never duplicates.

On a successful ingest, `indexed_at` is stamped in metadata.json (atomically).
Compared against `updated_at` it tells whether the indexed copy is stale, which
is what lets a bulk re-index skip tickets that haven't moved. Stamping is
best-effort: the ingest has already happened, so a missing or unreadable
metadata.json is a warning, not a failure.

Exit codes: 0 ok, 1 usage/not-found, 2 vectordb unreachable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib import error, request

from ticket_paths import resolve_ticket_dir


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Index one ticket timeline into vectordb")
    p.add_argument("ticket", help="Ticket number / folder name")
    p.add_argument("--api-url", default="http://localhost:8000")
    return p.parse_args()


def post(api_url: str, payload: dict) -> dict:
    req = request.Request(
        f"{api_url.rstrip('/')}/ingest",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def stamp_indexed_at(meta_path: Path, when: str) -> bool:
    """Record the successful index in metadata.json. Atomic; never raises."""
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["indexed_at"] = when
        rendered = json.dumps(meta, indent=2, ensure_ascii=False) + "\n"
        json.loads(rendered)  # sanity check before committing
        tmp = meta_path.with_suffix(".json.tmp")
        tmp.write_text(rendered, encoding="utf-8")
        os.replace(tmp, meta_path)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def main() -> int:
    args = parse_args()
    ticket_dir = resolve_ticket_dir(args.ticket)
    timeline = ticket_dir / "timeline.md"
    if not timeline.is_file():
        print(f"✗ No timeline found: {timeline}", file=sys.stderr)
        return 1

    text = timeline.read_text(encoding="utf-8")
    rel_path = f"{args.ticket}/timeline.md"
    if not text.strip():
        print(f"✗ {rel_path} is empty, nothing to index", file=sys.stderr)
        return 1

    payload = {
        "source": "tickets",
        "path": rel_path,
        "text": text,
        "metadata": {"kind": "support-ticket", "ticket": args.ticket},
    }
    try:
        res = post(args.api_url, payload)
    except error.URLError as exc:
        print(
            f"✗ vectordb unreachable at {args.api_url} ({exc}).\n"
            f"  Is the stack up? Try: /tickets:tickets-up",
            file=sys.stderr,
        )
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"✗ Ingest failed: {exc}", file=sys.stderr)
        return 2

    indexed_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    stamped = stamp_indexed_at(ticket_dir / "metadata.json", indexed_at)

    print(
        f"✓ Indexed {rel_path} — {res.get('chunks', '?')} chunks "
        f"(backend={res.get('embedding_backend', '?')})"
    )
    if stamped:
        print(f"  indexed_at={indexed_at}")
    else:
        print("  ! could not stamp indexed_at (metadata.json missing or invalid)",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
