---
description: Answer an investigation question about the ticket, then log the Q&A into the timeline in a collapsible entry.
argument-hint: <free-form question>
---

You are recording an investigation step: answer a question about the ticket,
iterate in chat, and only then log the Q&A into the timeline.

- Ticket data → the user's workspace `$TICKETS_ROOT` (default `~/TICKETS`).
- Plugin scripts/templates → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files
  into the workspace.
- Every helper takes the **bare** number and resolves the folder itself.
- Here `$ARGUMENTS` is the **question**, not a ticket number. If it's empty, ask
  the user what to investigate.

## Steps

1. **Resolve the ticket** — follow `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`,
   but the chain is **current ticket > cwd > ask** (no `$ARGUMENTS` rung — that's
   the question). State which ticket you resolved and how. `/investigate` writes,
   so run the applicable guards (cwd ≠ current; ticket doesn't exist → offer
   `/new-ticket`; content mismatch). Resolve the folder once:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
   ```

2. **Look for precedents first — before reasoning from scratch.** Consult only
   the sources that actually help this question; don't fire them all
   mechanically, and **skip the precedent search entirely** for a question about
   an artifact in the ticket itself ("what does this log say?"). Cite each source
   you use; if one is down, carry on with the rest.
   - **rag_search (vectordb, local)** — precedents in indexed tickets/code. Query
     per `${CLAUDE_PLUGIN_ROOT}/references/search-precedents.md` (literals, one
     search per literal, how to read the score). Good for recurring symptoms;
     skip for ticket-specific artifacts.
   - **Zendesk (live)** — `zendesk_search_tickets` on the symptom / error, to
     catch a case another engineer handled that isn't mirrored locally. Read-only.
   - **Jira (live)** — `searchJiraIssuesUsingJql` (e.g. `text ~ "<error>" ORDER BY
     updated DESC`) for already-reported bugs / escalations (APIM-XXXXX / AM-XXXX).
   - **Code — only with a concrete error / exception to trace:** vectordb for the
     indexed AM/APIM repos (per `search-precedents.md`), or GitHub
     (`search_code`) for freshness or non-indexed repos. Skip for conceptual
     questions with no error string.

3. **Answer** with the tools you need: `Read` for files in the ticket folder,
   `Bash` (`grep`/`find`) for local searches, `WebFetch` only if the user points
   at a URL. Stay grounded in what you can verify — **never invent ticket
   numbers, versions or commits.**

4. **Show what you found + your answer in chat, and write NOTHING to the timeline
   until the user confirms.** Iterate in chat first (his flow). Steps 5–9 —
   choosing the entry, formatting, the stamp, the summary — run only after a clear
   "log it".

5. **Decide where it goes:**
   - Opens a new investigation line → **new entry `[NNN]`** with emoji 🔍.
   - Continues the latest entry → **append to that entry's `<details>` block**,
     preserving the existing Q&A.
   - In doubt → ask the user.

6. **Format the Q&A** using the `Investigation` block of
   `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`:
   - `#### Qn: <the question>` — paraphrase if long; quote the verbatim text in
     the body.
   - **Claude:** the answer — concise, with code/log excerpts when useful.
   - If you ran a search, cite the exact command.
   - Leave a **Note:** line for the user's takeaway.

7. **Stamp `updated_at` — deterministic, atomic; don't hand-edit the JSON.**
   - **New entry** (step 5): get the number with
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number>` — it prints
     the consumed `NNN` and refreshes `updated_at`. Append entry `[NNN]`.
   - **Appended to an existing entry:** no new number, so refresh the mtime only:
     ```bash
     python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number> --touch
     ```
     `--touch` refreshes `updated_at` without bumping `next_entry`.
   `/investigate` records internal analysis — it does **not** change `status`, so
   there's no `set_meta`/`render_header` here.

8. **Refresh the `## 📋 Executive summary`** only if this investigation changes
   the picture (new hypothesis, ruled-out cause, new pending item). Minor or
   confirmatory → leave it as-is. It's the single source of truth `/status` and
   `/reply` read instead of the full timeline, so keep it self-contained and
   current.

9. **Brief response to the user** — the answer plus "Logged in entry [NNN]."
   Don't repeat the full answer in chat; it's already in the timeline.

## Don'ts

- Don't fabricate similar tickets — if a grep/search finds nothing, say so.
- Don't dump 200 lines of log into the timeline; quote the relevant 5–20.
- Don't restate a long question verbatim in the header — paraphrase in `Qn:` and
  quote the verbatim text in the body.
- Don't hand-edit `metadata.json` — use `bump_entry.py` (`--touch` when appending
  to an existing entry).
