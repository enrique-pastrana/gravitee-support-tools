---
description: Spin up, list, or tear down a local Gravitee stack — standalone APIM / AM via the gravitee-stacker MCP server, or the version-selectable Gamma singleton via its official docker-compose — ticket-scoped and logged to the timeline.
argument-hint: <up|list|down|clean> [apim|am|gamma][@version] [ticket]
---

Drive local Gravitee stacks. `$ARGUMENTS` is free-form intent (verb + product +
version + ticket); default verb is **up**. **The user drives; never bring a stack
up or tear one down without confirmation** — stacks pull images and consume RAM,
and teardown with volumes wipes data.

**Two very different back-ends — pick by product:**
- **`apim` / `am`** → **orchestrate the `gravitee-stacker` MCP server**; never
  reimplement docker-compose for these.
- **`gamma`** → **orchestrate `docker compose` directly** against the
  plugin-shipped official compose. This is the *one deliberate exception* to the
  no-compose rule: Gamma isn't in gravitee-stacker, so `/stack` runs the official
  public-image compose itself. See `${CLAUDE_PLUGIN_ROOT}/references/gamma-stack.md`.

**Conventions**
- Ticket data → workspace `$TICKETS_ROOT` (default `~/TICKETS`).
- Scripts/templates/references → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files
  into the workspace.
- gravitee-stacker is an **external** MCP server, wired in `.mcp.json` via
  `${GRAVITEE_STACKER_BIN}`. Its tools appear as `apim_*` / `am_*`.
- **Products differ in shape:**
  - **`apim` / `am`** — standalone and **multi-instance** (gravitee-stacker).
    **Instance = ticket number** by default → per-ticket isolation (own compose
    project, volumes, network, auto port band) and obvious ownership. Standalone
    ("a stack for my own testing", no ticket) → let the user name the instance.
  - **`gamma`** — the official Gamma stack (plugin compose): a **singleton** on
    **canonical ports `8082`–`8086`**, compose project **`gravitee-gamma`**,
    **version-selectable** (`gamma@4.13`, default `4.12`, needs 4.12+). Public
    Docker Hub images (`graviteeio/*`) — **no ACR login, no side-by-side repos**.
    It is **not** multi-instance and **not** ticket-isolated — only ever one, no
    instance name, ports don't remap. A full-pack Enterprise license (optional
    override) activates the Gamma modules; without one it runs OSS. Ticket link is
    **optional** (a logging courtesy, step 5).

Compose files (gamma): base `${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.yml`,
license override `${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.license.yml`.

## Steps

1. **Preflight.**
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/stack-preflight" [apim|am|gamma]
   ```
   - **apim / am:** if the gravitee-stacker tools aren't available the server
     didn't load — the script diagnoses a missing `GRAVITEE_STACKER_BIN`, Docker
     down, or absent license (MCP servers load only at launch, so a fix means
     relaunching Claude). If the tools **are** there, call `doctor` for a Docker +
     license readiness check.
   - **gamma:** the script checks **Docker is up**, whether a **license** resolves
     (explicit `license=` → `$APIM_LICENSE` → `~/.gravitee/license.key`; none = OSS,
     modules dormant), and whether canonical ports **8082–8086** are free. Relay
     what it reports; on a port conflict, stop (don't tear down whatever holds them).
     No gravitee-stacker involvement.

2. **Resolve intent + ticket.** Parse verb (`up`/`list`/`down`/`clean`), product
   (`apim`/`am`/`gamma`), version, and for apim/am any variant (`kafka`) / features
   (`prometheus`, `redis-rate-limit`, …). For a ticket-scoped action, resolve the
   ticket via `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md` (chain
   **arguments > current > cwd > ask**); an explicit number is a one-off (doesn't
   move the pointer).
   - **apim / am:** default the **instance to that ticket number**. Standalone →
     ask for an instance name; skip the ticket write-guards and step 5.
   - **gamma:** singleton — **no instance, no per-ticket scoping**, but **do**
     parse the version (`gamma@4.13` → `GAMMA_VERSION=4.13`, default `4.12`). Only
     when a ticket is already in context, offer the optional 🛠️ log (step 5); never
     prompt for a ticket just to bring Gamma up.

3. **Plan + confirm (up).** Preview without side effects, then **confirm before
   bringing up** (on any port conflict, report the busy ports and stop — never
   auto-down another stack):
   - **apim / am:**
     ```
     stack_preflight(kind="apim"|"am", version=…, variant=…)   # resolves version, computes canonical ports, flags conflicts
     ```
     Show the resolved version, ports/URLs, license source, and any conflict.
   - **gamma:** resolve the license (explicit `license=` → `$APIM_LICENSE` →
     `~/.gravitee/license.key` → none). Render the plan without side effects:
     ```bash
     GAMMA_VERSION=<version> docker compose \
       -f "${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.yml" \
       -p gravitee-gamma config >/dev/null   # validate; add the license -f below when one resolved
     ```
     State plainly: this is the **shared singleton** on canonical ports 8082–8086,
     the resolved **version** and **license mode** (EE vs OSS), that pulling images
     can take minutes, and that it replaces any Gamma already running. Confirm.

4. **Bring up.**
   - **apim / am:** `apim_up` / `am_up` with the resolved args (pass `license=`
     only if the user points at a specific file — otherwise let gravitee-stacker
     resolve `APIM_LICENSE` → `~/.gravitee/license.key` → OSS). These run
     **background/non-blocking**, so **poll `apim_status` / `am_status` until
     `overall` is `healthy`** (report progress; a non-zero exit → `failed`, relay
     the log tail).
   - **gamma:** run the official compose under the fixed project. Add the license
     override **only** when a license resolved (then set `GAMMA_LICENSE_FILE`);
     otherwise run the base file alone (OSS):
     ```bash
     # EE (license resolved):
     GAMMA_VERSION=<version> GAMMA_LICENSE_FILE=<resolved-path> docker compose \
       -f "${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.yml" \
       -f "${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.license.yml" \
       -p gravitee-gamma up -d
     # OSS (no license): drop the second -f and GAMMA_LICENSE_FILE.
     ```
     `up -d` returns once containers are created; images may still be pulling. **Poll
     `docker compose -p gravitee-gamma ps`** until every service is `Up`, then
     confirm the management API answers:
     ```bash
     curl -sf http://localhost:8083/management/organizations/DEFAULT/console >/dev/null && echo READY
     ```
     On a stuck/failed service relay `docker compose -p gravitee-gamma logs <service>`
     and stop. If a license was mounted, **verify activation** (per
     `references/gamma-stack.md`):
     ```bash
     docker logs gamma_management_api 2>&1 | grep -c "detected but not activated"   # want 0
     ```
     A non-zero count with a license usually means the mounted file is base64 text,
     not raw binary — point at the `base64 -d` fix in the reference.

   **Always print an Access URLs table** — the same **two-column `Role | URL`** shape
   for every product (credentials inline in the URL cell) — from what the tools/compose
   actually expose; never fabricate a port or host.
   - **APIM** — from the returned role→host-port map:

     | Role | URL |
     |---|---|
     | Console | http://localhost:\<console> (admin/admin) |
     | Portal | http://localhost:\<portal> |
     | Management API | http://localhost:\<mgmt>/management |
     | Gateway | http://localhost:\<gateway> |

     plus any feature URL the tool lists (e.g. Prometheus `http://localhost:<prometheus>`).
   - **AM** already returns full URL strings (console `…/am/ui/ (admin/adminadmin)`,
     management `…/am/management/`, gateway `…/am/`) — present them as-is in the table.
   - **gamma** — the fixed canonical ports:

     | Role | URL |
     |---|---|
     | Gamma console | http://localhost:8086 (admin/admin) |
     | APIM console | http://localhost:8084 (admin/admin) |
     | Developer portal | http://localhost:8085 (admin/admin) |
     | Management API | http://localhost:8083/management |
     | Gateway | http://localhost:8082 |

   Also report **which license source was used** (gamma: EE vs OSS). If an EE-only
   capability was expected but it resolved to OSS, warn and point at
   `~/.gravitee/license.key` / `APIM_LICENSE`.

5. **Log to the timeline (ticket-scoped only).** Record the stack via the
   `Local stack` block of `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`
   (🛠️): product@version, instance, key URLs, license mode. For **gamma**, only
   when a ticket is already in context and the user opts in — note it's the
   **shared** Gamma singleton (no instance; canonical `localhost:8082`–`8086`;
   version + EE/OSS).
   - **first stack action this session** → new entry `[NNN]`
     (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>` → prints
     `NNN`, refreshes `updated_at`)
   - **later lifecycle change** (torn down, version switched) → **append to that
     same entry's `<details>`** + `bump_entry.py <ticket> --touch` (no bump)
   - `/stack` doesn't change `status` (Zendesk-anchored) → **no `set_meta`/`render_header`.**

6. **list.**
   - **apim / am:** `apim_list` / `am_list` → tracked instances (version, ports,
     health) plus `other_stacks_on_apim_ports`.
   - **gamma:** `docker compose -p gravitee-gamma ps` (per-service state) — there's
     only ever one Gamma stack. If nothing is listed, it isn't up.

   Read values from the tools/compose — don't guess.

7. **down / clean.**
   - **apim / am:**
     - `down` → `apim_down` / `am_down` for the resolved instance (volumes kept by
       default). Wiping data (`volumes=true`, e.g. for a clean version downgrade)
       only on **explicit** user confirmation.
     - `clean` (no bulk-prune tool exists) → `apim_list` + `am_list`, show the
       tracked instances, ask **which to retire** (or "all stopped / resolved-
       ticket ones"), then `*_down` each. `volumes=true` per instance only when
       the user confirms the data loss.
   - **gamma:** (teardown uses the **base file only / just `-p`** — never the license
     override; its unset `${GAMMA_LICENSE_FILE}` on `down` errors with `empty section
     between colons`.)
     - `down` → `docker compose -p gravitee-gamma down` (stops + removes containers,
       **keeps** the `mongo-data` / `es-data` volumes so APIs/users survive).
     - Data wipe (factory reset) → `docker compose -p gravitee-gamma down -v` **only
       on explicit confirmation** — it destroys mongo + ES.
     - `clean` is **N/A** for gamma (nothing per-instance to prune) — treat it as
       `down` (containers only, volumes kept).
   - Ticket-scoped teardown → append the lifecycle line to the ticket's 🛠️ entry
     (`--touch`).

## Don'ts

- **Never bring up or tear down without confirmation** — stacks pull images /
  consume RAM; teardown with volumes destroys data (`apim/am`: `volumes=true`;
  `gamma`: `down -v`).
- **Don't reimplement docker-compose for apim/am** — orchestrate gravitee-stacker's
  tools. (**gamma is the sole exception**: it's driven by the plugin's official
  compose, since it isn't in stacker.)
- **Don't fabricate versions, ports, or URLs** — read apim/am from
  `stack_preflight` / `*_list` / `*_status`; gamma ports are the fixed 8082–8086,
  service state from `docker compose -p gravitee-gamma ps`.
- **Don't block on non-existent `*_wait` tools** — `apim_up` / `am_up` are
  background; poll `apim_status` / `am_status`. Gamma: poll `docker compose ps` +
  the management-API curl until ready.
- **Don't remap or double-run Gamma** — it's a canonical-port singleton; on a port
  conflict relay the busy ports and stop, and never expect a ticket-scoped instance
  name for it.
- **Don't mount a base64 license for gamma** — the node needs the raw binary;
  `base64 -d -i license.base64.txt -o ~/.gravitee/license.key` (see the reference).
- **Don't run EE-only capabilities silently in OSS** — warn when no license resolves.
- No hand-editing `metadata.json` — use `bump_entry.py` (`--touch` when appending).
