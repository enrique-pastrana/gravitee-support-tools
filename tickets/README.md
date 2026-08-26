# tickets

A Claude Code plugin for the Gravitee support team. It manages Zendesk support
tickets as chronological timelines — logging inbound messages, drafting replies,
generating KB articles and searching across past cases, all driven from Claude
Code.

> **Status: work in progress.** This plugin is being ported from the standalone
> `~/TICKETS` workspace into a portable marketplace plugin. The MCP wiring to
> `ia-tooling` is done and tested, and the first commands (`tickets-up`,
> `new-ticket`, `log-updates`, `reply`, `status`) are ported; the rest are on
> the way — see [PORTING.md](PORTING.md) for the plan and progress.

> **New here?** Read [docs/getting-started.md](docs/getting-started.md) — a
> plain-language first-time guide to what the plugin does and how to use it.

## What it will do

Ported from the `~/TICKETS` workspace: one folder per ticket with a
chronological `timeline.md`, plus slash commands that do the logging, drafting
and cross-ticket search. Optionally backed by the `ia-tooling`
(`gravitee-local-tooling`) stack for live Zendesk fetch, semantic RAG search and
log access — with a manual fallback when the stack is not running.

## Configuration

The plugin is configured through **shell environment variables** — there is no
plugin config file to edit. Set them once (in `~/.zshrc` / `~/.bashrc`); every
one has a sensible default except `IA_TOOLING_ROOT`, which each user must point
at their own `ia-tooling` checkout.

| Variable | Required? | Default | What it controls | If unset / wrong |
|---|---|---|---|---|
| `IA_TOOLING_ROOT` | **Yes** | `~/ia-tooling` | Locates your local `ia-tooling` checkout — used by `.mcp.json` to start the MCP servers and by the scripts to reach the stack. | `${IA_TOOLING_ROOT}` can't expand, so the Zendesk / search / GitHub / Atlassian MCP servers fail to start. Live Zendesk fetch and cross-ticket search stop working (commands fall back to their manual paste flow). |
| `TICKETS_ROOT` | No | `~/TICKETS` | Where ticket folders are stored — **your** workspace, outside the plugin. | Falls back to `~/TICKETS`. |
| `IA_TOOLING_ENV` | No | `$IA_TOOLING_ROOT/.env` | Path to the `ia-tooling` `.env` file that holds your Zendesk credentials (read by `fetch_attachments.py` to download attachments). | Falls back to `$IA_TOOLING_ROOT/.env`. If that file is missing, attachment downloads fail with a "missing ZENDESK_* in env" error. |
| `GRAVITEE_STACKER_BIN` | Only for `/stack` | — | Absolute path to the [`gravitee-stacker`](https://github.com/zach-sirotkin/gravitee-stacker) MCP binary — an **external** tool the `/stack` command drives to spin up local Gravitee stacks. `.mcp.json` uses it to start the server. | `${GRAVITEE_STACKER_BIN}` can't expand, so the gravitee-stacker MCP server fails to start and `/stack` has no tools. Every other command is unaffected. `/stack` runs `scripts/stack-preflight` to diagnose it. |
| `APIM_LICENSE` | No | `~/.gravitee/license.key` | Path to your Gravitee EE license, used by both back-ends (gravitee-stacker for `apim`/`am`, the compose override for `gamma`). Needed for EE-only capabilities (native-Kafka, alert-engine, Debug mode; for gamma the Gamma modules); without it stacks come up in OSS mode. | Falls back to `~/.gravitee/license.key`, then OSS mode. |
| `CLAUDE_PLUGIN_ROOT` | Automatic | — | Locates the plugin's own bundled `scripts/` and `templates/`. **Set by Claude Code — you never touch this.** | n/a — managed by Claude Code. |

```bash
# in ~/.zshrc (or ~/.bashrc)
export IA_TOOLING_ROOT="$HOME/ia-tooling"   # required — point at your ia-tooling
export TICKETS_ROOT="$HOME/TICKETS"         # optional — this is the default
# export IA_TOOLING_ENV="$HOME/ia-tooling/.env"   # optional — only if your .env lives elsewhere
# export GRAVITEE_STACKER_BIN="$HOME/.local/bin/gravitee-stacker"  # only for /stack
```

### Local Gravitee stacks (`/stack`, optional)

`/stack` spins up local Gravitee stacks (needs Docker). It handles three
products via **two different back-ends**:

- **`apim`** and **`am`** — standalone, **multi-instance** stacks driven by the
  external [`gravitee-stacker`](https://github.com/zach-sirotkin/gravitee-stacker)
  MCP server. Each one gets its own compose project, volumes, network and
  auto-assigned port band, so you can run several at once; `/stack` names the
  instance after the ticket by default, giving you per-ticket isolation.
- **`gamma`** — the Gamma stack: a **version-selectable singleton** on canonical
  ports `8082`–`8086`, driven by the plugin's **own official docker-compose**
  (public `graviteeio/*` images), **not** gravitee-stacker. There's only ever
  one, it isn't ticket-isolated, and it needs no extra tooling — just Docker (see
  [The Gamma stack](#the-gamma-stack-stack-up-gamma) below).

Only `apim`/`am` need gravitee-stacker. Install it once and point
`GRAVITEE_STACKER_BIN` at the binary, then relaunch Claude (MCP servers load only
at launch):

```bash
pipx install "git+https://github.com/zach-sirotkin/gravitee-stacker@v0.7.2"  # >= v0.7.2
export GRAVITEE_STACKER_BIN="$HOME/.local/bin/gravitee-stacker"
```

If something's wrong, `/stack` runs `scripts/stack-preflight [apim|am|gamma]` to
tell you what (stacker wiring for apim/am; Docker + license + ports for gamma).

#### Licensing (OSS vs EE)

**A license is optional.** Both back-ends resolve one through the same cascade
and take the first that exists and is non-empty; if none does, the stack simply
comes up in **OSS mode** — no error, nothing aborts. The order is:

1. an explicit `license=<path>` argument (only if you point `/stack` at a file),
2. the **`APIM_LICENSE`** environment variable,
3. the default path **`~/.gravitee/license.key`**,
4. otherwise → **OSS mode**.

The easiest setup is to drop your EE license once at `~/.gravitee/license.key`
and forget about it — it's mounted read-only into the management-api (and, for
apim/am, the gateway) automatically whenever it's present. `/stack` reports which
source was used (e.g. `license: default path` or `license: none (OSS mode)`).

You only need a license when the case requires an **enterprise-only** capability:

- the **`kafka`** variant (native-Kafka gateway) **requires** a license — it
  won't come up without one;
- other EE features (alert-engine, Debug mode, …) would otherwise start
  **crippled in OSS**, so `/stack` **warns** when you ask for one but it resolved
  to OSS, pointing you at `~/.gravitee/license.key` / `APIM_LICENSE` instead of
  silently giving you a degraded stack.

For plain APIM / AM reproductions you don't need a license at all.

#### The Gamma stack (`/stack up gamma`)

The Gamma stack is different from the standalone `apim`/`am` stacks. It's driven
by the plugin's **own official docker-compose** — the customer-deployment shape
from the docs, using **public Docker Hub images** (`graviteeio/*`) — **not**
gravitee-stacker. So it needs **no ACR login, no side-by-side module repo, no
`GAMMA_STACK_DIR`** — just Docker.

It's a **singleton**: one stack (mongo + ES + gateway + management-api + the
three UIs) on **canonical `localhost` ports**, compose project `gravitee-gamma`.
It is **not** multi-instance and **not** ticket-scoped — there's no instance
name and its ports can't be remapped, so only one runs at a time. `/stack` links
it to a ticket only as a logging courtesy. But it **is version-selectable**:
`/stack up gamma@4.13` (default `4.12`; Gamma needs 4.12+, since the module
plugins ship inside those images).

| Role | URL | Login |
|---|---|---|
| Gamma console | http://localhost:8086 | admin / admin |
| APIM console | http://localhost:8084 | admin / admin |
| Developer portal | http://localhost:8085 | admin / admin |
| Management API | http://localhost:8083/management | — |
| Gateway | http://localhost:8082 | — |

The **Gamma modules** (Agent Management, AuthZ, AIM, Edge, ESM, …) are baked into
the public 4.12+ images but **license-gated**: with a full-pack Enterprise license
(resolved via the cascade above and mounted through a compose override) they
activate; without one the stack still runs, in OSS mode, with the modules dormant.
Getting that license right has one sharp edge — the Slack bot hands you **base64
text**, but the node wants the **raw binary**, so you must decode it once
(`base64 -d -i license.base64.txt -o ~/.gravitee/license.key`). The full recipe,
the pack list, and the lifecycle commands live in
[`references/gamma-stack.md`](references/gamma-stack.md).

`/stack up gamma` brings the compose up (adding the license override when one
resolves), polls until the services are up and the management API answers, and
prints the URL table. `/stack list gamma` shows service state
(`docker compose -p gravitee-gamma ps`); `/stack down gamma` stops it but keeps
the data volumes (add a confirmed wipe only when you want a factory reset).

### Zendesk credentials (inside the `ia-tooling` `.env`)

These are **not** shell variables — they live inside the `ia-tooling` `.env`
file (the one `IA_TOOLING_ENV` points at) and are read from there. They are your
Zendesk auth; the plugin does not manage them, `ia-tooling` does:

| Key | Default | Purpose |
|---|---|---|
| `ZENDESK_AUTH_MODE` | `api-token` | `api-token` or `oauth`. |
| `ZENDESK_EMAIL` | — | Your Zendesk email (api-token mode). |
| `ZENDESK_API_TOKEN` | — | Zendesk API token (api-token mode). |
| `ZENDESK_OAUTH_ACCESS_TOKEN` | — | Bearer token (oauth mode). |
| `ZENDESK_BASE_URL` | `https://graviteesource.zendesk.com` | Your Zendesk instance URL. |

## Using it

Ticket data lives in **your** tickets workspace, not in the plugin — set its
location with `TICKETS_ROOT` (see [Configuration](#configuration) above; defaults
to `~/TICKETS`).

Commands available so far:

- **`/tickets-up`** — start and verify the `ia-tooling` stack (Docker + Ollama +
  vectordb). Run it first each session, and whenever another command reports the
  stack is down. It's the single recovery point — commands don't start the stack
  themselves, they point back here. Some (`new-ticket`, `log-updates`) can still
  work in a manual fallback with the stack down; indexing and `sync` cannot.
  macOS/Homebrew setup.
- **`/new-ticket <number>`** — start a new ticket. Creates
  `$TICKETS_ROOT/<thousand>/<number>/` with `timeline.md` and `metadata.json`,
  pulls the ticket subject/customer/priority and attachments from Zendesk (with
  a manual paste fallback when the stack is down), logs the opening message as
  entry `[001]`, and surfaces similar past tickets.
- **`/log-updates [number]`** — pull new activity from the Zendesk thread
  (customer messages, replies, internal notes) into the timeline as summarised
  entries, downloading any new attachments. Each entry keeps a `comment_id`
  pointer back to the exact words in Zendesk. Falls back to a manual paste flow
  when the stack is down.
- **`/reply [number]`** — draft an outbound reply grounded in the case, iterate
  on it in chat, and log it to the timeline only once you confirm.
- **`/status [number]`** — print a concise summary of a ticket (state, entry
  count, attachments, last entry). Read-only; infers the ticket from the current
  directory if no number is given.

## Requirements

The plugin talks to the `ia-tooling` (`gravitee-local-tooling`) stack through the
MCP servers it declares in `.mcp.json`: `zendesk`, `vectordb`, `github-mcp-server`,
`atlassian-mcp-server` and `kapa`.

Those servers live **outside** the plugin — they are your own local `ia-tooling`
checkout — so the plugin cannot know where it sits. It locates it through a single
environment variable, **`IA_TOOLING_ROOT`**, which each user sets once to point at
their own `ia-tooling`:

```bash
# in ~/.zshrc (or ~/.bashrc)
export IA_TOOLING_ROOT="$HOME/ia-tooling"
```

Without it, `.mcp.json` cannot expand `${IA_TOOLING_ROOT}` and those servers fail
to start. The plugin ships **no absolute paths** of its own — its bundled scripts
are referenced with `${CLAUDE_PLUGIN_ROOT}`, which Claude Code fills in
automatically.

Two deliberate omissions:

- **`fathom`** is not declared here — it belongs to the `p1-updates` plugin.
- **`grafana`** is parked for now.
- **`kapa`** is declared but currently fails to start on a known, unrelated
  `ia-tooling` issue (a global `kapa` MCP fails the same way). It is not used yet.

## Layout

```
tickets/
├── .claude-plugin/
│   └── plugin.json        # manifest (name, version, metadata)
├── .mcp.json              # ia-tooling MCP servers (via ${IA_TOOLING_ROOT})
├── commands/              # slash commands (ported from .claude/commands/)
├── agents/                # subagent definitions
├── skills/                # skills — each a <name>/SKILL.md directory
├── scripts/               # Python helpers (referenced via ${CLAUDE_PLUGIN_ROOT})
├── templates/             # file templates used by commands
├── references/            # shared procedure docs commands read on demand
├── docs/                  # user-facing guides (getting-started.md)
├── PORTING.md             # the porting journal — design decisions & progress
└── README.md
```

Only `plugin.json` lives under `.claude-plugin/`. Every other component —
including `.mcp.json` — sits at the plugin root.

## Local development

See the marketplace [CONTRIBUTING.md](../CONTRIBUTING.md). In short:

```bash
claude --plugin-dir /path/to/tickets
claude plugin validate ./tickets --strict
```
