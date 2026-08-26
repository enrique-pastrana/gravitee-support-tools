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
| `APIM_LICENSE` | No | `~/.gravitee/license.key` | Path to your Gravitee EE license, read by gravitee-stacker. Needed for EE-only stack features (native-Kafka, alert-engine, Debug mode); without it stacks come up in OSS mode. | Falls back to `~/.gravitee/license.key`, then OSS mode. |
| `GAMMA_STACK_DIR` | Only for `/stack up gamma` | `~/gravitee-gamma-modules-sdk` | Locates the Gamma demo-stack repo (with `docker/run.sh`) that gravitee-stacker drives for the Gamma stack. Only `/stack up gamma` uses it; `apim`/`am` don't. | Falls back to the default path; if that repo (plus an ACR login and a license inside it) is absent, `/stack up gamma` reports what's missing and won't start. |
| `CLAUDE_PLUGIN_ROOT` | Automatic | — | Locates the plugin's own bundled `scripts/` and `templates/`. **Set by Claude Code — you never touch this.** | n/a — managed by Claude Code. |

```bash
# in ~/.zshrc (or ~/.bashrc)
export IA_TOOLING_ROOT="$HOME/ia-tooling"   # required — point at your ia-tooling
export TICKETS_ROOT="$HOME/TICKETS"         # optional — this is the default
# export IA_TOOLING_ENV="$HOME/ia-tooling/.env"   # optional — only if your .env lives elsewhere
# export GRAVITEE_STACKER_BIN="$HOME/.local/bin/gravitee-stacker"  # only for /stack
```

### Local Gravitee stacks (`/stack`, optional)

`/stack` spins up local Gravitee stacks by driving the external
[`gravitee-stacker`](https://github.com/zach-sirotkin/gravitee-stacker) MCP
server (needs Docker). It handles three products:

- **`apim`** and **`am`** — standalone, **multi-instance** stacks. Each one gets
  its own compose project, volumes, network and auto-assigned port band, so you
  can run several at once; `/stack` names the instance after the ticket by
  default, giving you per-ticket isolation.
- **`gamma`** — the Gamma demo stack: a **shared singleton** on canonical ports,
  with nginx host-routing on `:80` (`gamma.localhost` / `apim.localhost` /
  `portal.localhost` / `am.localhost`). There's only ever one, it isn't
  ticket-isolated, and it needs extra setup (see [The Gamma stack](#the-gamma-stack-stack-up-gamma) below).

Install gravitee-stacker once and point `GRAVITEE_STACKER_BIN` at the binary,
then relaunch Claude (MCP servers load only at launch):

```bash
pipx install "git+https://github.com/zach-sirotkin/gravitee-stacker@v0.7.2"  # >= v0.7.2
export GRAVITEE_STACKER_BIN="$HOME/.local/bin/gravitee-stacker"
```

If the tools are missing, `/stack` runs `scripts/stack-preflight` to tell you
what's wrong.

#### Licensing (OSS vs EE)

**A license is optional.** gravitee-stacker resolves one through a cascade and
takes the first that exists and is non-empty; if none does, the stack simply
comes up in **OSS mode** — no error, nothing aborts. The order is:

1. an explicit `license=<path>` argument (only if you point `/stack` at a file),
2. the **`APIM_LICENSE`** environment variable,
3. the default path **`~/.gravitee/license.key`**,
4. otherwise → **OSS mode**.

The easiest setup is to drop your EE license once at `~/.gravitee/license.key`
and forget about it — stacker mounts it read-only into the gateway and
management-api automatically whenever it's present. `/stack` reports which
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

The Gamma stack is different from the standalone `apim`/`am` stacks: it's a
**shared singleton** — one full demo environment (AM + APIM + SPIRE, fronted by
nginx) on **canonical ports**, reachable through host-routing on `:80`
(`http://gamma.localhost`, `http://apim.localhost`, `http://portal.localhost`,
`http://am.localhost`). It is **not** multi-instance and **not** ticket-scoped:
there's no instance name and its ports can't be remapped, so only one can run at
a time. `/stack` links it to a ticket only as a logging courtesy.

It needs more than the standalone stacks:

1. the **demo-stack repo** checked out locally, pointed at by **`GAMMA_STACK_DIR`**
   (default `~/gravitee-gamma-modules-sdk`) — it holds `docker/run.sh`;
2. an **ACR login** (the images live in a private registry);
3. a **license** inside the repo (`docker/license/license.key`).

`/stack up gamma` runs the whole chain — bring the stack up in the background,
poll until it's healthy, then (after you confirm) run the demo **bootstrap**
(`stack_setup`: AM + APIM + SPIRE + `setup.sh`), which can take a few minutes.
`/stack setup gamma` re-runs just that bootstrap on an already-up stack, and
`/stack down gamma` tears it down. Before starting it, `/stack` asks
gravitee-stacker's `doctor` whether the repo, ACR login and license are all in
place, and if not it tells you exactly what's missing instead of failing
half-way. (If you need host `:443` / DNS routing there's an extra Edge Daemon
install step — a sudo command gravitee-stacker prints for you to run yourself.)

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
