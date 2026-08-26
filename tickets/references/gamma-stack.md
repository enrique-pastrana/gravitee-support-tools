# Reference: the local Gamma stack (`/stack … gamma`)

How `/stack` brings up **Gamma** locally, why it works differently from `apim`/`am`,
and the one-time **Enterprise license** setup that unlocks the Gamma modules. Read by
the `gamma` branch of the `/stack` command; the command decides *when* to act, this is
the *how* and the *why*.

## Gamma is not driven by gravitee-stacker

`apim` / `am` are multi-instance and driven by the external **gravitee-stacker** MCP
server (per-ticket isolation, auto port bands). **Gamma is different**: it runs from a
plugin-shipped **official docker-compose** using **public Docker Hub images**
(`graviteeio/*`) — the same shape a customer deploys. So `/stack … gamma`:

- **orchestrates `docker compose` directly** (the one deliberate exception to the
  "don't reimplement compose" rule — Gamma isn't in stacker), against
  `${CLAUDE_PLUGIN_ROOT}/templates/docker-compose-gamma.yml`;
- is a **singleton on canonical ports** (`8082`–`8086`) with a fixed compose project
  `gravitee-gamma` — **one Gamma at a time**, no instance name, ports don't remap;
- needs **no ACR login and no side-by-side module repos**. (That heavier path — Zach's
  `gravitee-gamma-modules-sdk` + stacker `stack_*` tools, private Azure Container
  Registry, locally-built `alpha` plugins, SPIRE/edge/nginx — is a *dev inner-loop* for
  people building the Gamma modules, not for reproducing released customer setups.)

**Requirements:** Docker Desktop running. That's it for OSS. Agent Management and the
other license-gated modules need the Enterprise license below — everything else runs
without one.

## Versioning

Every `graviteeio/*` image is pinned to `${GAMMA_VERSION:-4.12}`. Gamma needs **4.12+**
(the Gamma module plugins ship inside 4.12 and later images). `/stack up gamma@<version>`
sets `GAMMA_VERSION` for that run, e.g. `/stack up gamma@4.13`. Pin the version a
customer runs to reproduce their environment.

## The Enterprise license (one-time)

The public `apim-management-api:4.12+` image **already bakes in** the Gamma module
plugins (`authz`, `aim`, `edge`, `esm`). Without a license they load but stay dormant —
the log shows `WARN … 'aim' detected but not activated` and `No license file found`. A
**full-pack license activates them from the public images** — no SDK repo, no ACR.

### 1. Generate it (Gravitee staff: Slack `/generate-license` bot)

Use the **legacy `universe` tier + all packs** ("Cross-Version Full License"): the legacy
tier works on **every** APIM version (the newer `gamma-*` tiers are 4.12.0+ only), and the
**packs** are what actually switch the Gamma modules on.

```
/generate-license email=[YOUR_EMAIL] company=[YOUR_COMPANY] tier=universe \
  packs=native-kafka,agent-mesh,authorization-management,identity-and-access-management,agent-management,event-native-management,event-streaming-management,edge-management \
  expiry=[YYYY-MM-DD]
```

Pack → module it unlocks: `authorization-management`→`authz`,
`identity-and-access-management`→`aim`, `edge-management`→`edge`,
`event-streaming-management`→`esm`, plus `agent-management`, `agent-mesh`, `native-kafka`,
`event-native-management`. (Customers get theirs through their TAM.)

### 2. Convert base64 → raw binary  ⚠️ the easy trap

The bot offers **"Download License (base64)"** and **"Download Decoded License"**. The
gravitee-node loader wants the **RAW BINARY**, and **mounting the base64 text fails** with:

```
WARN  LicenseLoaderService - Provided license is malformed, skipping.
      MalformedLicenseException: License cannot be read
```

Download the **base64** one and decode it once into place (macOS `base64` needs `-i`/`-o`;
a positional filename errors out):

```bash
base64 -d -i ~/Downloads/license-*.base64.txt -o ~/.gravitee/license.key
chmod 600 ~/.gravitee/license.key
```

The result is ~768 bytes, `file` reports `data` (binary), and it begins `21 ce 4e 5e …`.
Don't use the "Decoded License" download — served as UTF-8 it gets mojibake-corrupted
(every byte ≥ `0x80` doubles, `ce`→`c3 8e`); it's only good for eyeballing the packs.

### 3. Where it lives

Canonical path **`~/.gravitee/license.key`** — the same file gravitee-stacker resolves for
`apim`/`am`, so one license serves all three. `/stack` resolves the license in this order
and passes it to the license override compose:

1. an explicit `license=<path>` on the command,
2. `$APIM_LICENSE`,
3. `~/.gravitee/license.key`,
4. none → OSS (Gamma modules stay dormant; `/stack` warns).

### 4. Verify activation

After `up`, the management_api log should show the license and **zero** dormant modules:

```bash
docker logs gamma_management_api 2>&1 | grep -A8 "License information:"        # tier=universe, packs=<all 8>
docker logs gamma_management_api 2>&1 | grep -c "detected but not activated"   # 0  ✅
```

If it still says `malformed`, the mounted file is the base64 text, not the binary — redo
step 2.

## Lifecycle (what `/stack` runs under the hood)

Fixed project `gravitee-gamma`; add the license override only when a license resolved:

```bash
# up (OSS)
docker compose -f templates/docker-compose-gamma.yml -p gravitee-gamma up -d
# up (EE) — GAMMA_LICENSE_FILE is the resolved host path
GAMMA_LICENSE_FILE=~/.gravitee/license.key GAMMA_VERSION=4.12 \
  docker compose -f templates/docker-compose-gamma.yml -f templates/docker-compose-gamma.license.yml \
  -p gravitee-gamma up -d

docker compose -p gravitee-gamma ps                # list / status
docker compose -p gravitee-gamma logs -f <service> # logs
docker compose -p gravitee-gamma down              # stop + remove containers, KEEP data (volumes)
docker compose -p gravitee-gamma down -v           # ⚠️ also wipe mongo/ES data (factory reset)
```

`down` keeps the named volumes (`mongo-data`, `es-data`) so APIs/users survive a restart;
`-v` is a data-wiping reset and only on explicit confirmation. There's only ever one Gamma
stack, so `clean` has nothing per-instance to prune — treat it as `down`.

⚠️ **`down` / `ps` use the base file only (or just `-p`) — never the license override.**
The override interpolates `${GAMMA_LICENSE_FILE}`; on teardown that variable isn't set, so
adding `-f docker-compose-gamma.license.yml` fails with
`invalid spec: :/opt/…/license.key:ro: empty section between colons`. The project name
(`-p gravitee-gamma`) alone identifies every container/volume — the override is an
**up-only** concern.

## Access URLs (canonical, fixed)

| Role | URL |
|---|---|
| Gamma console | http://localhost:8086 (admin/admin) |
| APIM console | http://localhost:8084 (admin/admin) |
| Developer portal | http://localhost:8085 (admin/admin) |
| Management API | http://localhost:8083/management |
| Gateway | http://localhost:8082 |

Read health/URLs from `docker compose -p gravitee-gamma ps` — don't fabricate ports.
