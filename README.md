# gravitee-support-tools

A Claude Code **marketplace** for the Gravitee support team — the catalogue the
team installs plugins from.

## Plugins

| Plugin | What it does |
| --- | --- |
| [`p1-updates`](p1-updates/) | Turns a Fathom customer call into a who/what/when P1 status summary, ready to paste into Slack. |

## Installing

Add the marketplace once, then install what you need from it.

```bash
claude plugin marketplace add enrique-pastrana/gravitee-support-tools
claude plugin install p1-updates@gravitee-support-tools
```

Installed skills are namespaced by plugin, so `updateP1` is invoked as
`/p1-updates:updateP1`. Start a new session — installing does not load the
plugin into sessions that are already open.

Check what you have:

```bash
claude plugin marketplace list
claude plugin list
```

To back out:

```bash
claude plugin uninstall p1-updates@gravitee-support-tools
claude plugin marketplace remove gravitee-support-tools
```

`uninstall` leaves the plugin files behind in
`~/.claude/plugins/cache/<marketplace>/`, marked with an `.orphaned_at` stamp so
a reinstall is instant. `claude plugin prune` does **not** clear that — it only
handles auto-installed dependencies. Delete the directory by hand if you want
the disk clean.

## Scopes

Both `marketplace add` and `install` take `--scope`, and getting it wrong is the
usual source of confusion.

| scope | declared in | who sees it |
| --- | --- | --- |
| `user` (default) | `~/.claude/settings.json` | you, in every directory |
| `project` | `<dir>/.claude/settings.json` | anyone who opens that directory — committed |
| `local` | `<dir>/.claude/settings.local.json` | only you, only in that directory |

Two traps worth knowing:

- **The directory you run from does not scope anything.** Running `install`
  inside a project folder without `--scope local` still installs globally.
- **`uninstall` defaults to `user`**, whatever the plugin was installed as. To
  undo a local install you must pass `--scope local` explicitly.

What `--scope local` isolates is the plugin's *activation*, not the
marketplace's visibility: `claude plugin marketplace list` reads a global cache
at `~/.claude/plugins/known_marketplaces.json`, so a locally-declared
marketplace still shows up from any directory. `claude plugin list` is the one
that respects scope — it records a `projectPath` for local installs and none
for user ones.

To put the marketplace in front of the whole team at clone time, declare it at
project scope so it lands in a committed `settings.json`:

```bash
claude plugin marketplace add enrique-pastrana/gravitee-support-tools --scope project
```

## Installing from a local checkout

While developing, point `marketplace add` at a path instead of a repo:

```bash
claude plugin marketplace add ../gravitee-support-tools --scope local
```

A bare `.` is rejected — pass `./something`, a relative path, or an absolute
one. Relative paths are resolved and stored as **absolute**, so a path-based
declaration is never portable to another machine. That is precisely why the
team-facing instructions above use the GitHub shorthand.

## Layout

```
gravitee-support-tools/
├── .claude-plugin/
│   └── marketplace.json   # the catalogue — name, owner, plugins[]
├── p1-updates/            # a plugin, with its own .claude-plugin/plugin.json
└── README.md
```

Two manifests, two different files, easily confused:

- `.claude-plugin/marketplace.json` at **this** level lists the plugins.
- `.claude-plugin/plugin.json` inside **each plugin** describes that plugin.

Each entry in `plugins[]` points at its plugin with `source`. A relative path
like `./p1-updates` means the plugin lives in this same repository; plugins
hosted elsewhere use a `git` / `git-subdir` source object instead.

Metadata is duplicated between the two manifests on purpose: the marketplace
entry is what the catalogue shows *before* the plugin is fetched. Keep the
descriptions in step when a plugin changes. Version is deliberately **not**
repeated here — it is read from `plugin.json`, so there is one place to bump.

## Adding a plugin

1. Create the plugin directory here, with `.claude-plugin/plugin.json` inside it.
2. Add an entry to `plugins[]` in `.claude-plugin/marketplace.json`, with
   `"source": "./<dir>"`.
3. Validate both manifests:

   ```bash
   claude plugin validate . --strict            # the marketplace
   claude plugin validate ./<dir> --strict      # the plugin
   ```

`--strict` fails on unrecognised fields and missing metadata that the runtime
would otherwise tolerate — use it, and use it in CI.

To cut a release, `claude plugin tag ./<dir>` creates a `<name>--v<version>`
git tag and refuses if `plugin.json` and the marketplace entry disagree — which
is the drift this layout invites.

## Developing against a plugin

While iterating you usually do **not** want to install. Load the plugin in
place for a single session:

```bash
claude --plugin-dir ./p1-updates
```

This installs nothing and copies nothing. Edits to a `SKILL.md` body take
effect immediately; changes to `.mcp.json`, either manifest, or a newly added
skill directory need `/reload-plugins` or a restart.

If you *have* installed from the marketplace and then edit the source, run
`claude plugin marketplace update gravitee-support-tools` to pick the change up.
