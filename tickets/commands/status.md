---
description: Print a concise summary of the current ticket (entries, attachments, state).
argument-hint: [ticket-number]
---

You are giving a status summary. Be concise — this is for the user to glance
at, not a report.

## Steps

1. **Resolve the ticket:** `$ARGUMENTS` if provided, else infer from cwd. Note
   tickets are grouped by thousand, so the folder is at
   `$TICKETS_ROOT/<thousand>/<number>/` (e.g. `16000/16575/`), not a flat
   `<number>/`. Below, `<ticket>` means that **full folder path** — if you only
   have the number, resolve the path first with the shared helper:
   `python3 -c "import sys, os; sys.path.insert(0, os.path.join(os.environ['CLAUDE_PLUGIN_ROOT'], 'scripts')); from ticket_paths import resolve_ticket_dir; print(resolve_ticket_dir('<number>'))"`.
2. **Read** `<ticket>/metadata.json` in full. For `timeline.md`, do **not**
   read it end-to-end — it can be 30k+ tokens. Read only what you need:
   - The `## 📋 Executive summary` section (state of play).
   - The **last entry** for the "Last entry" line — grab it cheaply, e.g.
     `grep -n "^### \[" <ticket>/timeline.md | tail -1` to find the last
     entry's line, then `Read` with `offset` from there.
   Only fall back to reading more of the timeline if the summary is missing
   or clearly stale.
3. **Print** a short summary (in chat, not into a file):

   ```
   TICKET-<id> — <subject>
   Customer: <customer>   Status: <status>
   Product: <product> <version>   Priority: <priority>
   Opened: <opened_at>   Updated: <updated_at>

   Entries: <count>     Next ID: [<next_entry zero-padded>]
   Received: <N> files across <D> day(s)
   Reproduction: <yes/no>     KB draft: <yes/no>

   Last entry:
     [NNN] <date> — <emoji> <title>
   ```

   Counts come from filesystem:
   - `find <ticket>/received -type f ! -name '.zd_attachments.json' 2>/dev/null | wc -l`
     for total files. The `! -name` excludes `fetch_attachments`' idempotency
     ledger, which isn't an attachment and would otherwise inflate the count.
   - `ls <ticket>/received/ 2>/dev/null | wc -l` for day count (`ls` skips the
     dotfile ledger already).
   - existence checks for `reproduction/` and `kb_article_draft.md`.

4. **Suggest** one or two natural next actions if obvious (e.g., "Customer
   replied 3 days ago — `/customer` to log a follow-up?"). Skip if nothing
   stands out.

## Don'ts

- Don't dump the whole timeline.
- Don't modify any file with this command — it's read-only.
