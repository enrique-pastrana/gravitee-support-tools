---
description: Keep a running P1 war-room log for the ticket — you drop raw notes in any language, they're cleaned into concise English and filed under Current status / Next steps by actor in p1-log.txt. Also triggers in plain language ("vamos a tomar notas para este P1", "let's log this P1").
argument-hint: [nothing = start/resume | stop]
---

You keep a **live P1 log** for one ticket. The user throws raw notes (any
language); you clean each into concise **English**, classify it, and maintain
`p1-log.txt` in the ticket folder. The **file is the source of truth** — not the
conversation: reopening reads it and continues, so the log survives a fresh
session.

- Ticket data → `$TICKETS_ROOT`; scripts → `${CLAUDE_PLUGIN_ROOT}`.
- File: `<ticket>/p1-log.txt`. **Plain text — no Markdown, no symbols, no adornos.**
- Content is **English**, concise, factual: one action per `-` bullet.
- Internal log → **keep names as given** (colleagues and customer). No
  anonymising (unlike `/updateP1`, which strips names for Slack).

## Mode — from `$ARGUMENTS`

| `$ARGUMENTS` | Do |
|---|---|
| empty / `start` | Resolve ticket → create-or-reopen file → enter capture mode |
| `stop` | Stamp `closed <HH:MM>`, leave capture mode, then **offer** (don't auto-run) to fold a summary into `timeline.md` |

## Steps — start / resume

1. **Resolve the ticket** per `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`
   (chain **arguments > cwd > ask**). Writes a file → run the mismatch guards.
   State the ticket in one line.
2. **Create or reopen** `<ticket>/p1-log.txt`:
   - Exists → read it, show current contents, continue from there.
   - Missing → create with this skeleton (`<customer>` from `metadata.json`):
     ```
     P1 notes - <ticket> - <customer>
     opened <YYYY-MM-DD HH:MM>

     CURRENT STATUS

     NEXT STEPS
     ```
3. **Enter capture mode**: say "capture on". Every following user message is a
   note until a control word (below).

## Filing a note

- **Clean** → concise English, **one action per `-` bullet**. Split a message
  into several bullets if it holds several actions.
- **Classify**:
  - **Section** — happening / established now → `CURRENT STATUS`; planned / owed
    → `NEXT STEPS`.
  - **Actor** — our side (named colleagues, "we", Gravitee) → `Gravitee`;
    customer side → `Customer`. Ambiguous → ask. User may override.
- **Layout**, actor and bullets at 2-space indent:
  ```
  CURRENT STATUS
    Gravitee
    - <action>
    Customer
    - <action>
  ```
- **Omit an actor with no items** — never leave an empty subsection.
- **`When:` — NEXT STEPS only.** End each actor block with one `When:` line, a
  natural-language deadline (`EOD today`, `tomorrow morning`, `next 30 min`). One
  per actor; if its bullets carry different deadlines, summarise them on it.
- **Move items as reality changes**: `NEXT STEPS` → `CURRENT STATUS` when work
  starts; append `(done HH:MM)` when it finishes.
- **Confirm** each note in one line: what you filed + where.

## Control words — any language

| Says | Effect |
|---|---|
| `para` / `pausa` / `stop` | Pause capture — answer normally, **don't** file messages |
| `sigue` / `reanuda` / `continúa` | Resume capture |
| re-running `/p1-log` | Reopen the file and resume |

## Don'ts

- Don't write Markdown or symbols — plain text, `-` bullets only.
- Don't invent actions or deadlines — file only what's said; ask if the actor is
  unclear.
- Don't file control words as notes.
- Don't touch `timeline.md` unless the user accepts the offer at `stop`.
