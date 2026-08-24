---
description: Pull new activity from the Zendesk ticket (customer messages, replies, internal notes) into the timeline as summarised entries.
argument-hint: [ticket-number]
---

Log new ticket activity into the timeline.

- Ticket data → `$TICKETS_ROOT` (default `~/TICKETS`); plugin machinery →
  `${CLAUDE_PLUGIN_ROOT}`. Never write plugin files into the workspace.
- Records **any** new content, whatever the source: customer message, a reply we
  sent, internal note, linked Jira update.
- **Summarise, never store the literal** — the verbatim lives in Zendesk; each
  entry keeps the `comment_id` as the pointer back.

## Resolve the ticket

- Follow `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`: `$ARGUMENTS` >
  current > cwd > ask; state which ticket and how.
- `/log-updates` **writes** → run the mismatch guards before logging.
- Resolve the folder once:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
  ```
- Below: `<ticket>` = bare number (helpers resolve the bucket); `<dir>` = that
  resolved folder (holds `timeline.md` / `metadata.json`).

## Steps

1. **Find the baseline.**
   - Read `<dir>/metadata.json`; note `last_comment_id` (newest Zendesk comment
     already in the timeline).
   - **Sanity-check vs the timeline:** scan `timeline.md` for `🔗 Zendesk comment
     #<id>` footers, take the largest as the id actually logged.
   - **On a gap** (`last_comment_id` set and **greater than** that largest logged
     id): the in-between comments were never logged and step 3 would skip them.
     Don't guess — tell the user how many fall in the gap and ask: (a) **backfill**
     from the largest logged id, or (b) **trust the cursor**. Use the chosen id as
     the step-3 baseline.
   - Skip this check when the timeline has no numeric comment footers yet (fresh
     adopt / paste-only history).

2. **Fetch the thread from Zendesk.**
   - Call `zendesk` MCP `zendesk_get_ticket_with_attachments` for `<number>`
     (ticket + comments + attachment list, one call).
   - On error (connection/compose): stack likely down → tell the user to run
     `"${IA_TOOLING_ROOT}/bin/local-tooling" start`, then **fall back to the paste
     flow** below and stop the Zendesk steps.

3. **Select what's new.**
   - Keep only comments with id **greater than** the step-1 baseline (ids increase
     over time). Process in chronological order.
   - `last_comment_id` is `null` (older ticket / first run) → don't guess: list
     comments briefly (id · date · author · one-line), ask which is the last one
     already logged, treat everything after as new.
   - Nothing new → say so in one line and stop; write nothing.

4. **For each new comment, in order:**
   - **Classify** (substantive vs non-substantive) per
     `${CLAUDE_PLUGIN_ROOT}/references/classify-entry.md`.
   - **Get the entry number (bump-first):**
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>` — increments
     `next_entry`, refreshes `updated_at`, prints the consumed `NNN`. One call per
     entry.
   - **Non-substantive** → one-line entry `### [NNN] <date> - 🔔 <one sentence>`;
     next comment (skip the rest).
   - **Substantive** → pull this comment's attachments first:
     ```bash
     python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_attachments.py" <ticket> <NNN> --comment-id <comment_id>
     ```
     (full procedure / fallback / how to read them:
     `${CLAUDE_PLUGIN_ROOT}/references/attachments.md`).
   - **Append the entry** to `timeline.md` with the `Incoming update` snippet from
     `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`:
     - timestamp = the comment's date/time.
     - emoji by author: 📥 customer, 📤 a reply we sent, 🔒 internal note
       (non-public), 🔗 linked source. Unsure → check the `public` flag + author,
       default 📥.
     - **Summary** in your own words — never the literal.
     - **Key details (verbatim)** only for load-bearing specifics (exact errors,
       versions, config, commands, ids); omit if none.
     - attachments block (use the `path` values the helper printed).
     - `🔗 Zendesk comment #<comment_id>` footer.
     - New entries go at the end of `## 🕐 Chronological timeline`.

5. **Update the baseline** — one call, don't hand-edit the JSON:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> --set last_comment_id=<newest_processed_comment_id>
   ```
   Set it to the newest comment you processed. (`bump_entry` already refreshed
   `updated_at`.)

6. **Refresh the `## 📋 Executive summary`** of `timeline.md` only if the new
   activity changes the state of play (new symptom, customer confirmation,
   decision). Keep it short: symptom, hypothesis, caveats, pending, status. It's
   the single source of truth `/status` and `/reply` read instead of the timeline.

7. **Summarise in chat** — how many entries added + one line each, then suggest a
   next action (`/investigate`, `/reply`, `/reproduce`).

## Fallback: paste flow (Zendesk unavailable)

Stack down, or content not in Zendesk yet:

- Ask the user to paste the message text (attachments next).
- Classify (same reference). Non-substantive → one-line entry, bump, stop.
- Attachments via the manual path (`attach.py`) in the attachments reference.
- Get `NNN` bump-first, append with the `Incoming update` snippet (no footer —
  write `🔗 Zendesk comment #—` or omit), refresh the summary if warranted.
- Leave `last_comment_id` unchanged (we didn't read Zendesk).

## Don'ts

- Don't paste the literal message — summarise; keep only load-bearing specifics
  verbatim. The comment id points to the exact words.
- Don't paste >50 lines of log into the timeline — link the file.
- Don't append to the wrong section, and don't drop a message entirely — even
  pure noise gets a one-line entry.
