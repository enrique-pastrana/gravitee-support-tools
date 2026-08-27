---
description: Spin up, list, or tear down a local Gravitee stack — standalone APIM / AM via the gravitee-stacker MCP server, or the version-selectable Gamma singleton via its official docker-compose — ticket-scoped and logged to the timeline.
argument-hint: <up|list|down|clean> [apim|am|gamma][@version] [ticket]
---

Drive local Gravitee stacks. `$ARGUMENTS` = free-form intent (verb + product +
version + ticket); default verb **up**. **The user drives — never bring a stack up
or tear one down without confirmation** (images + RAM; teardown with volumes wipes
data).

**Product matrix** — the single source for how the two back-ends differ:

| | **apim / am** | **gamma** |
|---|---|---|
| Back-end | `gravitee-stacker` MCP (`apim_*` / `am_*`) | `docker compose` directly, on the plugin's official compose |
| Shape | multi-instance | **singleton** — one at a time |
| Instance | ticket number (standalone → user-named) | none |
| Ports | auto band (stacker computes) | canonical **8082–8086**, don't remap |
| Compose project | per-instance | `gravitee-gamma` |
| Ticket scope | yes — write-guards + log (step 5) | optional log only (step 5) |
| Version | `@version` or `latest` | `@version`, default `4.12`, **needs 4.12+** |

Gamma is the **one deliberate exception** to "don't reimplement compose": it isn't
in gravitee-stacker, so `/stack` runs the official public-image compose itself. Full
why + license setup → `${CLAUDE_PLUGIN_ROOT}/references/gamma-stack.md`.

**License cascade** (all products, resolved once at plan time):
explicit `license=<path>` → `$APIM_LICENSE` → `~/.gravitee/license.key` → none = OSS.

**Conventions**
- Ticket data → `$TICKETS_ROOT` (default `~/TICKETS`). Plugin files → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files into the workspace.
- gravitee-stacker is an **external** MCP server wired in `.mcp.json` via `${GRAVITEE_STACKER_BIN}`.
- Gamma compose: base `${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.yml`, license override `${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.license.yml`.

## Steps

1. **Preflight.**
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/stack-preflight" [apim|am|gamma]
   ```
   - **apim / am:** if the `apim_*`/`am_*` tools are missing the server didn't load —
     the script diagnoses a missing `GRAVITEE_STACKER_BIN`, Docker down, or absent
     license (MCP servers load only at launch → a fix means relaunching Claude). If
     the tools **are** there, call `doctor` for Docker + license readiness.
   - **gamma:** the script checks Docker up, whether a license resolves (cascade
     above; none = OSS, modules dormant), and whether ports **8082–8086** are free.
     No gravitee-stacker involvement.

   Relay what it reports. On a port conflict → stop; never tear down whatever holds them.

2. **Resolve intent + ticket.** Parse verb, product, version, and for apim/am any
   variant (`kafka`) / features (`prometheus`, `redis-rate-limit`, …). For a
   ticket-scoped action, resolve the ticket via
   `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md` (chain
   **arguments > current > cwd > ask**; an explicit number is a one-off, doesn't move
   the pointer).
   - **apim / am:** default the **instance to the ticket number**. Standalone (own
     testing, no ticket) → ask for an instance name; skip the write-guards and step 5.
   - **gamma:** singleton — no instance, no per-ticket scoping. Parse the version
     (`gamma@4.13` → `GAMMA_VERSION=4.13`). Offer the optional log (step 5) only when
     a ticket is already in context; never prompt for one just to run Gamma.

3. **Plan + confirm (up).** Preview with **no side effects**, then confirm. On any
   port conflict, report the busy ports and stop — never auto-down another stack.
   - **apim / am:**
     ```
     stack_preflight(kind="apim"|"am", version=…, variant=…)   # resolves version, computes ports, flags conflicts
     ```
     Show resolved version, ports/URLs, license source, any conflict.
   - **gamma:** resolve the license (cascade above), then validate the compose:
     ```bash
     GAMMA_VERSION=<version> docker compose \
       -f "${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.yml" \
       -p gravitee-gamma config >/dev/null   # add the license -f (step 4) when one resolved
     ```
     State plainly: shared singleton on 8082–8086, resolved **version** and **license
     mode** (EE vs OSS), that pulling images can take minutes, and that it **replaces
     any Gamma already running**. Confirm.

4. **Bring up.** Both back-ends are **background** — never block on a `*_wait` tool;
   poll until ready.
   - **apim / am:** `apim_up` / `am_up` with the resolved args (pass `license=` only
     if the user points at a specific file; otherwise let stacker resolve the cascade).
     **Poll `apim_status` / `am_status` until `overall` = `healthy`** (report progress;
     non-zero exit → `failed`, relay the log tail).
   - **gamma:** run the official compose under project `gravitee-gamma`. Add the
     license override **only** when a license resolved:
     ```bash
     # EE (license resolved):
     GAMMA_VERSION=<version> GAMMA_LICENSE_FILE=<resolved-path> docker compose \
       -f "${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.yml" \
       -f "${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.license.yml" \
       -p gravitee-gamma up -d
     # OSS (no license): drop the second -f and GAMMA_LICENSE_FILE.
     ```
     `up -d` returns before images finish pulling. **Poll
     `docker compose -p gravitee-gamma ps` until every service is `Up`**, then confirm
     the management API answers:
     ```bash
     curl -sf http://localhost:8083/management/organizations/DEFAULT/console >/dev/null && echo READY
     ```
     On a stuck/failed service relay `docker compose -p gravitee-gamma logs <service>`
     and stop. If a license was mounted, **verify activation**:
     ```bash
     docker logs gamma_management_api 2>&1 | grep -c "detected but not activated"   # want 0
     ```
     Non-zero with a license = the mounted file is base64 text, not raw binary → point
     at the `base64 -d` fix in `references/gamma-stack.md`.

   **Then always print an Access URLs table** — the same two-column `Role | URL` shape
   for every product (credentials inline), read from what the tools/compose expose;
   **never fabricate a port or host**.
   - **APIM** — from the returned role→host-port map:

     | Role | URL |
     |---|---|
     | Console | http://localhost:\<console> (admin/admin) |
     | Portal | http://localhost:\<portal> |
     | Management API | http://localhost:\<mgmt>/management |
     | Gateway | http://localhost:\<gateway> |

     plus any feature URL the tool lists (e.g. Prometheus).
   - **AM** returns full URL strings (console `…/am/ui/ (admin/adminadmin)`, management
     `…/am/management/`, gateway `…/am/`) — present as-is.
   - **gamma** — the fixed canonical ports:

     | Role | URL |
     |---|---|
     | Gamma console | http://localhost:8086 (admin/admin) |
     | APIM console | http://localhost:8084 (admin/admin) |
     | Developer portal | http://localhost:8085 (admin/admin) |
     | Management API | http://localhost:8083/management |
     | Gateway | http://localhost:8082 |

   Report **which license source was used** (EE vs OSS). If an EE-only capability was
   expected but it resolved to OSS, warn and point at `~/.gravitee/license.key` /
   `APIM_LICENSE`.

5. **Log to the timeline (ticket-scoped only).** Record via the `Local stack` block
   of `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md` (🛠️): product@version,
   instance, key URLs, license mode. For **gamma**, only when a ticket is in context
   and the user opts in — note it's the shared singleton (no instance; `localhost:8082`–`8086`; version + EE/OSS).
   - **first stack action this session** → new entry:
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>` (prints `NNN`, refreshes `updated_at`).
   - **later lifecycle change** (torn down, version switched) → append to that entry's
     `<details>` + `bump_entry.py <ticket> --touch` (no bump).
   - `/stack` never changes `status` (Zendesk-anchored) → no `set_meta` / `render_header`.

6. **list.**
   - **apim / am:** `apim_list` / `am_list` → tracked instances (version, ports, health) + `other_stacks_on_apim_ports`.
   - **gamma:** `docker compose -p gravitee-gamma ps` (per-service state) — nothing listed = not up.

   Read values from the tools/compose — don't guess.

7. **down / clean.**
   - **apim / am:**
     - `down` → `apim_down` / `am_down` for the resolved instance (volumes kept).
       Wiping data (`volumes=true`, e.g. a clean version downgrade) → **explicit
       confirmation only**.
     - `clean` (no bulk-prune tool) → `apim_list` + `am_list`, show tracked instances,
       ask **which to retire** (or "all stopped / resolved-ticket ones"), then `*_down`
       each. `volumes=true` per instance only on confirmed data loss.
   - **gamma:** teardown uses the **base file only / just `-p`** — never the license
     override (its unset `${GAMMA_LICENSE_FILE}` errors `empty section between colons`).
     - `down` → `docker compose -p gravitee-gamma down` (removes containers, **keeps** `mongo-data` / `es-data`).
     - Data wipe (factory reset) → `docker compose -p gravitee-gamma down -v` — **explicit confirmation only** (destroys mongo + ES).
     - `clean` is **N/A** (nothing per-instance to prune) → treat as `down`.
   - Ticket-scoped teardown → append the lifecycle line to the ticket's 🛠️ entry (`--touch`).

## Don'ts

- **Never bring up or tear down without confirmation** (images / RAM; teardown with volumes destroys data — `apim/am`: `volumes=true`; `gamma`: `down -v`).
- **Don't reimplement docker-compose for apim/am** — orchestrate gravitee-stacker. (Gamma is the sole exception — see the matrix.)
- **Don't fabricate versions, ports, or URLs** — apim/am from `stack_preflight` / `*_list` / `*_status`; gamma ports are the fixed 8082–8086, state from `docker compose -p gravitee-gamma ps`.
- **Don't block on non-existent `*_wait` tools** — poll `apim_status` / `am_status`, or `docker compose ps` + the management-API curl.
- **Don't remap or double-run Gamma** — canonical-port singleton; on a conflict relay the busy ports and stop; no ticket-scoped instance name.
- **Don't mount a base64 license for gamma** — the node needs raw binary; `base64 -d -i license.base64.txt -o ~/.gravitee/license.key` (see the reference).
- **Don't run EE-only capabilities silently in OSS** — warn when no license resolves.
- **No hand-editing `metadata.json`** — use `bump_entry.py` (`--touch` when appending).
