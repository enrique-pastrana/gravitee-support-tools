---
description: Start and verify the ia-tooling stack (Docker + Ollama + vectordb) needed for the zendesk/vectordb MCP servers.
---

You are starting the local `ia-tooling` stack so the `zendesk` and `vectordb`
MCP servers work. This just wraps the bundled `tickets-up` script — the single
entry point every other command points at when it detects the stack is down.

## What the script does

Run in order, idempotent (if something is already up it just verifies):

1. Checks the **Docker** daemon responds.
2. Starts **Ollama** (embeddings backend, via `brew services`) if it isn't up.
   Non-fatal: if it won't start, `rag_search` still works but with poorer
   results.
3. Brings up the **ia-tooling stack** (`docker compose up -d` in
   `$IA_TOOLING_ROOT`): postgres + vectordb-api + the MCP adapters.
4. Sets the stack's containers to **restart automatically** after a Docker/Mac
   reboot (applied with `docker update`, so the company `ia-tooling` repo is
   never modified).
5. Waits for **vectordb-api** to be healthy and prints its `backend` and
   document count.

The script locates the stack through `$IA_TOOLING_ROOT` (default
`~/ia-tooling`) — the same variable the plugin's `.mcp.json` uses. It lives in
the plugin, not in `ia-tooling`, on purpose: a `git clean` in the company repo
must not take it away.

> **macOS-specific.** It assumes Docker Desktop and Ollama installed via
> Homebrew — the support team's setup.

## Steps

1. **Run** the script and show its output:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/tickets-up"
   ```

2. **Report** the result:
   - Ends with `✓ Ready to work on tickets.` → stack is up; mention the
     `backend` and `documents` count from the vectordb health line.
   - `✗ Docker is not responding` → **the one thing the script can't fix.**
     Docker Desktop isn't running and the script won't start it. Tell the user
     to open Docker Desktop and rerun `/tickets-up`.
   - `✗ vectordb API did not respond` → stack came up but the API is unhealthy;
     surface the diagnostic line (`cd "$IA_TOOLING_ROOT" && docker compose ps`)
     as-is.
   - Any other failure → surface the script's diagnostic line verbatim.

## When commands hit a down stack (fallback)

Other commands don't try to recover on their own — they point back here:

- **Recovery is always `/tickets-up`.** When a command fails with
  "vectordb unreachable" / a Zendesk connection error (usually exit code 2),
  the fix is to run this command, then retry the original one.
- **Degraded mode depends on the command:**
  - `new-ticket`, `customer` → can fall back to a **manual flow** (paste the
    Zendesk content, move attachments by hand) without the stack.
  - `index-*`, `close`, `kb-shared` → **no manual mode**; bring the stack up and
    re-index later.
  - `sync` → does **not** fall back; it stops and points here.

## Don'ts

- Don't try to start Docker Desktop yourself or work around a down daemon.
- Don't modify the script or the stack config.
- Keep it short — this is a one-shot "is it up?" action, not a report.
