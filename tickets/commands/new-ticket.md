---
description: Start a new ticket. Creates folder, timeline.md and metadata.json, and asks for the initial content.
argument-hint: <ticket-number>
---

You are starting a new ticket.

Ticket data lives in the user's tickets workspace, `$TICKETS_ROOT` (default
`~/TICKETS`). The plugin's machinery lives under `${CLAUDE_PLUGIN_ROOT}` — refer
to scripts and templates there, never inside the tickets workspace.

## Steps

1. **Resolve the ticket number.** The argument is `$ARGUMENTS`. If empty, ask
   the user for the Zendesk ticket number.

2. **Create the structure.** Use the Python helper — pass the **bare number**;
   it resolves the thousand bucket and creates the bucket folder on demand:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/init_ticket.py" <number>
   ```
   Tickets are grouped by thousand, so ticket 17545 lands in
   `$TICKETS_ROOT/17000/17545/` (alphanumeric ids have no bucket and go flat at
   the root). The helper creates the folder, copies templates, stamps the date,
   and **refuses to overwrite** an existing ticket — if it errors that the
   folder already exists, stop and tell the user; do **not** overwrite anything.
   It prints the full path it created.

3. **Pull the ticket from Zendesk (auto-fill).** Try the `zendesk` MCP server
   first — fetch ticket `<number>` (its detail + comments). From the response,
   extract: `subject`, requester / `customer` (organization or requester name),
   `priority`, `status`, `tags`, `created_at`, and the ticket `url`, plus the
   description (the opening message) and any first customer comment.
   - If the `zendesk` tool errors with a connection / compose failure, the
     ia-tooling stack is probably down — tell the user to run
     `"${IA_TOOLING_ROOT}/bin/local-tooling" start`, then **fall back** to
     asking the user to paste the initial Zendesk content manually (subject,
     customer, product, version, priority, opening message).
   - `product` and `version` are usually not clean Zendesk fields — infer from
     tags / subject if obvious, otherwise leave `TBD` and ask the user. Never
     invent them.

4. **Fill the ticket from what you pulled (or what the user pasted):**
   - Update `metadata.json` with the parsed fields (`subject`, `customer`,
     `product`, `version`, `priority`, `zendesk_url`, `tags`; ask back if
     anything is unclear; don't invent values). Also set `opened_at` to the
     ticket's Zendesk `created_at` (date part, `YYYY-MM-DD`) — `init_ticket`
     stamps today's date as a placeholder, so overwrite it with the real
     creation date. And set `last_comment_id` to the id of the opening comment
     you're logging as `[001]`, so `/log-updates` knows the baseline and only
     pulls what comes after. Then update the header of `timeline.md` (the
     `**Customer:**`, `**Product / version:**`, `**Opened:**`, … lines).
   - **Get the entry number (bump-first) and append.** Run
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number>` once — it
     increments `next_entry`, refreshes `updated_at`, and **prints the number it
     just consumed** (`001` on a fresh ticket); use that as `NNN`. Append entry
     `[NNN]` to `timeline.md` using the `Incoming update` snippet from
     `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`: 📥 Customer, a
     **summary** of the opening message (don't paste the literal Zendesk
     description), a `Key details (verbatim)` block only for load-bearing
     specifics, and the `🔗 Zendesk comment #<comment_id>` footer.

5. **Attachments — auto-download from Zendesk first.** Pull **only the opening
   comment's** attachments into entry `[001]` — pass its comment id (the same id
   you stored as `last_comment_id` in step 4):
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_attachments.py" <number> 1 --comment-id <opening_comment_id>`
   Scope it to that comment on purpose: `[001]` is the opening message, so only
   its own attachments belong here. Attachments from later comments belong to
   later entries and are pulled — under their correct entry number — by
   `/log-updates` as it logs those comments. (Scanning the whole thread here
   would tag every attachment `001_` and record it in the idempotency ledger, so
   `/log-updates` would then skip it and the later entries would lose their
   attachment links.) For a fresh ticket the thread is just the opening comment,
   so this fetches everything anyway. Follow
   `${CLAUDE_PLUGIN_ROOT}/references/attachments.md` for the full procedure —
   using the printed `path` values verbatim for the links, the manual
   `attach.py` fallback if it errors, and how to read what you downloaded.

6. **Check for similar past tickets.** Use two sources and merge:
   - **Semantic:** call the `vectordb` MCP `rag_search` tool with the ticket's
     symptom / error text to surface similar indexed tickets (skip if the tool
     is unavailable).
   - **Index:** read `$TICKETS_ROOT/_kb/tickets-index.md` if it exists and look
     for rows whose product/version, component or symptom plausibly match the
     new ticket (same product/version, same component, or overlapping symptom
     keywords). Skip this source if the file doesn't exist yet.
   - If any look relevant, list them briefly to the user with their ID,
     status and one-line symptom, so the user can decide whether to read the
     related timelines.
   - If nothing looks related, say so in one short sentence — don't
     stretch the match.
   - Don't auto-add anything to the index here; this step is read-only.

7. **Summarise:** print the path to the new ticket and ask what to do next
   (`/investigate`, `/log-updates`, `/reproduce`, …).

## Don'ts

- Don't run destructive shell commands.
- Don't write the timeline file from memory — use the template.
- Don't invent a customer, version or priority. If unknown, write `TBD`.
