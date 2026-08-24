# Reference: resolving which ticket a command acts on

Every command acts on exactly one ticket. This is the shared procedure for
deciding which — so all commands behave the same and none writes to the wrong
ticket silently. Commands point here instead of repeating it. Paths assume
`${CLAUDE_PLUGIN_ROOT}` (plugin) and `$TICKETS_ROOT` (data).

## The current ticket

The one a command uses when no number is passed. A one-line pointer at
`$TICKETS_ROOT/.current-ticket` (bare number) — so it persists across sessions
and independently of the shell's cwd. Read/write it **only** through the helper,
never by hand:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/current_ticket.py" get          # print it, or nothing
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/current_ticket.py" set <number> # point at <number>
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/current_ticket.py" clear        # forget it
```

## Resolution chain (first match wins)

1. **`$ARGUMENTS`** — an explicit number always wins. It's a **one-off**: use it
   for this run, but do **not** change the pointer (see guard 1).
2. **Current ticket** — `current_ticket.py get`. Use it if set.
3. **cwd** — if the shell sits in a ticket folder
   (`$TICKETS_ROOT/<thousand>/<number>/`, e.g. `16000/16575/`, or flat
   `$TICKETS_ROOT/<number>/` for alphanumeric ids), use that number.
4. **Ask** the user.

Resolve the bare number to its folder (handles the thousand-bucket layout):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
```

**Always state which ticket you resolved and how**, one line, before acting —
`Ticket: 17337 (current)` / `(from arguments)` / `(from cwd)`. The visible line
is what lets the user catch a wrong ticket at a glance; never act silently.

## Mismatch guards — check before you WRITE

Read-only commands (`/status`) skip these. Writers (`/new-ticket`,
`/log-updates`, `/reply`) must run them:

- **Explicit ≠ current** — `$ARGUMENTS` differs from the current ticket. The
  explicit number still wins, but **stop and get a yes** before writing: *"About
  to write to `<args>`, but the current ticket is `<current>`. Continue?"* A real
  gate, not a note you sail past — it matters most for `/log-updates`, which
  otherwise writes with no natural pause. Don't move the pointer either way.
- **cwd ≠ current** — shell is in one ticket's folder, pointer points elsewhere.
  Don't guess — ask which one.
- **Resolved ticket doesn't exist** — for commands needing an existing ticket
  (`/reply`, `/log-updates`, `/status`), if the folder's missing, stop and offer
  `/new-ticket <number>` instead of failing deep in a later step.
- **Content doesn't match** (best-effort) — before logging, sanity-check the
  material against `<dir>/metadata.json` (customer, subject, product). Clearly a
  different customer/ticket → stop and flag it, don't write it into the wrong
  timeline.

## Setting the current ticket

Write the pointer (`current_ticket.py set <number>`) when:

- **`/new-ticket`** creates a ticket → set it.
- the **user says they're working on a ticket** ("let's work on 17337", "switch
  to 16575", "trabajamos en el ticket 17337") → set it.
  - That ticket **has no folder yet** → don't point at nothing: say so and offer
    to create it (`/new-ticket <number>`) or set the pointer anyway. User picks.

Do **not** move the pointer just because a command got an explicit number
(guard 1) — that's a one-off, not a switch.
