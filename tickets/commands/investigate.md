---
description: Answer an investigation question about the ticket, then log the Q&A into the timeline in a collapsible entry.
argument-hint: <free-form question>
---

Record an investigation step: **answer first, iterate in chat, log only on
confirmation.** `$ARGUMENTS` is the **question** (not a ticket number); if empty,
ask what to investigate.

**Conventions**
- Ticket data → workspace `$TICKETS_ROOT` (default `~/TICKETS`).
- Scripts/templates/references → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files
  into the workspace.
- Every helper takes the **bare** number and resolves the folder itself.

## Steps

1. **Resolve the ticket.** Follow `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`,
   chain **current > cwd > ask** (no `$ARGUMENTS` rung — that's the question).
   State which ticket and how. `/investigate` writes → run the write-guards:
   cwd ≠ current · ticket doesn't exist → offer `/new-ticket` · content mismatch.
   Resolve the folder once:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
   ```

2. **Search precedents before reasoning from scratch** — selectively, not all
   mechanically. **Skip the whole search** for a question about an artifact in the
   ticket ("what does this log say?"). Cite each source used; if one is down,
   carry on. If **every** live source (rag_search + Zendesk + Jira) fails to
   connect, the stack/env is likely down — tell the user to run `/tickets-up`
   (it diagnoses a missing `IA_TOOLING_ROOT`), then continue with what you have.
   Query mechanics + scoring → `${CLAUDE_PLUGIN_ROOT}/references/search-precedents.md`.

   | source | tool | use when | skip when |
   |---|---|---|---|
   | rag_search (vectordb, local) | `rag_search` | recurring symptoms, precedents in indexed tickets/code | ticket-specific artifacts |
   | Zendesk (live, read-only) | `zendesk_search_tickets` | a case another engineer handled, not mirrored locally | — |
   | Jira (live) | `searchJiraIssuesUsingJql` — `text ~ "<error>" ORDER BY updated DESC` | already-reported bugs / escalations (APIM-XXXXX / AM-XXXX) | — |
   | Code | vectordb (indexed AM/APIM repos) or `search_code` (freshness / non-indexed) | **only** a concrete error/exception to trace | conceptual Qs, no error string |

3. **Answer** with `Read` (ticket files), `Bash` (`grep`/`find`), `WebFetch`
   (only if the user points at a URL). Stay grounded — **never invent ticket
   numbers, versions, or commits.**

4. **GATE — show findings + answer in chat; write NOTHING to the timeline until
   the user says "log it".** Iterate in chat first (his flow). Steps 5–9 run only
   after that confirmation.

5. **Place the entry:**
   - new investigation line → **new entry `[NNN]`** 🔍
   - continues the latest entry → **append to its `<details>`**, preserving Q&A
   - in doubt → ask

6. **Format** via the `Investigation` block of `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`:
   - `#### Qn: <question>` — paraphrase if long; quote verbatim text in the body
   - **Claude:** the answer — concise, with code/log excerpts
   - cite the exact command if you searched
   - leave a **Note:** line for the user's takeaway

7. **Stamp `updated_at`** — deterministic, atomic, never hand-edited:
   - new entry → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number>`
     (prints the consumed `NNN`, refreshes `updated_at`) → append entry `[NNN]`
   - appended to existing entry → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number> --touch`
     (refreshes `updated_at`, no bump)
   - `/investigate` doesn't change `status` → **no `set_meta`/`render_header`.**

8. **Refresh `## 📋 Executive summary`** only if the picture changed (new
   hypothesis, ruled-out cause, new pending item). Minor/confirmatory → leave it.
   It's the single source of truth `/status` and `/reply` read — keep it
   self-contained and current.

9. **Reply briefly:** the answer + "Logged in entry [NNN]." Don't repeat the full
   answer — it's already in the timeline.

## Don'ts

- No fabricated similar tickets — grep/search finds nothing → say so.
- No 200-line log dumps — quote the relevant 5–20.
- No hand-editing `metadata.json` — use `bump_entry.py` (`--touch` when appending).
