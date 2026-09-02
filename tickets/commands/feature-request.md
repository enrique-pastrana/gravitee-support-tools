---
description: Manage a customer feature request — draft the intake message (pre-filled for the customer to confirm), or, once they've replied, the closing message that hands off to their CSM/TAM/AE and closes the ticket.
argument-hint: [ticket] [intake|closing]
---

You are handling a **customer feature request**, a two-stage lifecycle tracked by
`fr_status` in `metadata.json` (`null → intake_sent → submitted`):

- **intake** — we don't yet have a clean statement of the need. Draft a message
  that **pre-fills** our understanding (use case, impact) for the customer to
  **confirm or correct**, and asks them for their criticality.
- **closing** — the customer has answered; **you** submit it to Product yourself
  (manual, outside the plugin), then this drafts the message that hands the
  customer off to their CSM/TAM/AE and closes the ticket.

Both messages go to the **customer**, so the same show-before-store rule as
`/reply` applies: draft → show in chat → iterate → your OK → **you send it** →
you confirm sent → only then log + advance state. Trigger it in plain language
too ("vamos a abrir una feature request", "la FR ya está hecha").

- Ticket data → `$TICKETS_ROOT`; plugin files → `${CLAUDE_PLUGIN_ROOT}` (never
  write plugin files into the workspace).
- **Never invent** customer-facing content — pre-fill only what the timeline
  supports; leave a `‹TODO›` or ask for the rest.

## Steps

1. **Resolve the ticket** per `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`
   (chain **arguments > cwd > ask**; this writes → run the mismatch guards). State
   the ticket in one line.

2. **Pick the stage.** Explicit in `$ARGUMENTS` / your words wins; else infer from
   `fr_status`: `null` → **intake**, `intake_sent` → **closing**. If still
   ambiguous, ask. Guard rails:
   - intake while `fr_status=intake_sent` → an intake already went out; confirm
     it's a re-send before proceeding.
   - closing while `fr_status` is `null` → no intake on record; confirm the
     customer really has given the info before closing.

3. **Read the timeline cheaply** (`${CLAUDE_PLUGIN_ROOT}/references/context-economy.md`):
   the `## 📋 Executive summary` + the entries stating the request (📥) and, for
   closing, the customer's answer. Don't dump the file. Drafting stays **inline**.

### Intake

4. Fill `${CLAUDE_PLUGIN_ROOT}/templates/fr-intake.md`:
   - `{{customer_first_name}}` — the requester's first name **only if** the
     timeline/metadata shows it; otherwise a neutral greeting.
   - `{{agent_name}}` — the current user's first name.
   - `{{use_case}}`, `{{impact}}` — **pre-fill our understanding** from the
     timeline, phrased for the customer to confirm/correct. `{{criticality}}` is
     the customer's call — leave the prompt unless the timeline already states it.
   - If the request is too thin to pre-fill honestly, say so and keep the section's
     question rather than inventing an answer.

5. **Show the draft in chat, iterate, save nothing.** Wait for explicit OK (a
   request for more changes is not an OK). Then **you send it**; wait for your
   "sent".

6. **On "sent"**, log + advance:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> --set fr_status=intake_sent --set status=waiting
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_header.py" <ticket>
   ```
   Append entry `[NNN]` with the **`Feature request`** snippet (📤, "intake sent")
   from `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`; refresh the executive
   summary (FR intake sent, awaiting the customer). `status=waiting` = ball in
   their court. Tell the user I'll flag the closing step when they reply (see
   **Proactive** below).

### Closing

4. **Contacts.** Read `csm` / `tam` / `ae` from `metadata.json`; build
   `{{contacts}}` from whichever are set (e.g. *"Customer Success Manager Jane Doe"*
   / *"TAM Bob Smith"*). If none needed are set, **ask**, and offer to persist them
   (`set_meta.py --set csm=… --set tam=… --set ae=…`) so they stick.

5. Fill `${CLAUDE_PLUGIN_ROOT}/templates/fr-closing.md` (`{{customer_first_name}}`
   as above; sign-off stays **"Gravitee Support"**). **Show, iterate, save
   nothing.** Wait for OK, then **you send it**; wait for your "sent".

6. **On "sent"**, log + advance:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> --set fr_status=submitted
   ```
   Append entry `[NNN]` with the **`Feature request`** snippet (📤, "closing
   sent"). Then **close the ticket**: chain **`/close <ticket>`**, which anchors to
   Zendesk's terminal status, logs the closing entry and stamps the metadata — don't
   hand-edit status here.

## Proactive (from `/log-updates` and `/sync`)

When a ticket has `fr_status=intake_sent` and new **customer** activity arrives,
that's the intake being answered → the closing stage is due. `/log-updates` and
`/sync` surface this; from here just proceed with **closing**.

## Don'ts

- **Don't auto-send** and **don't log/advance before** the user confirms it's sent.
- **Don't invent** the use case / impact — pre-fill from the timeline only; ask
  for the rest. Don't put words in the customer's mouth for **criticality**.
- **Don't skip `/close`** on the closing stage, and don't hand-edit `status` to
  close — let `/close` anchor it to Zendesk.
