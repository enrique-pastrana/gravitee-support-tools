# Getting started with the `tickets` plugin

A friendly, first-time guide: how to **install** the plugin, **configure** it, and
then use it day to day. Follow it top to bottom the first time; after that you'll
only come back for the command reference. (For repository/setup internals see the
[README](../README.md) and [PORTING.md](../PORTING.md).)

## What is this?

It turns each Zendesk support ticket into a **living document** you build up as
you work the case — one folder per ticket, with a single `timeline.md` that
tells the whole story in order. Instead of your context being scattered across
Zendesk comments, Slack, local notes and log files, everything lands in one
place, and Claude Code helps you fill it in.

You drive it with slash commands (`/new-ticket`, `/log-updates`, `/investigate`,
`/reply`, …). Each command does one job: pull the ticket in, log what the
customer said, record an investigation step, draft a reply, print a status.

---

## 1. Install it (once per machine)

The plugin ships through a Claude Code **marketplace** (a catalogue). Installing
is two steps: add the catalogue, then install the plugin from it.

Run these inside any Claude Code session (terminal or VS Code):

```
/plugin marketplace add enrique-pastrana/gravitee-support-tools
/plugin install tickets@gravitee-support-tools
```

- The first line registers the catalogue (it's a public GitHub repo, so the
  `owner/repo` shorthand is enough — no clone, no path).
- The second opens the plugin's details and **asks which scope** you want.
  Choose **User** — it installs it for your whole machine, every project.
- If the session says *"Run `/reload-plugins`"*, run it. Otherwise it's active
  immediately.

Prefer a menu? Just run `/plugin`, go to **Discover**, pick **tickets**, and
install from there — same result.

### It's available in the terminal *and* in VS Code — automatically

Installing to **User** scope writes to `~/.claude/settings.json`, and **both the
terminal CLI and the VS Code extension read that same file.** So you install
once and it's there in both places. If a surface was already open when you
installed, restart it or run `/reload-plugins`; new sessions pick it up on their
own.

### Keeping it up to date

When the plugin gets new versions, refresh the catalogue and reload:

```
/plugin marketplace update gravitee-support-tools
/reload-plugins
```

> **Note for the dev flow:** while developing the plugin we loaded it with
> `claude --plugin-dir …`. That's session-only and for testing. For real daily
> use, install it from the marketplace as above — it persists across restarts and
> is the same in every session and surface.

---

## 2. Configure it (once)

The plugin has **no config file of its own** — it's configured entirely with a
few environment variables. Here's the whole list:

| Variable | Required? | What it points to | Default |
|---|---|---|---|
| `IA_TOOLING_ROOT` | **Required** | Your `ia-tooling` checkout — how the plugin reaches Zendesk, search, the vector DB and (read-only) Grafana. | — |
| `TICKETS_ROOT` | Optional | Where your ticket folders are created and stored. | `~/TICKETS` |
| `KB_REPO` | Optional* | Your knowledge-base GitHub repo, as `owner/name`. | — |
| `IA_TOOLING_ENV` | Optional | Your `ia-tooling` `.env` file, only if it isn't at the default place. | `$IA_TOOLING_ROOT/.env` |
| `GRAVITEE_STACKER_BIN` | Optional | The `gravitee-stacker` binary, only if you use `/stack` and it isn't on your `PATH`. | on `PATH` |

\* Needed only for the KB commands (`/kb-candidate`, `/kb`, `/kb-publish`).

Your **Zendesk credentials are not set here** — they live in the `ia-tooling`
`.env` file, which the plugin finds at `$IA_TOOLING_ROOT/.env`.

### Where to put these so BOTH terminal and VS Code see them

This is the one gotcha worth getting right. The **reliable, works-everywhere**
place is the `env` block in **`~/.claude/settings.json`** — Claude Code reads it
the same way whether you're in the terminal or the VS Code extension:

```jsonc
// ~/.claude/settings.json
{
  "env": {
    "IA_TOOLING_ROOT": "/Users/you/ia-tooling",
    "TICKETS_ROOT":    "/Users/you/TICKETS",
    "KB_REPO":         "your-org/kb-articles"
  }
}
```

> **Use full absolute paths here** (`/Users/you/…`, not `~` or `${HOME}`). This
> block takes values literally — shell expansion is not guaranteed. Only add the
> lines you need; `IA_TOOLING_ROOT` is the only required one.

**Alternative — shell profile.** If you only use the terminal, or prefer your
`~/.zshrc`, exports work there and `${HOME}` expands normally:

```bash
# ~/.zshrc
export IA_TOOLING_ROOT="${HOME}/ia-tooling"
export TICKETS_ROOT="${HOME}/TICKETS"
export KB_REPO="your-org/kb-articles"
```

Just know that **the VS Code extension may not inherit your `~/.zshrc`**. If you
go this route and use VS Code, either launch it from a terminal with `code .`
(so it inherits your shell), or use the `settings.json` method above — which is
why it's the recommendation.

### KB repo — one-time repo setup

If you'll use the KB commands, `KB_REPO` points at a GitHub repo you own (one
article per file). The first time, you create it **private** and add two labels
plus an `articles/` folder — a couple of `gh` commands. There's also an
**optional** kanban board (a GitHub Project) to see the pipeline at a glance.
Full step-by-step in
[the KB workflow reference](../references/kb-workflow.md#one-time-repo-setup-per-user).

### Start the backing stack

Finally, from a session with the plugin loaded, bring up the stack (Docker +
Ollama + the local services):

```
/tickets-up
```

Run `/tickets-up` first each session. If any command later says the stack is
down, come back and run it again — it's the single place that starts and heals
the stack.

---

## The mental model (read this once)

**One folder per ticket**, in *your* workspace (`$TICKETS_ROOT`) — not inside the
plugin. Tickets are grouped by thousand, so ticket 17952 lives in:

```
$TICKETS_ROOT/17000/17952/
├── timeline.md      ← the story of the case, in order
├── metadata.json    ← structured facts (customer, product, status, …)
└── received/        ← attachments downloaded from Zendesk
```

**`timeline.md` has three parts:**

- **📋 Executive summary** — the current state of play (symptom, hypothesis,
  what's pending). This is the **single source of truth**. Keep it current: it's
  what `/status` and `/reply` read instead of re-reading the whole history.
- **🕐 Chronological timeline** — numbered entries `[001]`, `[002]`, … one per
  event (a customer message, a reply you sent, an investigation step).
- **📚 KB article draft** — filled in at the end, once the case is resolved.

**Entries are summaries, not transcripts.** When the plugin logs a Zendesk
message it writes the *main points* plus any load-bearing specifics (exact
errors, versions, config) verbatim — and keeps a `🔗 Zendesk comment #<id>`
pointer so you can always jump back to the exact words in Zendesk. This keeps
the timeline cheap to read.

## A day in the life

A typical case, start to finish:

1. **Bring the stack up:** `/tickets-up`
2. **Open the ticket:** `/new-ticket 17952`
   Creates the folder, pulls subject/customer/priority + the opening message and
   attachments from Zendesk, logs it as entry `[001]`, and shows you any similar
   past tickets.
3. **Work the case.** Read the attachments and dig in:
   - `/investigate <question>` records an analysis step — it answers your
     question grounded in the case (searching past tickets, Jira, the docs),
     iterates with you in chat, and logs the Q&A as a collapsible 🔍 entry once
     you confirm.
   - `/reproduce` scaffolds a `reproduction/` folder (steps, environment,
     configs, results) and logs a 🧪 milestone as you confirm or rule out the bug.
   - `/stack up` spins up a local Gravitee stack to test against (see below).
4. **The customer (or a colleague) replies:** `/log-updates`
   Pulls everything new on the Zendesk thread since you last checked and logs it
   as summarised entries.
5. **Answer them:** `/reply`
   Drafts a reply grounded in the case, shows it to you in chat, and lets you
   iterate. It only writes the reply into the timeline once you say to save it.
6. **Glance at where things stand any time:** `/status`
7. **Wrap it up:** `/close`
   Once the customer confirms, mirrors the ticket's terminal state from Zendesk
   (solved → resolved, closed → closed), stamps the resolution and logs a ✅ entry.
8. **Capture the knowledge (optional):** if the case is worth documenting,
   `/kb-candidate <reason>` → `/kb` → `/kb-publish` turns it into a published KB
   article (see the commands table and the KB workflow reference).

## The commands you have

| Command | What it does | When to use it |
|---|---|---|
| `/tickets-up` | Starts and verifies the `ia-tooling` stack. | First thing each session, or whenever a command says the stack is down. |
| `/new-ticket <number>` | Creates the ticket folder, fills it from Zendesk, logs the opening message, finds similar tickets. | When you pick up a new ticket. |
| `/log-updates [number]` | Pulls new Zendesk activity (customer messages, replies, internal notes) into the timeline as summarised entries, with attachments. | Whenever there's new activity on the ticket. |
| `/investigate <question> [number]` | Answers a question grounded in the case (past tickets, Jira, docs, live Grafana metrics/logs), iterates in chat, logs the Q&A as a 🔍 entry. | While digging into the cause of the problem. |
| `/reproduce [number]` | Scaffolds a `reproduction/` folder and logs a 🧪 milestone (reproduced / not reproduced). | When you try to reproduce the reported bug. |
| `/stack <up\|list\|down\|clean> [apim\|am\|gamma][@version] [number]` | Spins up / lists / tears down a local Gravitee stack — standalone APIM/AM (per-ticket, via `gravitee-stacker`) or the version-selectable Gamma singleton (via its official docker-compose) — scoped to the ticket and logged as a 🛠️ entry. | When you need a live environment to reproduce or test against. |
| `/reply [number]` | Drafts an outbound reply, iterates with you in chat, and logs it only on your confirmation. | When it's time to answer the customer. |
| `/status [number]` | Prints a concise summary — state, entry count, attachments, last entry. Read-only. | To catch up on a ticket at a glance. |
| `/sync [number]` | Compares local folders against live Zendesk and reports the drift (closed-in-ZD, new activity, metadata mismatches), sorted by severity. Read-only — suggests fixes, never applies them. | Periodically, to catch tickets that moved on Zendesk while your local snapshot went stale. With no number it sweeps the whole active queue. |
| `/close [number]` | Mirrors the ticket's terminal state from Zendesk, stamps the resolution, logs a ✅ entry. | Once the customer confirms the case is done. |
| `/kb-candidate <reason> [number]` | Flags the ticket as worth a KB article — opens a tracking Issue in your `$KB_REPO` (labeled `kb:candidate`) and records it on the ticket. | Mid-flow, the moment you realise a case is worth documenting. Needs `KB_REPO` set (see setup). |
| `/kb [number]` | Turns a candidate into a draft article: generates it from the timeline, iterates with you in chat, then opens a draft PR (`kb:draft`) in your `$KB_REPO`. | Once the case is resolved and you want to write up the KB article. Needs `KB_REPO` set. |
| `/kb-publish [number]` | Merges the draft PR (closing the candidate Issue), indexes the article into the vectordb, and records the published URL on the ticket. | Once the draft PR is reviewed and approved. Needs `KB_REPO` set. |

`[number]` is optional — the command resolves the ticket from what you're working
on: an explicit number wins, otherwise it uses the **ticket folder you're `cd`'d
into** (the window's current ticket), and only asks if it can't tell. Say "let's
work on `<number>`" to move the window into that ticket; give a number explicitly
to act on a different ticket as a one-off. (For `/investigate`, the free text is your **question**, not the number —
pass the number after it if you need to.)

`/stack` is optional and needs the external
[`gravitee-stacker`](https://github.com/zach-sirotkin/gravitee-stacker) tool plus
Docker — see [Local Gravitee stacks in the README](../README.md#local-gravitee-stacks-stack-optional).
Without it every other command works fine.

### Publishing a KB article — reviewing on GitHub first

`/kb` opens the draft as a **pull request** in your `$KB_REPO`. The natural,
safest way to publish is to **review and merge that PR on GitHub yourself**, then
run `/kb-publish` — it notices the PR is already merged and just does the
bookkeeping (fetches the article, indexes it into the vectordb, records the
published URL on the ticket, closes the candidate Issue).

Alternatively, `/kb-publish` can do the merge for you. Because merging is an
outward, irreversible action, Claude Code will ask you to confirm the `gh pr
merge` command the first time. If you publish often and want to skip that prompt,
add an allow rule to your settings:

```jsonc
// ~/.claude/settings.json
{ "permissions": { "allow": ["Bash(gh pr merge:*)"] } }
```

## When the stack is down

Most commands degrade gracefully instead of failing:

- `/new-ticket` and `/log-updates` fall back to a **paste flow** — you paste the
  content and drag attachments in manually, and they log it the same way.
- `/status` is fully local and never needs the stack.
- Indexing and cross-ticket search do need the stack — run `/tickets-up` first.

## Tips

- **Keep the executive summary current.** It's the shortcut every other command
  relies on; a stale summary makes replies and statuses worse.
- **Don't paste huge logs into the timeline.** Attachments live in `received/`
  and are linked — the timeline stays readable.
- **The `comment_id` footer is your friend.** Entries summarise; when you need
  the customer's exact words, that pointer takes you straight to the Zendesk
  comment.
