---
description: Remove a ticket folder entirely (rm -rf). Shows a recap and asks for confirmation first.
argument-hint: <ticket-number>
---

Remove a ticket folder from `$TICKETS_ROOT`. **This is destructive and
irreversible** — `rm -rf` of the whole folder (timeline, metadata, attachments,
reproduction, everything). Paths: `${CLAUDE_PLUGIN_ROOT}` (plugin), `$TICKETS_ROOT`
(data).

## Steps

1. **Resolve the ticket** — follow
   `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`: `$ARGUMENTS` > cwd > ask.
   A destructive delete needs a clear target, so if nothing resolves, **ask** — never
   guess. Print the resolution line (`Ticket: <id> (from arguments|from cwd)`) before
   anything else.
2. **Resolve the folder** —
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>`. If the folder
   **doesn't exist**, tell the user and **stop** (nothing to remove).
3. **Safety guard** — refuse to delete unless the resolved path is a real ticket
   folder **inside** `$TICKETS_ROOT`. Stop if it is `$TICKETS_ROOT` itself, a bare
   thousand-bucket (`$TICKETS_ROOT/16000`), or anything resolving outside
   `$TICKETS_ROOT`. Never `rm -rf` a guessed flat path — only the resolved one.
4. **Show a recap** of what will be deleted, so the user sees the weight of it:
   - From `<ticket>/metadata.json`: `subject`, `customer`, `status`.
   - `grep -c "^### \[" <ticket>/timeline.md` — entry count.
   - `find <ticket>/received -type f ! -name '.zd_attachments.json' 2>/dev/null | wc -l`
     — attachment count; note `reproduction/` if present.
   - `ls -la <ticket>` — the raw contents.
5. **Confirm** via **AskUserQuestion** (destructive → an explicit gate, never assume):
   - **"Yes, delete"** → proceed.
   - **"Cancel"** → stop, do nothing, say so.
6. **On confirm** — `rm -rf` the **resolved path** (step 2). Then:
   - If the shell's cwd was **inside** the deleted folder, `cd "$TICKETS_ROOT"` so the
     window isn't stranded in a directory that no longer exists.
   - Leave the (now maybe empty) thousand-bucket in place — don't prune it.
   - Confirm the deletion in **one line** (`Removed <id> (<N> entries, <M> files).`).

## Don'ts

- Don't delete without showing the recap and getting an explicit AskUserQuestion yes.
- Don't accept a target that resolves outside `$TICKETS_ROOT`, or the root / a bucket
  container itself.
- Don't prune the thousand-bucket folder, even if it's left empty.
- Don't try to "undo" — there is no undo; the confirmation gate is the only safeguard.
