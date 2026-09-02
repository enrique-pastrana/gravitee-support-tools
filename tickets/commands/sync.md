---
description: Compare local ticket folders against live Zendesk state and report divergences. Read-only — never writes back.
argument-hint: [ticket-number]
---

Reconcile local ticket folders against **Zendesk, the source of truth**. The local
`metadata.json` files are a snapshot that drifts; **surface** that drift, don't fix
it. Paths: `${CLAUDE_PLUGIN_ROOT}` (plugin), `$TICKETS_ROOT` (data).

**Strictly read-only.** Never write to Zendesk or to any local file — output is a
chat report only. When a divergence needs a fix, *suggest* the command (`/close`,
`/log-updates`); don't run it.

## Scope

- **`$ARGUMENTS` = a number** → sync just that ticket.
- **No argument** → sync the **active queue**. Enumerate + drop terminal ones:
  ```bash
  ls "$TICKETS_ROOT"/[0-9]*/[0-9]*/metadata.json "$TICKETS_ROOT"/[0-9]*/metadata.json 2>/dev/null
  ```
  - First glob descends the thousand-buckets (`$TICKETS_ROOT/<thousand>/<number>/`);
    second catches not-yet-bucketed flat numeric folders. Bucket folders (`16000/`)
    have no `metadata.json` → skipped.
  - Keep only tickets whose local `status` is **not** terminal (`resolved`/`closed`).
  - Exclude `_system`, `_kb`, `*copy*`, `TEST-*`, `test`, `___*`, `probe-*`.

## Steps

1. **Context economy** — the full-queue run is ~30 local reads + ~30 Zendesk
   fetches. Per `${CLAUDE_PLUGIN_ROOT}/references/context-economy.md`, run it in a
   **general-purpose subagent** that returns only the tables + digest. Single-ticket
   runs stay inline.
2. **Reachability** — call the `zendesk` MCP tool `zendesk_health`. On error, **stop**
   and point at `/tickets-up` — no local-only fallback; the comparison is the point.
3. **Per ticket, read local** `<ticket>/metadata.json`: `status`, `priority`,
   `customer`, `product`, `version`, `updated_at`, `fr_status`, Jira link (`jira`
   field — string or list — **and** `related_tickets`).
4. **Per ticket, fetch Zendesk** `zendesk_get_ticket(<id>)` — extract only these
   **gold fields**, discard the rest:
   - `status` (raw: `new`/`open`/`pending`/`hold`/`solved`/`closed`), `priority`,
     `updated_at`, `subject`
   - version + component from tags (`apim_X.Y.Z`, `am_X.Y.Z`, `apim_component_*`,
     `am_component_*`)
   - Jira key from custom field id `6151455794972` (e.g. `APIM-14177`)
   - any `resolution_*` tag
5. **Classify + emit** (see below).

## Zendesk status = raw, do NOT translate

Show Zendesk's raw status; these are not the user's states. Colour a row only by
*divergence*, never rewrite the status.

| Raw ZD | Means |
|--------|-------|
| `hold` | **engineering / L3** working it (escalated, our side) |
| `pending` | **customer** working it / waiting on them |
| `solved` / `closed` | done on Zendesk |
| `open` / `new` | in the agent's court |

## Classification

Sort by severity; a ticket can carry several flags — file under the highest,
mention the rest in the Note.

| Flag | Condition | Suggest |
|------|-----------|---------|
| 🔴 Closed in ZD, active locally | ZD `solved`/`closed`, local not terminal | `/close <id>` (advise only, never auto-close) |
| 🟠 New ZD activity not logged | ZD `updated_at` newer than local | `/log-updates` |
| 🟡 Metadata mismatch | customer / version / priority / Jira key disagree (Zendesk wins) | flag the field |
| 🟢 Aligned | no meaningful divergence | — |

**Feature-request intake answered:** if local `fr_status=intake_sent` and Zendesk
shows new customer activity (raw `pending`→ the customer replied, or `updated_at`
newer), note it on the row — the intake's been answered, suggest
`/feature-request closing`. It rides along with the 🟠/🟡 flag already on the row
(not a new severity bucket); surface it in the Note.

**Jira key:** check both the local `jira` field **and** `related_tickets` before
flagging it missing, or a present key reads as a false positive.

## Output

One table per non-empty bucket, in this order — `### 🔴 Closed in ZD, active
locally` / `### 🟠 New ZD activity not logged` / `### 🟡 Metadata mismatch only` /
`### 🟢 Aligned`. Columns:

```
| Ticket | Local status | ZD status | Δ updated | Note |
```

- No "Flags" column (the heading is the flag); a lower-severity flag on the row → in
  the Note.
- **Δ updated**: human delta between ZD and local `updated_at` (`+6d ZD`, or `=`).
- **Note**: the divergence + terse action (`/close`, `/log-updates`, fix field).
- 🟢: a one-line list of ticket numbers, no table.
- Close with a one-line digest: counts (`9🔴 9🟠 7🟡 1🟢`) + the single most urgent item.

## Silent execution — zero ceremony

- No step narration; no announcing `zendesk_health` or its result **unless it fails**.
- No confirmation before/after, no closing question. The only prose you emit is the
  tables + the digest — everything else is harness chrome.

## Don'ts

- Don't write to Zendesk or any local file. Report only.
- Don't auto-close or auto-edit metadata, even when the fix is obvious.
- Don't dump raw Zendesk JSON — only the gold fields, in the table.
- Don't include resolved/closed/test folders unless `$ARGUMENTS` points at one.
