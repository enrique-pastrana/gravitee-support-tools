---
description: Compare local ticket folders against live Zendesk state and report divergences. Read-only — never writes back.
argument-hint: [ticket-number]
---

You are reconciling the user's local ticket folders against **Zendesk, the source
of truth**. The local `metadata.json` files are a snapshot that drifts; this
command **surfaces** that drift — it does not fix it. Paths assume
`${CLAUDE_PLUGIN_ROOT}` (plugin) and `$TICKETS_ROOT` (data).

**Strictly read-only.** Never write to Zendesk (the `zendesk` MCP is read-only
anyway) and never touch any local `metadata.json` / `timeline.md`. The output is a
chat report only. When a divergence calls for a fix, *suggest* the command
(`/close`, `/log-updates`) — don't run it.

## Scope

- **`$ARGUMENTS` names a ticket number** → sync just that one ticket.
- **No argument** → sync the **active queue**: every numeric ticket folder whose
  local `status` is not terminal (not `resolved`, not `closed`). Enumerate with:

  ```bash
  ls "$TICKETS_ROOT"/[0-9]*/[0-9]*/metadata.json "$TICKETS_ROOT"/[0-9]*/metadata.json 2>/dev/null
  ```

  Tickets are grouped by thousand (`$TICKETS_ROOT/<thousand>/<number>/`), so the
  first glob descends into the buckets; the second catches any not-yet-bucketed
  flat numeric folder. The bucket folders themselves (`16000/`, `17000/`) are
  **containers, not tickets** — they have no `metadata.json`, so the glob skips
  them. **Exclude** `_system`, `_kb`, `*copy*`, `TEST-*`, `test`, `___*`,
  `probe-*`. Read each `metadata.json`'s `status` and drop the terminal ones — do
  **not** re-verify resolved/closed tickets (reopenings are rare and caught when
  that ticket is next touched).

## Context economy

The full-queue run is a fan-out of ~30 local reads + ~30 Zendesk fetches. Per
`${CLAUDE_PLUGIN_ROOT}/references/context-economy.md`, **launch a general-purpose
subagent** so the intermediate JSON dumps stay off the main context — it returns
only the final tables + digest. Single-ticket runs can stay inline.

## Procedure

First confirm Zendesk is reachable: call the `zendesk` MCP tool `zendesk_health`.
If it errors, **stop** and tell the user to bring the stack up (`/tickets-up`) — do
not fall back to a local-only report; the comparison is the whole point.

For each in-scope ticket:

1. **Local** — read `<ticket>/metadata.json`, keep: `status`, `priority`,
   `customer`, `product`, `version`, `updated_at`, and the Jira link (`jira` field
   — string or list — and `related_tickets`).
2. **Zendesk** — `zendesk_get_ticket(<id>)`. The payload is large; extract only
   these **gold fields**, discard the rest:
   - `status` (raw: `new` / `open` / `pending` / `hold` / `solved` / `closed`)
   - `priority`
   - `updated_at`
   - `subject`
   - version + component from tags (`apim_X.Y.Z`, `am_X.Y.Z`, `apim_component_*`,
     `am_component_*`)
   - Jira key from custom field id `6151455794972` (e.g. `APIM-14177`, `GKO-2850`)
   - any `resolution_*` tag (e.g. `resolution_customer_abandoned`)

## Zendesk status semantics (do NOT translate to local vocabulary)

Show the **raw** Zendesk status in the table — these are not the user's states:

- `hold` → **engineering / L3** is working it (escalated, our side).
- `pending` → the **customer** is working it / we're waiting on them.
- `solved` / `closed` → done on Zendesk.
- `open` / `new` → in the agent's court.

Colour a row only by *divergence*; never rewrite the status.

## Classification

Tag each ticket, sort by severity (a ticket can carry more than one flag — file it
under its highest and mention the rest):

- 🔴 **Closed in ZD, active locally** — ZD `solved`/`closed` but local status not
  terminal. Suggest `/close <id>`. Advise only, never auto-close.
- 🟠 **New ZD activity not logged** — ZD `updated_at` newer than local
  `updated_at`. Likely a customer reply / internal note missing from the timeline.
  Suggest `/log-updates`.
- 🟡 **Metadata mismatch** — customer / version / priority / Jira key disagree with
  Zendesk's gold fields. Zendesk wins; flag the field. **Jira key:** check both the
  local `jira` field **and** `related_tickets` before flagging it missing —
  otherwise a present key reads as a false positive.
- 🟢 **Aligned** — no meaningful divergence.

## Silent execution

Read-only and destroys nothing → **zero ceremony**:

- Don't narrate steps ("first I'll list…", "launching the subagent…").
- Don't announce `zendesk_health` or its result **unless it fails** (only then:
  stop, point at `/tickets-up`).
- Don't ask for confirmation before or after — nothing to confirm.
- Don't add a closing question. End on the digest line.
- The only prose you emit is the tables + the one-line digest. Tool panels and the
  subagent's internal calls are harness chrome, not yours to comment on.

## Output

**One table per severity bucket**, each under its own heading, in this order (skip
an empty bucket):

### 🔴 Closed in ZD, active locally
### 🟠 New ZD activity not logged
### 🟡 Metadata mismatch only
### 🟢 Aligned

Per-section columns:

```
| Ticket | Local status | ZD status | Δ updated | Note |
```

- No "Flags" column — the heading says the flag. A lower-severity flag on the same
  row goes in the Note.
- **Δ updated**: human delta between ZD and local `updated_at` (`+6d ZD`, or `=`).
- **Note**: the specific divergence + terse suggested action (`/close`,
  `/log-updates`, fix field).
- For 🟢, a one-line list of ticket numbers is enough — no table.
- Close with a one-line digest: counts (`9🔴 9🟠 7🟡 1🟢`) and the single most
  urgent item.

## Don'ts

- Don't write to Zendesk or any local file. Report only.
- Don't auto-close or auto-edit metadata, even when the fix is obvious.
- Don't dump raw Zendesk JSON into chat — only the gold fields, in the table.
- Don't include resolved/closed/test folders unless `$ARGUMENTS` points at one.
