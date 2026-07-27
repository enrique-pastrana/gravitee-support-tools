# Contributing

How this marketplace is put together, and how to add to it. For installing and
using the plugins, see [README.md](README.md).

## Layout

```
gravitee-support-tools/
├── .claude-plugin/
│   └── marketplace.json   # the catalogue — name, owner, plugins[]
├── p1-updates/            # a plugin, with its own .claude-plugin/plugin.json
├── CONTRIBUTING.md
└── README.md
```

Two manifests, two different files, easily confused:

- `.claude-plugin/marketplace.json` at the **repository root** lists the plugins.
- `.claude-plugin/plugin.json` inside **each plugin** describes that plugin.

The marketplace manifest must sit at the repository root. That is what makes
`claude plugin marketplace add <owner>/<repo>` work — Claude Code looks for
`.claude-plugin/marketplace.json` there and nowhere else.

Within a plugin, only `plugin.json` belongs inside `.claude-plugin/`. Every
other component — `skills/`, `agents/`, `commands/`, `.mcp.json` — sits at the
plugin root. Putting `.mcp.json` in `.claude-plugin/` is the mistake most easily
made.

Each entry in `plugins[]` points at its plugin with `source`. A relative path
like `./p1-updates` means the plugin lives in this same repository; plugins
hosted elsewhere use a `git` / `git-subdir` source object instead.

Metadata is duplicated between the two manifests on purpose: the marketplace
entry is what the catalogue shows *before* the plugin is fetched. Keep the
descriptions in step when a plugin changes. Version is deliberately **not**
repeated in the marketplace entry — it is read from `plugin.json`, so there is
one place to bump.

## Adding a plugin

1. Create the plugin directory here, with `.claude-plugin/plugin.json` inside it.
2. Add an entry to `plugins[]` in `.claude-plugin/marketplace.json`, with
   `"source": "./<dir>"`.
3. Add a row to the table in [README.md](README.md).
4. Validate both manifests.

## Validating

```bash
claude plugin validate . --strict            # the marketplace
claude plugin validate ./<dir> --strict      # the plugin
```

`--strict` fails on unrecognised fields and missing metadata that the runtime
would otherwise tolerate — use it, and use it in CI.

Note that `validate` accepts a bare `.`, while `marketplace add` rejects it.

## Working on a plugin

While iterating you usually do **not** want to install. Load the plugin in place
for a single session:

```bash
claude --plugin-dir ./p1-updates
```

This installs nothing and copies nothing. Edits to a `SKILL.md` body take effect
immediately; changes to `.mcp.json`, either manifest, or a newly added skill
directory need `/reload-plugins` or a restart.

When a `--plugin-dir` plugin shares a name with an installed one, the local copy
wins for that session — so you can test changes without uninstalling first.

If the MCP server fails to start, `claude --debug` shows the initialisation
error.

## Installing from a local checkout

To exercise the full marketplace path against working copy rather than GitHub,
point `marketplace add` at a path:

```bash
claude plugin marketplace add ../gravitee-support-tools --scope local
```

A bare `.` is rejected — pass `./something`, a relative path, or an absolute
one. Relative paths are resolved and stored as **absolute**, so a path-based
declaration is never portable to another machine. That is why the instructions
in the README use the GitHub shorthand instead.

Use `--scope local` so the declaration stays in that directory's
`.claude/settings.local.json` rather than your global settings. Undoing it needs
the flag too:

```bash
claude plugin uninstall p1-updates@gravitee-support-tools --scope local
claude plugin marketplace remove gravitee-support-tools
```

If you have installed from the marketplace and then edit the source, run
`claude plugin marketplace update gravitee-support-tools` to pick the change up.

## Releasing

Bump `version` in the plugin's `plugin.json`, then:

```bash
claude plugin tag ./<dir>
```

This creates a `<name>--v<version>` git tag and refuses if `plugin.json` and the
marketplace entry disagree — which is the drift this two-manifest layout invites.

## Conventions

`.claude/settings.local.json` is personal — permissions and local-scope plugin
declarations — and is gitignored. The shared equivalent is
`.claude/settings.json`, which is committed on purpose.
