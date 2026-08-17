---
description: Log a new message from the customer (pasted text and/or attachments) into the current ticket's timeline.
argument-hint: [ticket-number]
---

You are logging a new inbound message from the customer.

Ticket data lives in the user's tickets workspace, `$TICKETS_ROOT` (default
`~/TICKETS`). The plugin's machinery lives under `${CLAUDE_PLUGIN_ROOT}` — refer
to scripts and templates there, never inside the tickets workspace.

## Resolve the ticket

- If `$ARGUMENTS` has a ticket number, use it.
- Otherwise infer the current ticket from the cwd. If still ambiguous, ask.

Tickets are grouped by thousand, so the folder is at
`$TICKETS_ROOT/<thousand>/<number>/` (e.g. `16000/16575/`), not a flat
`<number>/`. The Python helpers below take the **bare number** and resolve the
bucket themselves; timeline edits happen in the ticket folder.

## Substantive vs. non-substantive

Before logging, classify the message — this controls how much goes into the
timeline (don't pay tokens to store process noise verbatim):

- **Substantive** — answers a question we asked, brings a new technical fact,
  a decision, a new symptom, or confirms a fix. → Log a **full entry** (steps
  below as normal). Summarise long prose into the relevant fact instead of
  pasting it word-for-word; link/keep the attachment for the verbatim source.
- **Non-substantive** — process noise with no technical content: "any update?",
  a reminder, an acknowledgement, an out-of-office, "we're still looking into
  it". → Log a **one-line entry** only:
  `### [NNN] <date> - 🔔 <one sentence>` — no `<details>`, no pasted body, no
  analysis, and **do not touch the Executive summary**.
- **When in doubt → full entry.** The default bias is to never lose
  information; the one-line treatment is only for what is clearly process
  noise. **Never drop a message entirely** — the timeline stays chronological
  and complete.

## Steps

1. **Get the entry number** by running
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket> --peek`.
   Save it as `NNN`. (You'll commit the bump at step 5.)
2. **Ask** the user to paste the customer's message (just the text — attachments
   come next). Then classify it (see above). If it's non-substantive, skip the
   attachment/analysis machinery and just write the one-line entry, then commit
   the bump (step 5) and stop.
3. **Attachments — try Zendesk auto-download first:**
   - If the message came from Zendesk and you know the comment id (from the
     `zendesk` MCP `zendesk_get_ticket_comments` response), pull its
     attachments automatically:
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_attachments.py" <ticket> <NNN> --comment-id <comment_id>`
     The helper authenticates against the ia-tooling `.env`
     (`$IA_TOOLING_ROOT/.env`), downloads only **new** attachments (idempotent
     via a ledger), and routes them to `received/<comment-date>/NNN_<name>` with
     the same naming attach.py uses. It prints JSON with the saved paths — read
     it to know what landed.
   - If you don't have a comment id, omit `--comment-id` to scan the whole
     thread (still only grabs what's new).
   - **Use the `path` values from that JSON verbatim** for the timeline's
     attachment links. The helper lowercases and normalises filenames and adds
     the `NNN_` prefix, so the on-disk name differs from the original Zendesk
     filename — don't reconstruct the links from the original name or they
     won't resolve.
   - **Fall back to the manual flow** if the helper errors (stack down, no
     Zendesk creds, MCP unavailable): ask the user for the source path (or
     "drag them into ~/Downloads now") and move each file with
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/attach.py" <ticket> <NNN> <source>`,
     which handles the date routing and `NNN_` renaming (use the destination
     path it prints). All files (screenshots, logs, configs) go to the same
     date folder — no per-type split.
   - For images (downloaded or pasted), `Read` them and capture a one-line
     description.
   - For text logs ≤ 1 MB you can read and extract the relevant excerpt.
     For larger logs, only read the first/last N lines or grep for stack
     traces; do **not** paste the full content.
4. **Append entry** `[NNN]` to `timeline.md` using the
   `inbound customer message` snippet from
   `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`. Fill:
   - timestamp = current local time (YYYY-MM-DD HH:MM),
   - short title = your one-line summary of the message,
   - quoted message body — quote the relevant part, not the whole thing. If
     the message is long prose, capture the actionable fact(s) and trim
     greetings, restated history and filler. The attachment / Zendesk thread
     is the verbatim source if ever needed.
   - attachments block,
   - initial analysis inside `<details>` (only if you actually have something
     to say from reading the attachments — don't pad with fluff).
5. **Commit the bump** by running
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>`.
   This increments `next_entry` and refreshes `updated_at`.
6. **Ask** what to do next (`/investigate`, `/reply`, `/reproduce`, …).

## Don'ts

- Don't paste >50 lines of log into the timeline. Link the file.
- Don't keep original filenames if they're noisy (`Screenshot 2025-05-20 at
  10.34.12.png` → `001_screenshot.png`).
- Don't append to the wrong section. New entries go at the end of
  `## 🕐 Chronological timeline`.
