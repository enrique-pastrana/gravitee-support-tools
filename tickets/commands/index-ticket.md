---
description: Index (or re-index) a ticket's timeline into the vectordb so it surfaces in future similar-ticket searches.
argument-hint: [ticket-number]
---

You are indexing one ticket's curated timeline into the local vectordb, so a
future ticket can find this one as prior art.

- Ticket data → the user's workspace `$TICKETS_ROOT`; plugin scripts →
  `${CLAUDE_PLUGIN_ROOT}`.
- The helper takes the **bare** number and resolves the folder itself.
- Indexing is **idempotent**: re-running after edits updates changed chunks and
  prunes stale ones. Never duplicates, so a re-index is always safe.

## Steps

1. **Resolve the ticket** per `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`
   (chain **arguments > cwd > ask**). `$ARGUMENTS` is the **ticket number**.
   This stamps `indexed_at`, so it **writes** → run the mismatch guards. State
   the ticket in one line.

2. **Run the indexer:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/index_ticket.py" <number>
   ```
   Sends `timeline.md` to the vectordb (`source=tickets`,
   `path=<number>/timeline.md`, `kind=support-ticket`); the API chunks it
   server-side and upserts. On success it stamps `indexed_at` in `metadata.json`.

3. **Report the result in one line** from the script output: chunks indexed,
   backend, `indexed_at`.

## On failure

- **Exit 2 — "vectordb unreachable"** → the ia-tooling stack is down. Tell the
  user to run `/tickets:tickets-up`, then retry. Nothing was indexed.
- **Exit 1 — "No timeline found"** → wrong number, or the ticket has no
  `timeline.md` yet.
- **Exit 1 — "is empty"** → the timeline exists but has no content to index.
- **`! could not stamp indexed_at`** → the ingest **succeeded**; only the
  metadata stamp failed (missing or invalid `metadata.json`). Say so; don't
  re-run the ingest to "fix" it.

## Notes

- **Only `timeline.md` is indexed** — it's the distilled investigation (root
  cause, finding, workaround). Raw logs and attachments under `received/` are
  excluded on purpose: they'd dilute rag_search ranking.
- **When to index:** once a ticket has gained investigation worth finding again
  — after a meaty `/investigate`, or at `/close` on the now-complete timeline.
- **Staleness:** `indexed_at` older than `updated_at` means the indexed copy is
  behind the timeline — re-run to refresh it.
- This doesn't "train" anything: it adds this ticket's vectors to the search
  index so future searches can retrieve it. How those searches read the results
  is in `${CLAUDE_PLUGIN_ROOT}/references/search-precedents.md`.

## Don'ts

- Don't index a ticket that has nothing useful yet — a near-empty timeline adds
  noise to every future search without adding a precedent.
- Don't index anything but the timeline, and don't hand-edit `metadata.json` —
  the script stamps `indexed_at` itself.
