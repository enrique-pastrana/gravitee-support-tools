---
description: Spin up, list, or tear down a local Gravitee stack (APIM / AM) via the gravitee-stacker MCP server, ticket-scoped and logged to the timeline.
argument-hint: <up|list|down|clean> [apim|am][@version] [ticket]
---

Drive local Gravitee stacks by **orchestrating the `gravitee-stacker` MCP
server** — never reimplement docker-compose. `$ARGUMENTS` is free-form intent
(verb + product + version + ticket); default verb is **up**. **The user drives;
never bring a stack up or tear one down without confirmation** — stacks pull
images and consume RAM, and teardown with volumes wipes data.

**Conventions**
- Ticket data → workspace `$TICKETS_ROOT` (default `~/TICKETS`).
- Scripts/templates/references → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files
  into the workspace.
- gravitee-stacker is an **external** MCP server, wired in `.mcp.json` via
  `${GRAVITEE_STACKER_BIN}`. Its tools appear as `apim_*` / `am_*` / `stack_*`.
- **Instance = ticket number** by default → per-ticket isolation (own compose
  project, volumes, network, auto port band) and obvious ownership. Standalone
  ("a stack for my own testing", no ticket) → let the user name the instance.

## Steps

1. **Preflight.** If the gravitee-stacker tools aren't available, the server
   didn't load — run and relay:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/stack-preflight"
   ```
   (diagnoses a missing `GRAVITEE_STACKER_BIN`, Docker down, or absent license;
   MCP servers load only at launch, so a fix means relaunching Claude). If the
   tools **are** there, call `doctor` for a Docker + license readiness check.

2. **Resolve intent + ticket.** Parse verb (`up`/`list`/`down`/`clean`),
   product (`apim`/`am`), version (pin like `4.12.7`, or `latest`), and any
   variant (`kafka`) / features (`prometheus`, `redis-rate-limit`, …). For a
   ticket-scoped action, resolve the ticket via
   `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md` (chain **arguments >
   current > cwd > ask**); an explicit number is a one-off (doesn't move the
   pointer). Default the **instance to that ticket number**. Standalone → ask for
   an instance name; skip the ticket write-guards and step 5.

3. **Plan + confirm (up).** Preview without side effects:
   ```
   stack_preflight(version=…, instance=…)   # resolves version, computes ports, flags conflicts
   ```
   Show the resolved version, ports/URLs, license source, and any conflict.
   **Confirm before bringing up.** On `port_conflict`, report it and stop —
   never auto-down another instance.

4. **Bring up.** `apim_up` / `am_up` with the resolved args (pass `license=` only
   if the user points at a specific file — otherwise let gravitee-stacker resolve
   `APIM_LICENSE` → `~/.gravitee/license.key` → OSS). Then block on
   `apim_wait` / `am_wait` until healthy. Report the URLs and **which license
   source was used**. If an **EE-only** capability was requested (`kafka`,
   `alert-engine`, Debug mode) but it resolved to **OSS**, warn and point at
   `~/.gravitee/license.key` / `APIM_LICENSE`.

5. **Log to the timeline (ticket-scoped only).** Record the stack via the
   `Local stack` block of `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`
   (🛠️): product@version, instance, key URLs, license mode.
   - **first stack action this session** → new entry `[NNN]`
     (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>` → prints
     `NNN`, refreshes `updated_at`)
   - **later lifecycle change** (torn down, version switched) → **append to that
     same entry's `<details>`** + `bump_entry.py <ticket> --touch` (no bump)
   - `/stack` doesn't change `status` (Zendesk-anchored) → **no `set_meta`/`render_header`.**

6. **list.** `apim_list` / `am_list` → tracked instances (version, ports, health)
   plus `other_stacks_on_apim_ports`. Read values from the tools — don't guess.

7. **down / clean.**
   - `down` → `apim_down` / `am_down` for the resolved instance (volumes kept by
     default). Wiping data (`volumes=true`, e.g. for a clean version downgrade)
     only on **explicit** user confirmation.
   - `clean` (no bulk-prune tool exists) → `apim_list` + `am_list`, show the
     tracked instances, ask **which to retire** (or "all stopped / resolved-ticket
     ones"), then `*_down` each. `volumes=true` per instance only when the user
     confirms the data loss.
   - Ticket-scoped teardown → append the lifecycle line to the ticket's 🛠️ entry
     (`--touch`).

## Don'ts

- **Never bring up or tear down without confirmation** — stacks pull images /
  consume RAM; teardown with `volumes=true` destroys data.
- **Don't reimplement docker-compose** — orchestrate gravitee-stacker's tools only.
- **Don't fabricate versions, ports, or URLs** — read them from `stack_preflight`
  / `*_list` / `*_status`.
- **Don't run EE-only variants silently in OSS** — warn when no license resolves.
- No hand-editing `metadata.json` — use `bump_entry.py` (`--touch` when appending).
