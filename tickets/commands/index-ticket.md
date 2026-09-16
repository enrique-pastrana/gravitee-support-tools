---
description: Index (or re-index) a ticket's timeline into the vectordb so it surfaces in future similar-ticket searches.
argument-hint: [ticket-number]
---

You are indexing one ticket's curated timeline into the local vectordb, so a
future ticket can find this one as prior art.

- Ticket data → `$TICKETS_ROOT`; plugin scripts → `${CLAUDE_PLUGIN_ROOT}`.
- The helper takes the **bare** number and resolves the folder itself.
- **Only `timeline.md`** is indexed — the distilled investigation. `received/`
  logs and attachments are excluded on purpose: they dilute rag_search ranking.
- **Idempotent**: re-running upserts changed chunks and prunes stale ones, so a
  re-index is always safe.

## Steps

1. **Resolve the ticket** per `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`
   (chain **arguments > cwd > ask**). `$ARGUMENTS` is the **ticket number**. This
   stamps `indexed_at`, so it **writes** → run the mismatch guards. State the
   ticket in one line.

2. **Index it:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/index_ticket.py" <number>
   ```
   Sends `timeline.md` as `source=tickets`, `path=<number>/timeline.md`,
   `kind=support-ticket`; the API chunks server-side and stamps `indexed_at` in
   `metadata.json` on success.

3. **Report in one line:** chunks indexed, backend, `indexed_at`.

## Outcomes

| Result | Means | Do |
|---|---|---|
| exit 0 | Indexed and stamped | Report it. |
| exit 0 + `! could not stamp indexed_at` | Ingest **succeeded**; only the stamp failed (`metadata.json` missing or invalid) | Say so. Don't re-run to "fix" it. |
| exit 2 `vectordb unreachable` | Stack down — **nothing was indexed** | Point at `/tickets:tickets-up`, then retry. |
| exit 1 `No timeline found` | Wrong number, or no `timeline.md` yet | Stop. |
| exit 1 `is empty` | Timeline has no content | Stop. |

## Notes

- **When:** once the ticket holds investigation worth finding again — after a
  meaty `/investigate`, or at `/close`.
- **Stale index:** `indexed_at` older than `updated_at` means the index lags the
  timeline → re-run.
- Indexing adds vectors to the search index; it trains nothing. How searches read
  what comes back: `${CLAUDE_PLUGIN_ROOT}/references/search-precedents.md`.

## Don'ts

- Don't index a thin timeline — it adds noise to every future search without
  adding a precedent.
- Don't hand-edit `metadata.json`; the script stamps `indexed_at` itself.
