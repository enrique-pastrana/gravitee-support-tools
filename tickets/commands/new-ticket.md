---
description: Start a new ticket. Creates folder, timeline.md and metadata.json, and fills them from Zendesk.
argument-hint: <ticket-number>
---

Start a new ticket.

- Ticket data → the user's workspace `$TICKETS_ROOT` (default `~/TICKETS`).
- Plugin scripts/templates → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files
  into the workspace.
- Every helper takes the **bare** number and resolves the folder itself.

## Steps

1. **Ticket number** — use `$ARGUMENTS`; if empty, ask for it.

2. **Create the folder:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/init_ticket.py" <number>
   ```
   Prints the path it created. On an "already exists" error: **stop**, tell the
   user, overwrite nothing.

3. **Pull from Zendesk** — fetch ticket `<number>` (detail + comments) via the
   `zendesk` MCP. Extract: `subject`, `customer` (org or requester), `priority`,
   `status`, `tags`, `created_at`, the ticket `url`, the opening message, and the
   opening comment's **id**.
   - Tool error (connection / compose) → stack likely down: tell the user to run
     `"${IA_TOOLING_ROOT}/bin/local-tooling" start`, then fall back to asking
     them to paste the content manually.
   - `product` / `version` aren't clean Zendesk fields — infer from tags/subject
     if obvious, else leave `TBD` and ask. Never invent.

4. **Write metadata** — one call, don't hand-edit the JSON:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <number> \
     --set subject="…" --set customer="…" --set product="…" \
     --set version="…" --set priority="…" --set zendesk_url="…" \
     --set tags="tag1, tag2" \
     --set opened_at=<created_at_date> --set last_comment_id=<opening_comment_id>
   ```
   - Pass only fields you resolved; leave the rest at their `TBD`/`null`
     placeholders. Ask if unclear; don't invent. The helper types each field
     (so a version like `3.10` stays a string) and rejects unknown keys.
   - `opened_at` = Zendesk `created_at` (date, `YYYY-MM-DD`) — overwrites the
     placeholder `init_ticket` stamped.
   - `last_comment_id` = opening comment id — the baseline `/log-updates` reads
     to pull only what comes after.

5. **Regenerate the header:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_header.py" <number>
   ```
   Rebuilds the header from `metadata.json`; leaves everything below the first
   `---` untouched, so it can't drift from the metadata.

6. **Log the opening message as `[001]`:**
   - Get the number: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number>`
     → prints the consumed `NNN` (`001` here) and refreshes `updated_at`.
   - Append entry `[NNN]` with the **`Incoming update`** snippet from
     `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`: 📥 Customer, a
     **summary** (not the literal Zendesk text), a `Key details (verbatim)` block
     only for load-bearing specifics, and the `🔗 Zendesk comment #<id>` footer.

7. **Attachments — opening comment only:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_attachments.py" <number> 1 --comment-id <opening_comment_id>
   ```
   Scope to the opening comment on purpose: only its attachments belong to
   `[001]`; later comments' attachments are pulled under their own entries by
   `/log-updates`. Then follow `${CLAUDE_PLUGIN_ROOT}/references/attachments.md`
   — why the scoping matters, using the printed `path` values verbatim for links,
   the `attach.py` fallback, and reading what you downloaded.

8. **Similar past tickets** — read-only, merge two sources:
   - **Semantic:** `vectordb` MCP `rag_search` on the symptom / error text (skip
     if unavailable).
   - **Index:** read `$TICKETS_ROOT/_kb/tickets-index.md` if it exists; match on
     product/version, component, or overlapping symptom keywords.
   - List any relevant hits (id, status, one-line symptom) so the user can
     decide. If none, say so in one line — don't stretch. Add nothing here.

9. **Finish** — print the ticket path and suggest a next step (`/investigate`,
   `/log-updates`, `/reproduce`).

## Don'ts

- No destructive shell commands.
- Don't write the timeline from memory — use the snippet.
- Don't invent customer / version / priority — write `TBD`.
