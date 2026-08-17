# Porting `~/TICKETS` → `tickets` plugin

The journal of turning the standalone `~/TICKETS` workspace into a portable
Claude Code plugin in the `gravitee-support-tools` marketplace. This is a
development document — the user-facing doc is [README.md](README.md).

## Why

`~/TICKETS` is a full Claude-Code-driven system for handling Zendesk tickets: a
folder per ticket with a chronological `timeline.md`, driven by slash commands.
It only works from that one checkout, with hardcoded paths. Porting it to a
plugin makes it installable, portable and shareable through the marketplace.

## Source

- Workspace: `/Users/enrique.pastrana/TICKETS`
- Its own git repo (`tickets-tool`), separate from this marketplace.
- The `updateP1` command from this workspace already shipped separately as the
  `p1-updates` plugin — this plugin ports the rest.

## Component mapping

What lives in `~/TICKETS` and where it lands in the plugin:

| Source (`~/TICKETS`)            | Plugin destination        | Notes |
|---------------------------------|---------------------------|-------|
| `.claude/commands/*.md` (19)    | `commands/`               | Straight port; drop `updateP1` (already in `p1-updates`). |
| `.claude/agents/queue-health.md`| `agents/`                 | Straight port. |
| `_system/scripts/*.py`          | `scripts/`                | Reference via `${CLAUDE_PLUGIN_ROOT}`; fix `~/TICKETS` path assumptions. |
| `_system/templates/*`           | `templates/`              | Straight port. |
| `CLAUDE.md` (behavioural contract) | `skills/` (likely)     | Cannot ship as a root `CLAUDE.md`; see open question 3. |
| ticket data (`13000-15000/`, `16000/`, …) | **not ported**   | User data, not machinery — stays in the user's workspace. |
| `.mcp.json`                     | `.mcp.json` (TBD)         | Hardcoded absolute paths today; see open question 2. |

## Open questions (decide before/while porting)

### 1. Where does the ticket data live?
Today the scripts default to `~/TICKETS` (overridable with `TICKETS_ROOT`) and
the permission allowlist assumes that path. As a plugin, the machinery ships but
the ticket folders belong to the user. Need a portable way for the plugin to
locate the tickets root — env var, a config file, or the current working
directory. **Undecided.**

### 2. The `ia-tooling` MCP wiring — DECIDED (2026-08-17)
`~/TICKETS/.mcp.json` hardcoded `/Users/enrique.pastrana/ia-tooling/...` for the
`zendesk`, `vectordb`, `github`, `atlassian`, `kapa` servers. Not portable.

**Decision:** declare the servers in the plugin's own `.mcp.json`, replacing the
hardcoded prefix with a single per-user environment variable
**`${IA_TOOLING_ROOT}`** (Claude Code expands it at load time). The user sets it
once in their shell (`export IA_TOOLING_ROOT="$HOME/ia-tooling"`). No absolute
path lives in the repo. Scoped down for now:

- **5 servers** ported: `zendesk`, `vectordb`, `github-mcp-server`,
  `atlassian-mcp-server`, `kapa`. Only `zendesk` (env-file) and the three
  `local-tooling` commands carried a path; `vectordb` had none.
- **`fathom` dropped** here — already shipped in `p1-updates`.
- **`grafana` parked** for now.

**Verified** in the clean `sandbox/` via `claude --plugin-dir ../gravitee-support-tools/tickets`:
`/mcp` showed all servers prefixed `plugin:tickets:` (proving the plugin, not
`~/TICKETS`, provides them). 4 of 5 connected with tools (zendesk 11, vectordb 4,
github 23, atlassian 31). `kapa` failed on a pre-existing, unrelated `ia-tooling`
issue (the user's global `kapa` MCP fails identically) — parked.

### 3. The behavioural contract (`CLAUDE.md`)
The 15KB `CLAUDE.md` is the rulebook Claude follows in the workspace (response
style, ticket conventions, MCP usage, pre-authorised actions). A plugin cannot
inject a root `CLAUDE.md` into the user's directory. Candidate: turn it into a
plugin **skill** (or split it across command prompts). **Undecided.**

## Progress log

- **2026-08-17** — Created branch `add-tickets-plugin`. Scaffolded the empty
  plugin: `plugin.json`, README stub, this journal, and empty
  `commands/ agents/ skills/ scripts/ templates/` dirs. Added the plugin to the
  marketplace catalogue. No logic ported yet.
- **2026-08-17** — Resolved open question 2 (MCP wiring). Wrote a portable
  `.mcp.json` using `${IA_TOOLING_ROOT}` for 5 ia-tooling servers (fathom
  dropped, grafana parked). Validated JSON + `plugin validate --strict`, then
  tested from the clean `sandbox/` with `--plugin-dir`: 4/5 servers connected
  (kapa parked). Documented the `IA_TOOLING_ROOT` requirement in the README.
  Commands, agent, scripts, templates and the `CLAUDE.md` contract still to port.
