# Reference: resolving which ticket a command acts on

Every command works on exactly one ticket. This is the shared procedure for
deciding which — so all commands behave the same and none of them ever writes to
the wrong ticket silently. Commands point here instead of repeating it. Paths
below assume `${CLAUDE_PLUGIN_ROOT}` (the plugin) and `$TICKETS_ROOT` (the data).

## The current ticket

The "current ticket" is the one a command uses when no number is passed. It's a
one-line pointer at `$TICKETS_ROOT/.current-ticket` (the bare number), so it
persists across sessions and independently of the shell's cwd. Read/write it
**only** through the helper — never hand-edit the file:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/current_ticket.py" get          # print it, or nothing
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/current_ticket.py" set <number> # point at <number>
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/current_ticket.py" clear        # forget it
```

## Resolution chain (first match wins)

1. **`$ARGUMENTS`** — an explicit number always wins. It's a **one-off**: use it
   for this run, but do **not** change the current ticket (see guard 1).
2. **Current ticket** — `current_ticket.py get`. Use it if one is set.
3. **cwd** — if the shell is inside a ticket folder
   (`$TICKETS_ROOT/<thousand>/<number>/`, e.g. `16000/16575/`, or a flat
   `$TICKETS_ROOT/<number>/` for alphanumeric ids), use that number.
4. **Ask** the user.

Resolve the bare number to its folder with the shared helper (it handles the
thousand-bucket layout):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
```

**Always state which ticket you resolved and how**, in one line, before acting —
e.g. `Ticket: 17337 (current)` / `(from arguments)` / `(from cwd)`. Never act
silently; a visible line is what lets the user catch a wrong ticket at a glance.

## Mismatch guards — check before you WRITE

Read-only commands (`/status`) can skip these. Commands that write
(`/new-ticket`, `/log-updates`, `/reply`) must run them:

- **Explicit ≠ current** — `$ARGUMENTS` is set and differs from the current
  ticket. The explicit number still wins, but say so and confirm before writing:
  *"About to write to `<args>`, but the current ticket is `<current>`.
  Continue?"* Don't overwrite the pointer.
- **cwd ≠ current** — the shell sits in one ticket's folder but the current
  ticket points elsewhere. Don't guess — ask which one the user means.
- **Resolved ticket doesn't exist** — for commands that need an existing ticket
  (`/reply`, `/log-updates`, `/status`), if the folder isn't there, stop and
  offer `/new-ticket <number>` instead of failing deep in a later step.
- **Content doesn't match** (best-effort) — before logging an entry or a reply,
  sanity-check the material against `<dir>/metadata.json` (customer, subject,
  product). If it clearly belongs to a different customer/ticket, stop and flag
  it rather than writing it into the wrong timeline.

## Setting the current ticket

Write the pointer (`current_ticket.py set <number>`) when:

- **`/new-ticket`** creates a ticket → set it to that number.
- the **user says they're working on a ticket** — "let's work on 17337",
  "switch to 16575", "trabajamos en el ticket 17337" → set it.

Do **not** move the pointer just because a command got an explicit number
(guard 1) — that's a one-off, not a switch.
