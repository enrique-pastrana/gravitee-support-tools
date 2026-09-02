---
description: Draft an L3 engineering escalation from the ticket (bug / problem / question), show it for review, then log it in the timeline once you've pasted it into Zendesk.
argument-hint: [ticket] [bug|problem|question]
---

You are drafting an **L3 / engineering escalation** from what the ticket already
knows, for the user to paste into Zendesk. Three types, one flow. It is
**outward-bound**: fill → show in chat → iterate → user OK → **the user pastes it
into Zendesk** → user confirms logged → only then touch `timeline.md`. Trigger it
in plain language too ("vamos a crear un bug", "escala esto como problem").

- Ticket data → `$TICKETS_ROOT` (default `~/TICKETS`); plugin files →
  `${CLAUDE_PLUGIN_ROOT}` (never write plugin files into the workspace).
- **Never invent** engineering-facing content. If a field has no basis in the
  ticket, ask the user or leave a clearly-marked `‹TODO›` — don't guess.

## Steps

1. **Resolve the ticket** per `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`
   (chain **arguments > cwd > ask**; `/escalate` writes, so run the mismatch
   guards). `$ARGUMENTS` may carry the number and/or the type. State the ticket
   in one line.

2. **Pick the type** — `bug`, `problem`, or `question`. Take it from the user's
   words / `$ARGUMENTS`; if unclear, ask (one line each):
   | Type | Use when | Template |
   |---|---|---|
   | **bug** | confirmed defect, reproducible, enough info to file | `templates/bug-report.md` |
   | **problem** | needs L3 analysis (repro'd or not); asks for code review / deeper look | `templates/l3-problem.md` |
   | **question** | need an answer/clarification from L3, not a fix | `templates/l3-question.md` |

3. **Read the timeline cheaply** (`${CLAUDE_PLUGIN_ROOT}/references/context-economy.md`):
   the `## 📋 Executive summary` + the entries that carry the evidence — a
   reproduction (🧪), root-cause/investigation (🔍), the key inbound (📥). Don't
   dump the whole file. The drafting (steps 5–7) stays **inline** with the user.

4. **Autofill the chosen template** from `${CLAUDE_PLUGIN_ROOT}/templates/<t>.md`:
   - `{{open_date}}` = today (problem/question).
   - `{{installation_type}}`, `{{apim_version}}`, `{{gko_version}}`,
     `{{am_version}}`, `{{database}}` ← `metadata.json` (problem/question). A
     field that's **null** in metadata renders as `N/A` (never a made-up value) —
     and surface it in step 5 to confirm it's genuinely N/A vs. just uncaptured.
   - **bug:** `{{describe}}`/`{{expected}}`/`{{current}}` from the summary +
     analysis; `{{repro_steps}}` from a 🧪 entry / `reproduction/steps.md` if
     present; `{{useful_info}}` = the attachments/logs already on the ticket;
     `{{environment}}` from `version`/`apim_version`; `{{browser}}` usually unknown.
   - **problem:** `{{summary}}`, `{{data_collected}}`, `{{replicated}}` (Y/N) +
     `{{replication_steps}}`, `{{investigation}}` from the timeline;
     `{{request_from_l3}}` is the ask.
   - **question:** `{{summary}}`, `{{investigation}}`, `{{questions}}`.

5. **Ask for what's missing** (in chat), skipping anything the timeline answers:
   - the **ask itself** — Request from L3 / the Question(s) / bug confirmation —
     usually needs your steer;
   - `{{browser}}` for a UI bug;
   - if any L3 context field is **null** in metadata (installation type,
     component versions, database), ask, and **offer to persist** it so future
     escalations autofill (step 8).

6. **Show the full filled template in chat, verbatim in a fenced code block** (it
   gets pasted as-is). Write **nothing** yet.

7. **Iterate in chat only** — apply tweaks, keep showing the updated draft, save
   nothing. Then **wait for explicit OK**. Proposing more changes or asking your
   opinion is **not** an OK.

8. **After the OK, hand it over and wait.** The user pastes it into Zendesk
   themselves. **Do not log yet.** Persist any L3 context they gave (no entry
   consumed — metadata only):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> \
     --set installation_type="<...>" --set apim_version="<...>" [--set ...]
   ```

9. **On the user's confirmation that they've logged it** ("done / sent / logged"),
   append the timeline entry:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>
   ```
   Append entry `[NNN]` with the **`L3 escalation`** snippet from
   `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md` (🚀; the pasted text inside
   the `<details>`).

10. **Offer a status change** (only if it moved): escalating usually parks the
    ticket waiting on engineering → suggest **`on hold`**; confirm, then
    ```bash
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> --set status="on hold"
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_header.py" <ticket>
    ```
    and refresh the `## 📋 Executive summary` (now escalated, what we asked L3).

## Don'ts

- **Don't auto-send** and **don't log before** the user confirms they pasted it.
- **Don't invent** content — ask or leave `‹TODO›`; never fabricate repro steps,
  versions, or a bug confirmation the ticket doesn't support.
- **Don't bump `next_entry`** for the metadata-only persist in step 8.
