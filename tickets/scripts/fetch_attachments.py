#!/usr/bin/env python3
"""Download NEW Zendesk attachments for a ticket into received/<date>/NNN_<name>.

Idempotent: keeps a ledger of attachment tokens already downloaded so re-runs
only fetch what's new. Follows the same naming convention as attach.py
(NNN_ prefix, normalised filename, routed to received/<comment-date>/).

Usage:
    fetch_attachments.py <ticket> <entry> [--comment-id ID] [--date YYYY-MM-DD]
                         [--env PATH] [--dry-run]

  <entry>        The NNN entry number to prefix downloaded files with.
  --comment-id   Only download attachments from this comment (e.g. the message
                 being logged by /log-updates, or the opening comment for
                 /new-ticket's [001]). Omit to scan the whole thread — pull
                 every attachment across all comments under one entry number.
  --date         Force the date subfolder (YYYY-MM-DD). By default each
                 attachment goes to received/<date-of-its-comment>/.
  --dry-run      List what would be downloaded without writing anything.

Auth: reads ZENDESK_BASE_URL / ZENDESK_EMAIL / ZENDESK_API_TOKEN (api-token
mode) or ZENDESK_OAUTH_ACCESS_TOKEN (oauth mode) from the ia-tooling .env.

Output: a JSON object on stdout:
    {"downloaded": [{"path": ..., "file_name": ..., "content_type": ...,
                     "size": ..., "comment_id": ...}],
     "skipped": <n already-present>, "ticket": <id>}
so the caller can read images and describe them.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from ticket_paths import resolve_ticket_dir

# ia-tooling .env holding the Zendesk token. Machine-specific: honour
# $IA_TOOLING_ENV, else fall back to $IA_TOOLING_ROOT/.env (the same variable
# the plugin's .mcp.json uses to locate the stack), else ~/ia-tooling/.env.
_IA_TOOLING_ROOT = Path(os.environ.get("IA_TOOLING_ROOT", Path.home() / "ia-tooling"))
DEFAULT_ENV = Path(os.environ.get("IA_TOOLING_ENV", _IA_TOOLING_ROOT / ".env"))
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Zendesk's attachment CDN (zdusercontent.com) sits behind Cloudflare, which
# blocks the default Python-urllib User-Agent (error 1010). Use a curl UA.
USER_AGENT = "curl/8.4.0"


def normalise(name: str) -> str:
    """Same rules as attach.py: lowercase stem, special chars -> _, keep ext."""
    stem = Path(name).stem
    ext = Path(name).suffix.lower()
    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9._-]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    if not stem:
        stem = "file"
    return f"{stem}{ext}"


def load_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not env_path.is_file():
        return env
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        v = v.strip().strip("'").strip('"')
        env[k.strip()] = v
    return env


def auth_header(env: dict[str, str]) -> dict[str, str]:
    mode = (env.get("ZENDESK_AUTH_MODE") or "api-token").lower()
    if mode == "oauth" and env.get("ZENDESK_OAUTH_ACCESS_TOKEN"):
        return {"Authorization": f"Bearer {env['ZENDESK_OAUTH_ACCESS_TOKEN']}"}
    email = env.get("ZENDESK_EMAIL")
    token = env.get("ZENDESK_API_TOKEN")
    if not email or not token:
        raise SystemExit("error: missing ZENDESK_EMAIL / ZENDESK_API_TOKEN in env")
    raw = f"{email}/token:{token}".encode()
    return {"Authorization": "Basic " + base64.b64encode(raw).decode()}


def base_url(env: dict[str, str]) -> str:
    url = env.get("ZENDESK_BASE_URL", "https://graviteesource.zendesk.com")
    return url.rstrip("/")


def http_get(url: str, headers: dict[str, str]) -> bytes:
    req = urllib.request.Request(url, headers={**headers, "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # noqa: D401
        return None


_NOREDIR_OPENER = urllib.request.build_opener(_NoRedirect)


def download_attachment(url: str, headers: dict[str, str]) -> bytes:
    """Download a Zendesk attachment.

    The /attachments/token/ URL 302s to a CDN host (zdusercontent.com) that
    carries its own JWT in the redirect URL and *rejects* the Zendesk
    Authorization header. So: send auth to Zendesk to get the 302, then fetch
    the CDN URL with no auth header (like curl does across hosts). The CDN is
    behind Cloudflare, which needs a non-urllib User-Agent.
    """
    req = urllib.request.Request(
        url, headers={**headers, "User-Agent": USER_AGENT})
    try:
        with _NOREDIR_OPENER.open(req, timeout=30) as resp:
            return resp.read()  # no redirect (rare): body is the file
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
            r2 = urllib.request.Request(
                e.headers["Location"], headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(r2, timeout=30) as resp:
                return resp.read()
        raise


def fetch_comments(base: str, ticket: str, headers: dict[str, str]) -> list[dict]:
    """Page through /api/v2/tickets/<id>/comments.json."""
    comments: list[dict] = []
    url = f"{base}/api/v2/tickets/{ticket}/comments.json?page[size]=100"
    while url:
        data = json.loads(http_get(url, {**headers, "Accept": "application/json"}))
        comments.extend(data.get("comments", []))
        nxt = (data.get("links") or {}).get("next")
        url = nxt if nxt and data.get("meta", {}).get("has_more") else None
    return comments


# Inline images embedded in a comment's html_body as
# <img src="https://<host>/attachments/token/<TOKEN>/?name=<file>">. These are
# NOT listed in comment["attachments"] (that array is formal uploads only), so
# we parse them out of the HTML and treat them like any other attachment.
INLINE_IMG_RE = re.compile(
    r'<img[^>]+src="([^"]*?/attachments/token/([^/"?]+)/[^"]*?)"', re.I)
INLINE_NAME_RE = re.compile(r"[?&]name=([^&\"]+)", re.I)


def inline_attachments(comment: dict) -> list[dict]:
    """Extract inline images from a comment's html_body as attachment dicts.

    Shaped like a formal attachment (token / content_url / file_name /
    content_type) so the main loop can handle inline and formal uniformly.
    Deduplicated by token within the comment.
    """
    html = comment.get("html_body") or ""
    out: list[dict] = []
    seen: set[str] = set()
    for full_url, token in INLINE_IMG_RE.findall(html):
        if token in seen:
            continue
        seen.add(token)
        m = INLINE_NAME_RE.search(full_url)
        name = urllib.parse.unquote(m.group(1)) if m else "inline.png"
        # Zendesk names every inline paste "image.png"; disambiguate with the
        # token so multiple inline images in one comment don't all collide.
        stem, ext = Path(name).stem, (Path(name).suffix or ".png")
        name = f"{stem}_{token[:8]}{ext}"
        out.append({
            "token": token,
            "content_url": full_url,
            "file_name": name,
            "content_type": None,
            "size": None,
            "_inline": True,
        })
    return out


def comment_date(comment: dict) -> str:
    ts = comment.get("created_at")
    if ts:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now().strftime("%Y-%m-%d")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ticket")
    p.add_argument("entry", type=int)
    p.add_argument("--comment-id", type=int, default=None)
    p.add_argument("--date", default=None)
    p.add_argument("--env", default=str(DEFAULT_ENV))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.date and not DATE_RE.match(args.date):
        print(f"error: --date must be YYYY-MM-DD, got: {args.date}", file=sys.stderr)
        return 2

    ticket_dir = resolve_ticket_dir(args.ticket)
    if not ticket_dir.is_dir():
        print(f"error: ticket folder not found: {ticket_dir}", file=sys.stderr)
        return 1

    env = load_env(Path(args.env).expanduser())
    headers = auth_header(env)
    base = base_url(env)

    try:
        comments = fetch_comments(base, args.ticket, headers)
    except urllib.error.URLError as e:
        print(f"error: cannot reach Zendesk: {e}", file=sys.stderr)
        return 3

    # Idempotency ledger: which attachment tokens we've already pulled.
    ledger_path = ticket_dir / "received" / ".zd_attachments.json"
    ledger: dict = {}
    if ledger_path.is_file():
        try:
            ledger = json.loads(ledger_path.read_text())
        except json.JSONDecodeError:
            ledger = {}
    done = set(ledger.get("tokens", []))

    downloaded: list[dict] = []
    skipped = 0

    for c in comments:
        if args.comment_id is not None and c.get("id") != args.comment_id:
            continue
        for att in list(c.get("attachments", [])) + inline_attachments(c):
            token = att.get("token") or att.get("content_url")
            if not token:
                continue
            if token in done:
                skipped += 1
                continue

            date_str = args.date or comment_date(c)
            dest_dir = ticket_dir / "received" / date_str
            prefix = f"{args.entry:03d}_"
            dest = dest_dir / (prefix + normalise(att.get("file_name", "file")))

            # Avoid clobbering: if the normalised target exists, suffix _2, _3…
            base_stem, base_ext = dest.stem, dest.suffix
            n = 2
            while dest.exists():
                dest = dest_dir / f"{base_stem}_{n}{base_ext}"
                n += 1

            entry = {
                "file_name": att.get("file_name"),
                "content_type": att.get("content_type"),
                "size": att.get("size"),
                "comment_id": c.get("id"),
                "path": str(dest),
            }

            if args.dry_run:
                downloaded.append({**entry, "dry_run": True})
                continue

            try:
                blob = download_attachment(att["content_url"], headers)
            except urllib.error.URLError as e:
                print(f"warn: failed {att.get('file_name')}: {e}", file=sys.stderr)
                continue

            dest_dir.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(blob)
            done.add(token)
            downloaded.append(entry)

    if not args.dry_run and downloaded:
        ledger["tokens"] = sorted(done)
        ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

    print(json.dumps({
        "downloaded": downloaded,
        "skipped": skipped,
        "ticket": args.ticket,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
