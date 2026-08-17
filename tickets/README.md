# tickets

A Claude Code plugin for the Gravitee support team. It manages Zendesk support
tickets as chronological timelines — logging inbound messages, drafting replies,
generating KB articles and searching across past cases, all driven from Claude
Code.

> **Status: work in progress.** This plugin is being ported from the standalone
> `~/TICKETS` workspace into a portable marketplace plugin. The MCP wiring to
> `ia-tooling` is done and tested; the commands are not ported yet — see
> [PORTING.md](PORTING.md) for the plan and progress.

## What it will do

Ported from the `~/TICKETS` workspace: one folder per ticket with a
chronological `timeline.md`, plus slash commands that do the logging, drafting
and cross-ticket search. Optionally backed by the `ia-tooling`
(`gravitee-local-tooling`) stack for live Zendesk fetch, semantic RAG search and
log access — with a manual fallback when the stack is not running.

## Using it

_To be documented as commands are ported._

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
