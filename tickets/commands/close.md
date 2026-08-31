---
description: Close a ticket — mirror its Zendesk terminal status locally, log a closing entry, and stamp the metadata.
argument-hint: [ticket-number]
---

You are closing a ticket: recording that it reached a terminal state, anchored
to what Zendesk shows.

- Ticket data → the user's workspace `$TICKETS_ROOT` (default `~/TICKETS`).
- Plugin scripts/templates → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files
  into the workspace.
- Every helper takes the **bare** number and resolves the folder itself.
- Closing is a **state change, not a cleanup** — never delete anything.

## Steps

1. **Resolve the ticket** — follow `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`:
   `$ARGUMENTS` > cwd > ask; state which ticket you resolved and
   how. `/close` **writes**, so run the mismatch guards (explicit ≠ cwd,
   ticket doesn't exist) before writing. Resolve the folder once:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
   ```

2. **Already terminal? Check it's fully stamped before writing.** Read
   `metadata.json` and branch on `status` + `resolved_at`:
   - **Terminal (`resolved`/`closed`) and `resolved_at` set** → already closed:
     say so (with `resolved_at`) and **stop**. Do **not** bump, append an entry,
     or re-stamp — a second pass duplicates the closing entry. Re-close only if
     the user **explicitly** asks; only then continue and add `--force` to the
     `close_meta.py` call in step 6.
   - **Terminal but `resolved_at` missing/`null`** → an *incomplete* close: the
     status was moved outside `/close` (e.g. `/log-updates` syncing status), so
     the timestamp was never stamped. **Backfill only — don't bump or append an
     entry** (the closing entry already exists). Derive the real resolution
     moment from the newest timeline entry (the closing/confirmation entry), or
     the Zendesk solved time from step 3, and run:
     ```bash
     python3 "${CLAUDE_PLUGIN_ROOT}/scripts/close_meta.py" <number> --stamp-only --resolved-at <ISO>
     python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_header.py" <number>
     ```
     Then **stop**. (Verify with step 3 first that Zendesk really shows it
     terminal; if it doesn't, treat it as the status-drift case below, not a
     backfill.)
   - **Not terminal** → a normal close: continue.

3. **Read the Zendesk terminal status** — the source of truth for whether this
   ticket is really done. Call the Zendesk MCP (`zendesk_get_ticket_with_attachments`,
   or a lighter get) and map its status:
   - Zendesk **solved** → local `resolved`
   - Zendesk **closed** → local `closed`
   - **Not terminal** (open / pending / hold): don't close silently against the
     source of truth. Say *"Zendesk still shows this as `<status>` — mark it
     solved/closed there first, or confirm you want to close locally anyway."*
     and wait for a yes.
   - **Stack down / can't read Zendesk**: fall back to asking the user which
     terminal state applies (solved → `resolved`, closed → `closed`), like
     `/log-updates`' paste-flow fallback. Don't block the close on the stack.

4. **Confirm the customer agreed.** A ticket is only closed once the customer has
   confirmed the resolution (a solved/closed Zendesk status is strong evidence).
   If that confirmation isn't already in the timeline or Zendesk, suggest
   `/log-updates` to pull it in first — **don't** close without it.

5. **Append the closing entry (bump-first).**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number>
   ```
   Prints the consumed `NNN` and refreshes `updated_at`. Append entry `[NNN]`
   with the **`Resolution`** snippet from
   `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md` (emoji ✅). Fill, one line
   each: **Root cause**, **Fix applied**, **KB candidate** (yes/no — ask the
   user).

6. **Stamp the metadata (deterministic, atomic) then re-render the header.**
   Don't hand-edit the JSON or the badge, and don't hand-compute the elapsed
   time:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/close_meta.py" <number> --status <resolved|closed> [--kb-candidate]
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_header.py" <number>
   ```
   `close_meta.py` sets `status`, `resolved_at` (now), computes
   `resolution_time_hours` from `opened_at`, refreshes `updated_at`, and — only
   with `--kb-candidate` — sets `kb_candidate=true` (it never downgrades a
   previous yes). Pass `--kb-candidate` when step 5's KB answer is yes. Add
   `--force` **only** when step 2 sent you here for an explicit re-close;
   otherwise never — the guard is there on purpose. `render_header.py` rebuilds
   the timeline header from the metadata, so the header, `/status`, and the
   metadata never drift — `resolved` renders as 🟢 Resolved, `closed` as
   ✅ Closed.

7. **Refresh the executive summary.** Update the `## 📋 Executive summary` prose
   to read as a closed case: final root cause, the fix, and the terminal status.
   It's the single source of truth `/status` reads instead of the full timeline,
   so leave it self-contained and current.

8. **Suggest natural follow-ups** (don't run them — these commands aren't ported
   yet):
   - If this is a KB candidate: `/kb` to draft a knowledge-base article from the
     timeline.
   - `/index-ticket` to index the now-complete, curated timeline into the
     vectordb so it surfaces in future similar-ticket searches.

## Don'ts

- Don't close a ticket the customer hasn't confirmed resolved.
- Don't re-close an already-terminal ticket unless the user explicitly asks —
  it duplicates the closing entry.
- Don't delete anything. Closing is a state change, not a cleanup.
- Don't hand-edit `metadata.json` or the timeline header — use `close_meta.py` +
  `render_header.py`.
