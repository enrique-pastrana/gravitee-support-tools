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

## Using it

Three ways in, depending on what you have:

```
/p1-updates:updateP1                          the most recent Fathom meeting
/p1-updates:updateP1 yesterday's OCTO call    a meeting you name
/p1-updates:updateP1 <paste a transcript>     no Fathom call at all
```

You do not have to type the command. Asking in conversation works too, because
the skill is model-invoked:

> give me a P1 update from the last call

> P1 summary from yesterday's call with the customer

When it names a meeting rather than taking the latest, it searches titles and
summaries. If several match, or none do, it lists the candidates and asks you to
pick instead of guessing.

It always opens by stating which meeting it used — check that line first, since
a wrong pick is otherwise invisible. Then it prints:

```
Current status
Who: Gravitee
What:
- …

When: …

Next steps
Who: Customer
What:
- …

When: …
```

Actors with nothing to report are omitted, so it is normal to see only Gravitee
under *Current status* and only Customer under *Next steps*. Nothing is written
to disk — copy it into Slack yourself, and ask for tweaks first if it needs
them.

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
container and is not part of the plugin — so `--plugin-dir` and
`claude plugin validate` are pointed *here*, not one level up.

```bash
claude --plugin-dir /path/to/p1-updates
```

For the rest — validating, reloading after an edit, installing from a local
checkout, releases — see [CONTRIBUTING.md](../CONTRIBUTING.md).

One thing specific to this plugin: because it declares an MCP server,
`/reload-plugins` invalidates the prompt cache and can refuse to apply, telling
you to pass `--force`. Restarting the session avoids the question. If Fathom
fails to come up, `claude --debug` shows the initialisation error.

## Known gaps

- **Picking the latest meeting** relies on `list_meetings` returning the most
  recent first. If it ever picks the wrong call, that is the branch to fix. The
  skill always states which meeting it chose, so a bad pick is visible
  immediately rather than silent.
- **`search_meetings` matches titles and summaries, not participants.** Asking
  for a call by customer name only works when the name is in the meeting title.
  Adding `find_person`, which searches the participant index, would close this.
