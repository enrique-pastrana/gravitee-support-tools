#!/usr/bin/env python3
"""Index a published KB article into the local vectordb.

Usage:
    python3 index_kb.py <ticket-number> --file <article.md> --url <kb-url> \
        [--path <source-path>] [--title "..."] [--api-url http://localhost:8000]

Indexes the FULL article (public body + INTERNAL block) so a future rag_search
surfaces the distilled KB answer, with its title and canonical URL travelling
alongside. The vectordb is private (support team only), so the internal
references (ticket, Jira, customer, engineering notes) are kept on purpose —
they are the most useful part when triaging a new ticket.

Decoupled from ticket folders: the article lives in the KB GitHub repo, so the
caller (/kb-publish) fetches the merged article via `gh api` and passes it here
as --file. `--url` is the canonical article URL on the repo's default branch;
`--path` is the vectordb source path used for upsert identity.

A header line with the title and the article URL is prepended to the chunk text
so the link shows up in the returned content even if the result viewer doesn't
render metadata.

Source/path: source="tickets", path=<--path> (default "<ticket>/kb-article.md"),
metadata kind="kb-article" (distinct from the timeline's kind="support-ticket").
The /ingest endpoint upserts by (source, path, chunk_hash), so re-running after
edits updates changed chunks and prunes stale ones.

Exit codes: 0 ok, 1 usage/not-found, 2 vectordb unreachable.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib import error, request


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Index one published KB article into vectordb")
    p.add_argument("ticket", help="Source ticket number / folder name")
    p.add_argument("--file", required=True, help="Path to the article Markdown to index")
    p.add_argument("--url", required=True, help="Canonical URL of the published article")
    p.add_argument("--path", default=None, help="vectordb source path (default: <ticket>/kb-article.md)")
    p.add_argument("--title", default=None, help="KB title (default: first H1 of the article)")
    p.add_argument("--api-url", default="http://localhost:8000")
    return p.parse_args()


def first_h1(text: str) -> str | None:
    m = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return m.group(1).strip() if m else None


def post(api_url: str, payload: dict) -> dict:
    req = request.Request(
        f"{api_url.rstrip('/')}/ingest",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    args = parse_args()
    article = Path(args.file)
    if not article.is_file():
        print(f"✗ No article file found: {article}", file=sys.stderr)
        return 1

    body = article.read_text(encoding="utf-8")
    title = args.title or first_h1(body) or f"KB article — ticket {args.ticket}"
    rel_path = args.path or f"{args.ticket}/kb-article.md"

    # Prepend a header so the title + article URL are part of the indexed
    # content (visible in the returned chunk even without metadata rendering).
    header = (
        f"KB ARTICLE: {title}\n"
        f"KB URL: {args.url}\n"
        f"Source ticket: {args.ticket}\n\n"
    )
    text = header + body

    payload = {
        "source": "tickets",
        "path": rel_path,
        "text": text,
        "metadata": {
            "kind": "kb-article",
            "ticket": args.ticket,
            "title": title,
            "kb_url": args.url,
        },
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

    print(
        f"✓ Indexed KB {rel_path} — {res.get('chunks', '?')} chunks "
        f"(backend={res.get('embedding_backend', '?')}) → {args.url}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
