# Reference: handling ticket attachments

Shared procedure for pulling attachments out of a Zendesk ticket into the
ticket's `received/` folder. Commands (`/log-updates`, `/new-ticket`) point here
instead of repeating the steps. Paths below assume `${CLAUDE_PLUGIN_ROOT}` (the
plugin) and `$TICKETS_ROOT` (the ticket data).

## Division of labour: script vs. MCP

The `zendesk` MCP server *can* return attachments (`zendesk_get_attachment`),
but it hands them back **as base64 in the model context** — expensive in tokens
and it does **not** write them to disk. So keep the two jobs separate:

- **Download → always the script** (`fetch_attachments.py`). It writes files
  straight to `received/`, keeps the bytes out of context, is idempotent, and
  normalises names. This is what actually persists an attachment.
- **Explore → the MCP** (`zendesk_get_ticket_with_attachments` /
  `zendesk_get_ticket_attachments`). Use it only to *see what a ticket contains*
  (the comment thread + the list of attachments) so you can decide what to log.
- **View a downloaded file → the `Read` tool** on the local path. `Read`
  renders images natively, so never route an image through the MCP just to look
  at it — download it, then `Read` the file. Cheaper and it's saved anyway.

## Download (primary path)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_attachments.py" <ticket> <NNN> [--comment-id <id>]
```

- `<NNN>` is the entry number the files belong to (they're prefixed `NNN_`).
- `--comment-id <id>` limits the download to one comment (use it when logging a
  single specific update). Omit it to scan the whole thread (e.g. a fresh
  ticket) — either way it only grabs what's **new** (idempotent via the
  `received/.zd_attachments.json` ledger).
- The helper authenticates against the ia-tooling `.env`
  (`$IA_TOOLING_ROOT/.env`), routes each file to
  `received/<comment-date>/NNN_<name>`, and prints JSON:
  `{"downloaded": [{"path", "file_name", "comment_id", …}], "skipped": N}`.
- **Use the `path` values from that JSON verbatim** for the timeline's
  attachment links. The helper lowercases and normalises filenames and adds the
  `NNN_` prefix, so the on-disk name differs from the original Zendesk filename
  — don't reconstruct links from the original name or they won't resolve.

## Which entry owns an attachment

An attachment belongs to the entry for the comment it arrived on — so it's
downloaded (and `NNN_`-prefixed) under that entry's number, not lumped elsewhere.

This is why `/new-ticket` scopes the opening fetch with `--comment-id <opening>`:
`[001]` is only the opening message, so only its attachments belong there. If
you instead scanned the whole thread at ticket-creation time, every attachment
would be tagged `001_` **and recorded in the idempotency ledger**
(`received/.zd_attachments.json`) — so when `/log-updates` later logs those
comments it would find them already downloaded, skip them, and the later entries
would lose their attachment links. Let each comment's attachments be pulled, under
their own entry number, by the command that logs that comment.

## Fallback (stack down / no creds / MCP unavailable)

If `fetch_attachments.py` errors, move files in manually — ask the user for the
source path (or "drag them into ~/Downloads now") and run, per file:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/attach.py" <ticket> <NNN> <source>
```

It does the same date routing and `NNN_` renaming and prints the destination
path — use that one for the link. All files (screenshots, logs, configs) go to
the same date folder; no per-type split.

## Reading what you downloaded

- **Images:** `Read` the local file and capture a one-line description for the
  entry's attachments block.
- **Text logs ≤ 1 MB:** read and extract the relevant excerpt.
- **Larger logs:** read only the first/last N lines or grep for stack traces —
  do **not** paste the full content into the timeline. Link the file instead.
