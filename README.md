# gravitee-support-tools

A Claude Code **marketplace** for the Gravitee support team — the catalogue the
team installs plugins from.

> **Want to add a plugin, or work on one?** Everything about the repository
> layout, the two manifests, local development and releases lives in
> **[CONTRIBUTING.md](CONTRIBUTING.md)**. This page is for installing and using
> what is already here.

## Plugins

| Plugin | What it does |
| --- | --- |
| [`p1-updates`](p1-updates/) | Turns a Fathom customer call into a who/what/when P1 status summary, ready to paste into Slack. |

## Installing

Adding the marketplace and installing a plugin are two separate steps — the
catalogue on its own installs nothing.

### From inside Claude Code

`/plugin` opens an interactive panel with four tabs: **Discover**, **Installed**,
**Marketplaces** and **Errors**. The same two steps also work as slash commands:

```
/plugin marketplace add enrique-pastrana/gravitee-support-tools
/plugin install p1-updates@gravitee-support-tools
```

`/plugin install` opens the plugin's details and **asks** which scope you want
before installing. The Discover tab shows the same details — the components it
adds and its context cost — if you would rather browse than type.

Then `/reload-plugins` activates it without restarting.

### From the shell

```bash
claude plugin marketplace add enrique-pastrana/gravitee-support-tools
claude plugin install p1-updates@gravitee-support-tools
```

The difference is that the shell command **never asks**: it installs to user
scope unless you pass `--scope`. Use it for scripting; use `/plugin` when you
want to see what you are getting.

Either way, installing does not load the plugin into sessions that are already
open — run `/reload-plugins` or start a new one.

Skills are namespaced by plugin, so `updateP1` is invoked as
`/p1-updates:updateP1`.

### Fathom authentication

`p1-updates` talks to Fathom through an MCP server. Authentication is OAuth and
**per person**: open `/mcp`, select `fathom`, and authorise with your own
account. No token lives in this repository — it is stored on your own machine,
and everyone sees only their own meetings.

## Scopes

Both `marketplace add` and `install` take `--scope`.

| scope | declared in | who sees it |
| --- | --- | --- |
| `user` (default) | `~/.claude/settings.json` | you, in every directory |
| `project` | `<dir>/.claude/settings.json` | anyone who opens that directory — committed |
| `local` | `<dir>/.claude/settings.local.json` | only you, only in that directory |

The directory you run from does not scope anything by itself — only the flag
does. And `uninstall` defaults to `user` whatever the plugin was installed as,
so undoing a local install needs `--scope local` explicitly.

To put the marketplace in front of the whole team at clone time, declare it at
project scope so it lands in a committed `settings.json`:

```bash
claude plugin marketplace add enrique-pastrana/gravitee-support-tools --scope project
```

## Checking and uninstalling

```bash
claude plugin marketplace list
claude plugin list
```

To back out:

```bash
claude plugin uninstall p1-updates@gravitee-support-tools
claude plugin marketplace remove gravitee-support-tools
```

Removing a marketplace uninstalls every plugin you installed from it, so the
second command alone is enough if you want the lot gone.

To switch a plugin off without removing it — and back on later — use
`claude plugin disable` and `claude plugin enable`. That keeps the install and
your Fathom authentication intact.

## Troubleshooting

**The clone fails.** `marketplace add` has been observed cloning over SSH
(`git@github.com:…`) even with `gh config get git_protocol` set to `https`. The
repository is public, but a missing GitHub SSH key is the first thing to check.

**Uninstalling did not free the disk.** `uninstall` leaves the plugin files in
`~/.claude/plugins/cache/<marketplace>/`, marked with an `.orphaned_at` stamp so
a reinstall is instant. `claude plugin prune` does **not** clear that — it only
handles auto-installed dependencies. Delete the directory by hand.

**The skill does not appear.** Installing does not affect open sessions: run
`/reload-plugins` or start a new one. If it still does not show up, clear the
cache with `rm -rf ~/.claude/plugins/cache`, restart, and reinstall.

## Contributing

Adding a plugin, changing an existing one, or cutting a release — see
**[CONTRIBUTING.md](CONTRIBUTING.md)**.
