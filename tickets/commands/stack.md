---
description: Spin up, list, or tear down a local Gravitee stack — standalone APIM / AM, or the Gamma demo stack — via the gravitee-stacker MCP server, ticket-scoped and logged to the timeline.
argument-hint: <up|list|down|clean|setup> [apim|am|gamma][@version] [ticket]
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
- **Products differ in shape:**
  - **`apim` / `am`** — standalone and **multi-instance**. **Instance = ticket
    number** by default → per-ticket isolation (own compose project, volumes,
    network, auto port band) and obvious ownership. Standalone ("a stack for my
    own testing", no ticket) → let the user name the instance.
  - **`gamma`** — the Gamma demo stack (`stack_*` tools): a **shared singleton**
    on **canonical ports**, with nginx host-routing on `:80`
    (`gamma.localhost` / `apim.localhost` / `portal.localhost` / `am.localhost`).
    It is **not** multi-instance and **not** ticket-isolated — there is only ever
    one, no instance name, and ports can't be remapped. It needs extra setup:
    the demo-stack repo at `GAMMA_STACK_DIR`, an ACR login, and a license inside
    the repo. Ticket link is **optional** (a logging courtesy, step 5).

## Steps

1. **Preflight.** If the gravitee-stacker tools aren't available, the server
   didn't load — run and relay:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/stack-preflight"
   ```
   (diagnoses a missing `GRAVITEE_STACKER_BIN`, Docker down, or absent license;
   MCP servers load only at launch, so a fix means relaunching Claude). If the
   tools **are** there, call `doctor` for a Docker + license readiness check.
   For **gamma**, read `doctor`'s **`gamma_stack`** block (`ready`,
   `stack_dir_found`, `needs`, `next_steps`) — it needs `GAMMA_STACK_DIR` + ACR
   login + license. If it isn't `ready`, relay `next_steps` and **stop**; don't
   attempt `stack_up`. (`stack_preflight` only covers `apim`/`am`, not gamma.)

2. **Resolve intent + ticket.** Parse verb (`up`/`list`/`down`/`clean`, plus
   `setup` for gamma), product (`apim`/`am`/`gamma`), version (pin like `4.12.7`,
   or `latest`), and any variant (`kafka`) / features (`prometheus`,
   `redis-rate-limit`, …). For a ticket-scoped action, resolve the ticket via
   `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md` (chain **arguments >
   current > cwd > ask**); an explicit number is a one-off (doesn't move the
   pointer).
   - **apim / am:** default the **instance to that ticket number**. Standalone →
     ask for an instance name; skip the ticket write-guards and step 5.
   - **gamma:** singleton — **no instance, no version, no per-ticket scoping.**
     Only when a ticket is already in context, offer the optional 🛠️ log (step 5);
     never prompt for a ticket just to bring Gamma up.

3. **Plan + confirm (up).** Preview without side effects, then **confirm before
   bringing up** (on any `port_conflict`, report the busy ports and stop — never
   auto-down another stack):
   - **apim / am:**
     ```
     stack_preflight(kind="apim"|"am", version=…, variant=…)   # resolves version, computes canonical ports, flags conflicts
     ```
     Show the resolved version, ports/URLs, license source, and any conflict.
   - **gamma:** no preview tool beyond step 1's `doctor`. State plainly that this
     brings up the **shared** Gamma stack on canonical ports (`:80` host-routing),
     that setup can take several minutes, and that it will replace any Gamma stack
     already running. Confirm.

4. **Bring up.**
   - **apim / am:** `apim_up` / `am_up` with the resolved args (pass `license=`
     only if the user points at a specific file — otherwise let gravitee-stacker
     resolve `APIM_LICENSE` → `~/.gravitee/license.key` → OSS). These run
     **background/non-blocking**, so **poll `apim_status` / `am_status` until
     `overall` is `healthy`** (report progress; a non-zero exit → `failed`, relay
     the log tail).
   - **gamma:** run the chain — `stack_up(pull=true)` (background) → **poll
     `stack_status` until `overall: healthy`** (`starting` = still pulling/health-
     polling; `failed`/`partial` → relay `problems` + `stack_logs(<service>)` and
     stop) → **confirm, then `stack_setup`** (foreground `run.sh setup`, bootstraps
     AM + APIM + SPIRE; can take minutes — on `timeout` relay the manual re-run
     command it returns). Note the optional `stack_install_daemon` step (host Edge
     Daemon on `:443`; it's a manual sudo command the tool only *prints*) if the
     user needs host `:443` / DNS routing.

   **Always print an Access URLs table**, built from the `urls`/`ports` the tools
   return — never fabricate a port or host.
   - **APIM** returns a role→host-port map; render:

     | Role | URL |
     |---|---|
     | Console | `http://localhost:<console>` (admin/admin) |
     | Portal | `http://localhost:<portal>` |
     | Management API | `http://localhost:<mgmt>/management` |
     | Gateway | `http://localhost:<gateway>` |

     plus any feature URL the tool lists (e.g. Prometheus `http://localhost:<prometheus>`).
   - **AM** already returns full URL strings (console `…/am/ui/ (admin/adminadmin)`,
     management `…/am/management/`, gateway `…/am/`) — present them as-is.
   - **gamma** → read from **`stack_ports`**: the host-routed UIs
     (`http://gamma.localhost`, `http://apim.localhost`, `http://portal.localhost`,
     `http://am.localhost`) plus the direct backend ports it lists.

   Also report **which license source was used**. If an **EE-only** capability
   was requested (`kafka`, `alert-engine`, Debug mode) but it resolved to **OSS**,
   warn and point at `~/.gravitee/license.key` / `APIM_LICENSE`.

5. **Log to the timeline (ticket-scoped only).** Record the stack via the
   `Local stack` block of `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`
   (🛠️): product@version, instance, key URLs, license mode. For **gamma**, only
   when a ticket is already in context and the user opts in — note it's the
   **shared** Gamma demo stack (no instance; canonical host-routed URLs).
   - **first stack action this session** → new entry `[NNN]`
     (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>` → prints
     `NNN`, refreshes `updated_at`)
   - **later lifecycle change** (torn down, version switched) → **append to that
     same entry's `<details>`** + `bump_entry.py <ticket> --touch` (no bump)
   - `/stack` doesn't change `status` (Zendesk-anchored) → **no `set_meta`/`render_header`.**

6. **list.**
   - **apim / am:** `apim_list` / `am_list` → tracked instances (version, ports,
     health) plus `other_stacks_on_apim_ports`.
   - **gamma:** `stack_status` (overall + per-service health) + `stack_ports`
     (canonical URLs). There's only ever one Gamma stack.

   Read values from the tools — don't guess.

7. **down / clean.**
   - **apim / am:**
     - `down` → `apim_down` / `am_down` for the resolved instance (volumes kept by
       default). Wiping data (`volumes=true`, e.g. for a clean version downgrade)
       only on **explicit** user confirmation.
     - `clean` (no bulk-prune tool exists) → `apim_list` + `am_list`, show the
       tracked instances, ask **which to retire** (or "all stopped / resolved-
       ticket ones"), then `*_down` each. `volumes=true` per instance only when
       the user confirms the data loss.
   - **gamma:** `down` → `stack_down` (tears the whole singleton down). `clean` is
     **N/A** for gamma (nothing per-instance to prune) — treat it as `down`.
   - Ticket-scoped teardown → append the lifecycle line to the ticket's 🛠️ entry
     (`--touch`).

8. **setup (gamma only).** `/stack setup gamma` runs **`stack_setup`** against an
   already-up Gamma stack (re-bootstrap AM + APIM + SPIRE without a fresh `up`).
   Not a verb for `apim`/`am` — for those, bootstrapping happens inside `up`.

## Don'ts

- **Never bring up or tear down without confirmation** — stacks pull images /
  consume RAM; teardown with `volumes=true` destroys data.
- **Don't reimplement docker-compose** — orchestrate gravitee-stacker's tools only.
- **Don't fabricate versions, ports, or URLs** — read them from `stack_preflight`
  / `*_list` / `*_status` / `stack_ports`.
- **Don't block on non-existent `*_wait` tools** — `apim_up` / `am_up` / `stack_up`
  are background; poll `apim_status` / `am_status` / `stack_status` until healthy.
- **Don't remap or double-run Gamma** — it's a canonical-port singleton; on
  `port_conflict` relay the busy ports and stop, and never expect a ticket-scoped
  instance name for it.
- **Don't run EE-only variants silently in OSS** — warn when no license resolves.
- No hand-editing `metadata.json` — use `bump_entry.py` (`--touch` when appending).
