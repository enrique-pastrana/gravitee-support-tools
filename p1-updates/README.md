# p1-updates

A Claude Code plugin for the Gravitee support team. It turns a Fathom customer
call into a **who/what/when** P1 status summary, ready to paste into Slack.

## What it does

The plugin ships one skill, `updateP1`, and the Fathom MCP server it depends on.

```
/p1-updates:updateP1
```

With no argument it takes the most recent Fathom meeting. You can also name one
in plain language ("yesterday's call with X"), or paste a transcript directly
and skip Fathom entirely. Claude also invokes the skill on its own when you ask
for a P1 summary in conversation — the explicit command is not required.

The summary is printed in chat only. The skill writes nothing to disk and never
touches the ticket.

Customer and third-party names are stripped from the body: the two actors are
always **Gravitee** and **Customer**. Note that the line naming which meeting
was picked is *not* anonymised — it exists so a wrong pick gets caught, and it
is for you, not for the channel.

## Requirements

Fathom, connected through the MCP server this plugin declares in `.mcp.json`.

Authentication is OAuth, per person: the first time you use the plugin, open
`/mcp`, select `fathom`, and authorise with your own Fathom account. No token
is stored in this repository, and everyone sees only their own meetings.

## Layout

```
p1-updates/
├── .claude-plugin/
│   └── plugin.json        # manifest (name, version, metadata)
├── .mcp.json              # Fathom MCP server (HTTP + OAuth)
├── skills/                # skills — each a <name>/SKILL.md directory
│   └── updateP1/
│       └── SKILL.md
├── agents/                # subagent definitions (empty)
├── commands/              # flat .md skills (empty)
└── README.md
```

Only `plugin.json` lives under `.claude-plugin/`. Every other component sits at
the plugin root — including `.mcp.json`, which is the mistake most easily made.

## Local development

This directory is the plugin root. The parent folder is the marketplace
container and is not part of the plugin.

Validate the manifest from here:

```bash
claude plugin validate . --strict
```

To load it in a live session, pass `--plugin-dir` when starting Claude Code:

```bash
claude --plugin-dir /path/to/p1-updates
```

The flag loads the plugin in place for that session only. It installs nothing,
copies nothing, and leaves no files in the directory you launch from.

Edits to a `SKILL.md` body take effect immediately. Changes to `.mcp.json`, the
manifest, or a newly added skill directory do not — run `/reload-plugins` or
restart the session to pick those up.

If the MCP server fails to start, `claude --debug` shows the initialisation
error.

## Known gaps

- **Picking the latest meeting** relies on `list_meetings` returning the most
  recent first. If it ever picks the wrong call, that is the branch to fix. The
  skill always states which meeting it chose, so a bad pick is visible
  immediately rather than silent.
- **`search_meetings` matches titles and summaries, not participants.** Asking
  for a call by customer name only works when the name is in the meeting title.
  Adding `find_person`, which searches the participant index, would close this.
