# Reference: resolving which ticket a command acts on

Every command acts on exactly one ticket. This is the shared procedure for
deciding which — so all commands behave the same and none writes to the wrong
ticket silently. Commands point here instead of repeating it. Paths assume
`${CLAUDE_PLUGIN_ROOT}` (plugin) and `$TICKETS_ROOT` (data).

## The current ticket = the window's working directory

Each window works on **one** ticket, and the signal for which one is the shell's
**current directory**: when the shell sits inside a ticket's folder, that's the
ticket this window is on. This is per-window by construction — two windows have
two independent cwds, so working two tickets side by side never crosses wires.
There is no shared state file; the cwd *is* the state.

For this to hold, **the session's working directory must contain `$TICKETS_ROOT`**
— open the editor/workspace at `$TICKETS_ROOT`, launch the window from there, or
add it with `/add-dir "$TICKETS_ROOT"`. Otherwise the sandbox resets the cwd out of
the ticket folder after each command and the signal is lost.

## Resolution chain (first match wins)

1. **`$ARGUMENTS`** — an explicit number always wins. It's a **one-off**: use it
   for this run, but do **not** move the window (don't `cd`) — see guard 1.
2. **cwd** — if the shell sits in a ticket folder
   (`$TICKETS_ROOT/<thousand>/<number>/`, e.g. `18000/18180/`, or flat
   `$TICKETS_ROOT/<number>/` for alphanumeric ids), use that number. This is the
   normal per-window signal.
3. **Ask** the user — no shortcuts. If neither above matched, ask for the number;
   do **not** infer it from a "sole candidate" because the workspace happens to
   hold only one ticket. That heuristic silently breaks the moment a second ticket
   exists, and it's exactly the kind of wrong-ticket guess this chain prevents.

Resolve the bare number to its folder (handles the thousand-bucket layout):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
```

**Always state which ticket you resolved and how**, one line, before acting —
`Ticket: 18180 (from cwd)` / `(from arguments)`. The visible line is what lets the
user catch a wrong ticket at a glance; never act silently.

## Switching this window to a ticket

When the user says they're working on a ticket ("let's work on 18180", "switch to
16575", "trabajamos en el ticket 18180") — or when `/new-ticket` creates one —
**move the window into that ticket's folder** so cwd carries the state:

```bash
cd "$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>)"
```

- That ticket **has no folder yet** → don't `cd` into nothing: say so and offer to
  create it (`/new-ticket <number>`).
- If the `cd` gets reset (shell bounces back out of the folder), `$TICKETS_ROOT`
  isn't a working directory of this session — tell the user to open the workspace
  at `$TICKETS_ROOT` or run `/add-dir "$TICKETS_ROOT"`, then retry.

## Mismatch guards — check before you WRITE

Read-only commands (`/status`) skip these. Writers (`/new-ticket`,
`/log-updates`, `/reply`) must run them:

- **Explicit ≠ cwd** — `$ARGUMENTS` names one ticket but the shell sits in a
  different ticket's folder. The explicit number still wins for this run, but
  **stop and get a yes** before writing: *"About to write to `<args>`, but this
  window is in `<cwd-ticket>`. Continue?"* A real gate, not a note you sail past —
  it matters most for `/log-updates`, which otherwise writes with no natural
  pause. Don't move the window either way.
- **Resolved ticket doesn't exist** — for commands needing an existing ticket
  (`/reply`, `/log-updates`, `/status`), if the folder's missing, stop and offer
  `/new-ticket <number>` instead of failing deep in a later step.
- **Content doesn't match** (best-effort) — before logging, sanity-check the
  material against `<dir>/metadata.json` (customer, subject, product). Clearly a
  different customer/ticket → stop and flag it, don't write it into the wrong
  timeline.
