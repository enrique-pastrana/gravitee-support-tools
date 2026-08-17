# Getting started with the `tickets` plugin

A friendly first-time guide. If you just installed the plugin and want to know
what it does and how to use it day to day, start here. (For setup internals and
the porting status, see the [README](../README.md) and
[PORTING.md](../PORTING.md).)

> **Work in progress.** A first set of commands is ready (`tickets-up`,
> `new-ticket`, `log-updates`, `reply`, `status`); more are on the way. This
> guide covers what works today.

## What is this?

It turns each Zendesk support ticket into a **living document** you build up as
you work the case — one folder per ticket, with a single `timeline.md` that
tells the whole story in order. Instead of your context being scattered across
Zendesk comments, Slack, local notes and log files, everything lands in one
place, and Claude Code helps you fill it in.

You drive it with slash commands (`/new-ticket`, `/log-updates`, `/reply`, …).
Each command does one job: pull the ticket in, log what the customer said, draft
a reply, print a status.

## The mental model (read this once)

**One folder per ticket**, in *your* workspace — not inside the plugin. By
default that's `~/TICKETS`; tickets are grouped by thousand, so ticket 17952
lives in:

```
~/TICKETS/17000/17952/
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

## One-time setup

You need two things set once, and the backing stack running.

**1. Tell the plugin where your ticket data goes** (optional — defaults to
`~/TICKETS`):

```bash
export TICKETS_ROOT="$HOME/TICKETS"
```

**2. Tell it where your `ia-tooling` checkout is** (required — this is how it
reaches Zendesk, search, etc.):

```bash
# add to ~/.zshrc or ~/.bashrc
export IA_TOOLING_ROOT="$HOME/ia-tooling"
```

**3. Start the backing stack** (Docker + Ollama + the local services), from a
Claude Code session with the plugin loaded:

```
/tickets-up
```

Run `/tickets-up` first each session. If any other command tells you the stack
is down, come back and run it again — it's the single place that starts and
heals the stack.

## A day in the life

A typical case, start to finish:

1. **Bring the stack up:** `/tickets-up`
2. **Open the ticket:** `/new-ticket 17952`
   Creates the folder, pulls subject/customer/priority + the opening message and
   attachments from Zendesk, logs it as entry `[001]`, and shows you any similar
   past tickets.
3. **Work the case.** Read the attachments, investigate, reproduce.
4. **The customer (or a colleague) replies:** `/log-updates`
   Pulls everything new on the Zendesk thread since you last checked and logs it
   as summarised entries.
5. **Answer them:** `/reply`
   Drafts a reply grounded in the case, shows it to you in chat, and lets you
   iterate. It only writes the reply into the timeline once you say to save it.
6. **Glance at where things stand any time:** `/status`

## The commands you have today

| Command | What it does | When to use it |
|---|---|---|
| `/tickets-up` | Starts and verifies the `ia-tooling` stack. | First thing each session, or whenever a command says the stack is down. |
| `/new-ticket <number>` | Creates the ticket folder, fills it from Zendesk, logs the opening message, finds similar tickets. | When you pick up a new ticket. |
| `/log-updates [number]` | Pulls new Zendesk activity (customer messages, replies, internal notes) into the timeline as summarised entries, with attachments. | Whenever there's new activity on the ticket. |
| `/reply [number]` | Drafts an outbound reply, iterates with you in chat, and logs it only on your confirmation. | When it's time to answer the customer. |
| `/status [number]` | Prints a concise summary — state, entry count, attachments, last entry. Read-only. | To catch up on a ticket at a glance. |

`[number]` is optional when you're already working inside a ticket's folder —
the command infers it. Give the number explicitly from anywhere else.

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
