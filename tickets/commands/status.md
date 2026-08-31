---
description: Print a concise summary of the current ticket (entries, attachments, state).
argument-hint: [ticket-number]
---

You are giving a status summary. Be concise — this is for the user to glance
at, not a report. This command is **read-only**: never modify any file.

## Steps

1. **Resolve the ticket** — follow
   `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`: `$ARGUMENTS` > current
   ticket > cwd > ask. Read-only, so skip the write guards. Below, `<ticket>`
   means the **full folder path** — resolve it from the number with
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>`.
   Print the resolution as its own line **before** the summary —
   `Ticket: <id> (current)` / `(from arguments)` / `(from cwd)`. Don't fold it
   into the `TICKET-<id>` header; this standalone line is what lets the user
   catch a wrong ticket at a glance.
2. **Read** `<ticket>/metadata.json` in full. For `timeline.md`, do **not**
   read it end-to-end — it can be 30k+ tokens (the "never dump a big payload"
   rule of `${CLAUDE_PLUGIN_ROOT}/references/context-economy.md`). Read only what
   you need:
   - The `## 📋 Executive summary` section (state of play).
   - The **last entry** for the "Last entry" line — grab it cheaply:
     `grep -n "^### \[" <ticket>/timeline.md | tail -1` finds the last entry's
     line, then `Read` with `offset` from there.
   Only fall back to reading more of the timeline if the summary is missing
   or clearly stale.
3. **Print** the resolution line (step 1) then a short summary (in chat, not
   into a file):

   ```
   Ticket: <id> (current|from arguments|from cwd)

   TICKET-<id> — <subject>
   Customer: <customer>   Status: <status label>
   Product: <product> <version>   Priority: <priority>
   Opened: <opened_at>   Updated: <updated_at>

   Entries: <count>     Next ID: [<next_entry as 3 digits, e.g. 008>]
   Received: <N> files across <D> day(s)
   Reproduction: <yes/no>     KB draft: <yes/no>

   Last entry:
     [NNN] <date> — <emoji> <title>
   ```

   Values come from deterministic sources — don't eyeball them:
   - **Status label**:
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_header.py" --label "<status>"`
     (pass metadata's raw `status`; prints the same `🟡 Investigating` label the
     timeline header uses, so status reads consistently everywhere).
   - **Entries**: `grep -c "^### \[" <ticket>/timeline.md` — the count of entries
     actually in the timeline. Use this, **not** `next_entry - 1`: `next_entry` is
     bumped before an entry is written, so it can run ahead of reality; the
     timeline is the source of truth for what's really there.
   - **Received files**:
     `find <ticket>/received -type f ! -name '.zd_attachments.json' 2>/dev/null | wc -l`.
     The `! -name` excludes `fetch_attachments`' idempotency ledger, which isn't
     an attachment and would otherwise inflate the count.
   - **Day count**: `ls <ticket>/received/ 2>/dev/null | wc -l` — one entry per
     `received/<date>/` subfolder (`ls` skips the dotfile ledger already).
   - **Reproduction / KB draft**: existence checks for `reproduction/` and
     `kb_article_draft.md`.

4. **Suggest** one or two natural next actions if obvious (e.g., "Customer
   replied 3 days ago — `/log-updates` to pull it in?"). Skip if nothing
   stands out.

## Don'ts

- Don't dump the whole timeline.
