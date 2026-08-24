# Reference: handling ticket attachments

Shared procedure for pulling attachments out of a Zendesk ticket into the
ticket's `received/` folder. Commands (`/log-updates`, `/new-ticket`) point here
instead of repeating it. Paths assume `${CLAUDE_PLUGIN_ROOT}` (plugin) and
`$TICKETS_ROOT` (data).

## Division of labour: script vs. MCP

The `zendesk` MCP *can* return attachments (`zendesk_get_attachment`), but hands
them back **as base64 in the model context** — token-expensive, and it doesn't
write to disk. So keep the jobs separate:

- **Download → always the script** (`fetch_attachments.py`): writes straight to
  `received/`, keeps bytes out of context, idempotent, normalises names. This is
  what actually persists an attachment.
- **Explore → the MCP** (`zendesk_get_ticket_with_attachments` /
  `zendesk_get_ticket_attachments`): only to *see what a ticket contains* (thread
  + attachment list) so you can decide what to log.
- **View a downloaded file → the `Read` tool** on the local path. `Read` renders
  images natively — never route an image through the MCP just to look; download,
  then `Read`. Cheaper, and it's saved anyway.

## Download (primary path)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_attachments.py" <ticket> <NNN> [--comment-id <id>]
```

- `<NNN>` = the entry number the files belong to (prefixed `NNN_`).
- `--comment-id <id>` limits the download to one comment (use when logging a
  single update). Omit to scan the whole thread (e.g. a fresh ticket). Either way
  it only grabs what's **new** (idempotent via `received/.zd_attachments.json`).
- Authenticates against the ia-tooling `.env` (`$IA_TOOLING_ROOT/.env`), routes
  each file to `received/<comment-date>/NNN_<name>`, prints JSON:
  `{"downloaded": [{"path", "file_name", "comment_id", …}], "skipped": N}`.
- **Use the `path` values from that JSON verbatim** for timeline links. The
  helper lowercases, normalises, and adds the `NNN_` prefix, so the on-disk name
  differs from the Zendesk filename — reconstruct a link from the original name
  and it won't resolve.

## Which entry owns an attachment

An attachment belongs to the entry for the comment it arrived on — downloaded
(and `NNN_`-prefixed) under that entry's number.

This is why `/new-ticket` scopes the opening fetch with `--comment-id <opening>`:
`[001]` is only the opening message. Scan the whole thread at creation time
instead and every attachment gets tagged `001_` **and recorded in the ledger**
(`received/.zd_attachments.json`) — so when `/log-updates` later logs those
comments it finds them already downloaded, skips them, and the later entries lose
their links. Let each comment's attachments be pulled under their own entry, by
the command that logs that comment.

## Fallback (stack down / no creds / MCP unavailable)

If `fetch_attachments.py` errors, move files in manually — ask the user for the
source path (or "drag them into ~/Downloads now"), then per file:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/attach.py" <ticket> <NNN> <source>
```

Same date routing and `NNN_` renaming; prints the destination path — use that for
the link. All files (screenshots, logs, configs) go to the same date folder; no
per-type split.

## Reading what you downloaded

- **Images:** `Read` the local file; capture a one-line description for the entry.
- **Text logs ≤ 1 MB:** read, extract the relevant excerpt.
- **Larger logs:** read only first/last N lines or grep for stack traces — never
  paste full content into the timeline; link the file.
