---
description: Pull new activity from the Zendesk ticket (customer messages, replies, internal notes) into the timeline as summarised entries.
argument-hint: [ticket-number]
---

You are logging new ticket activity into the timeline.

Ticket data lives in the user's tickets workspace, `$TICKETS_ROOT` (default
`~/TICKETS`). The plugin's machinery lives under `${CLAUDE_PLUGIN_ROOT}` — refer
to scripts and templates there, never inside the tickets workspace.

This command records **any** new content on the ticket, whatever the source: a
customer message, a reply we already sent, an internal note, a linked Jira
update. It **summarises** — it does not store the literal text; the verbatim
lives in Zendesk and each entry keeps the `comment_id` as the pointer back to it.

## Resolve the ticket

Follow `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`: `$ARGUMENTS` >
current ticket > cwd > ask; state which ticket and how. `/log-updates`
**writes**, so run the mismatch guards before logging. Resolve the folder once:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
```

Below, `<ticket>` is the bare number (the Python helpers resolve the bucket
themselves); `<dir>` is that resolved folder (where `timeline.md` /
`metadata.json` live).

## Steps

1. **Find the baseline.** Read `<dir>/metadata.json` and note `last_comment_id`
   — the id of the newest Zendesk comment already in the timeline.

   **Sanity-check it against the timeline.** Scan `timeline.md` for its
   `🔗 Zendesk comment #<id>` footers and take the largest as the id actually
   logged. If `last_comment_id` is set and is **greater than** that largest
   logged id, the cursor is ahead of what's really in the timeline: the comments
   between them were never logged, and step 3 would silently skip them. Don't
   guess — tell the user how many comments fall in the gap and ask whether to
   (a) **backfill** from the largest logged id (treat everything after it as
   new), or (b) **trust the cursor** and only pull comments after
   `last_comment_id`. Then use the chosen id as the baseline for step 3. (Skip
   this check when the timeline has no numeric comment footers yet — e.g. a fresh
   adopt or paste-only history.)

2. **Fetch the thread from Zendesk.** Call the `zendesk` MCP
   `zendesk_get_ticket_with_attachments` for `<number>` (ticket + comments +
   attachment list in one call). If it errors (connection/compose failure), the
   ia-tooling stack is probably down — tell the user to run
   `"${IA_TOOLING_ROOT}/bin/local-tooling" start`, then **fall back to the paste
   flow** (see below) and stop following the Zendesk steps.

3. **Select what's new.** Keep only comments with an id **greater than** the
   baseline chosen in step 1 (the cursor, or the largest logged id if the user
   opted to backfill; comment ids increase over time). Process them in
   chronological order.
   - If `last_comment_id` is `null` (older ticket, or first run), don't guess:
     list the comments briefly (id · date · author · one-line) and ask the user
     which is the last one already logged, then treat everything after it as new.
   - If nothing is new, say so in one line and stop — don't write anything.

4. **For each new comment, in order:**
   a. **Classify** it (substantive vs. non-substantive) per
      `${CLAUDE_PLUGIN_ROOT}/references/classify-entry.md`.
   b. **Get its entry number (bump-first):** run
      `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>` once — it
      increments `next_entry`, refreshes `updated_at`, and **prints the number
      it just consumed**. Use that as `NNN` for this entry. (One call per
      entry; no separate peek.)
   c. **Non-substantive** → write a one-line entry
      `### [NNN] <date> - 🔔 <one sentence>` and move to the next comment (skip
      d–e).
   d. **Substantive** → pull this comment's attachments first:
      `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_attachments.py" <ticket> <NNN> --comment-id <comment_id>`
      (see `${CLAUDE_PLUGIN_ROOT}/references/attachments.md` for the full
      procedure, the manual fallback, and how to read what you downloaded).
   e. **Append the entry** to `timeline.md` using the `Incoming update` snippet
      from `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`:
      - timestamp = the comment's date/time,
      - emoji/source label by author: 📥 customer, 📤 a reply we sent, 🔒
        internal note (a non-public comment), 🔗 linked source. If unsure who
        the author is, look at the comment's `public` flag and author, and
        default to 📥.
      - **Summary** of the main points in your own words — never the literal.
      - **Key details (verbatim)** only for load-bearing specifics (exact
        errors, versions, config, commands, ids); omit if none.
      - attachments block (use the `path` values the helper printed),
      - `🔗 Zendesk comment #<comment_id>` footer.
      New entries go at the end of `## 🕐 Chronological timeline`.

5. **Update the baseline** — one call, don't hand-edit the JSON:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> --set last_comment_id=<newest_processed_comment_id>
   ```
   Set it to the id of the newest comment you just processed. (`bump_entry`
   already refreshed `updated_at`.)

6. **Refresh the `## 📋 Executive summary`** of `timeline.md` if the new
   activity changes the state of play (a new symptom, a customer confirmation, a
   decision). Keep it short — symptom, current hypothesis, caveats, pending,
   status. Skip if nothing changed. This summary is the single source of truth
   `/status` and `/reply` read instead of the whole timeline.

7. **Summarise** in chat: how many entries you added and a one-line each, then
   suggest a natural next action (`/investigate`, `/reply`, `/reproduce`).

## Fallback: paste flow (Zendesk unavailable)

When the stack is down or you have content that isn't in Zendesk yet:

1. Ask the user to paste the message text (attachments next).
2. Classify it (same reference). Non-substantive → one-line entry, bump, stop.
3. Attachments via the manual path in the attachments reference
   (`attach.py`), if any.
4. Get `NNN` bump-first, append the entry with the `Incoming update` snippet
   (no `comment_id` footer — write `🔗 Zendesk comment #—` or omit it), refresh
   the summary if warranted. Leave `last_comment_id` unchanged (we didn't read
   Zendesk).

## Don'ts

- Don't paste the literal message. Summarise; keep only load-bearing specifics
  verbatim. The comment id is the pointer to the exact words.
- Don't paste >50 lines of log into the timeline. Link the file.
- Don't append to the wrong section, and don't drop a message entirely — even
  pure noise gets a one-line entry.
