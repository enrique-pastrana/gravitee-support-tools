---
description: Draft a reply to the customer based on what we know so far, and log it in the timeline.
argument-hint: [ticket-number]
---

You are drafting an outbound reply to the customer and logging it in the timeline.

> **⛔ INVARIANT — show before store.** A customer reply is **shown in chat and
> approved by the user before anything is written to disk.** The **first** thing
> you produce is the draft, in the chat, as a blockquote — never a
> `timeline.md` entry, never a file. You touch `bump_entry`/`timeline.md` **only
> after** an explicit "save / log it / ok" (step 7). This holds **even when the
> user's own words say "store it / almacénalo / guárdalo"** — treat that as
> "prepare it and show me", not as permission to write. Storing a reply the user
> hasn't seen is a bug, not a shortcut. (This rule also applies when a reply is
> asked for in plain language **without** the `/reply` command — the guard is the
> same.)

- Ticket data → the user's workspace `$TICKETS_ROOT` (default `~/TICKETS`).
- Plugin scripts/templates → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files
  into the workspace.
- Every helper takes the **bare** number and resolves the folder itself.

## Steps

1. **Resolve the ticket** — follow `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`:
   `$ARGUMENTS` > cwd > ask; state which ticket you resolved and
   how. `/reply` **writes**, so run the mismatch guards (explicit ≠ cwd,
   ticket doesn't exist) before drafting. Resolve the folder once:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
   ```

2. **Read the timeline cheaply, not end-to-end** (large ones are 30k+ tokens).
   Ground the draft in:
   - the `## 📋 Executive summary` — the current state of play;
   - the **last 3–5 entries** — a reply almost always answers the latest
     exchange. Find them with `grep -nE "^### \[" timeline.md`, then `Read` from
     the N-th-from-last header onward.
   Read further back only if the summary or recent entries point at an earlier
   finding (a reproduction, a root cause) you actually need to quote. This is the
   "never dump a big payload" rule of
   `${CLAUDE_PLUGIN_ROOT}/references/context-economy.md`; the drafting in steps
   4–7 stays **inline** — it happens with the user, don't delegate it.

3. **Ask the user** (in chat, not the file), skipping anything obvious from the
   timeline:
   - tone: standard / formal / more direct?
   - points to emphasise or omit?
   - if a fix is involved: validated locally, or proposed without reproduction?
   - **Check the previous outbound entry.** If it already asked the customer for
     something they haven't answered yet, don't repeat the same request —
     build on it (a nudge, or new information), or confirm with the user that a
     re-ask is intended.

4. **Compose the draft** in English — *in the chat, not to any file* — ready to
   paste into Zendesk:
   - Greeting (no first names unless the timeline shows them).
   - One short paragraph framing the problem as the customer sees it.
   - The analysis you ran (one or two paragraphs, no jargon dump).
   - Proposed action: numbered steps, config snippets in fenced code blocks.
   - A confirmation request ("could you apply this and let us know?").
   - Sign-off: `Best,\n<your name>` (the current user's first name).

5. **Show the draft in chat first**, as a blockquote so the user can read it. Do
   **not** touch `timeline.md` yet.

6. **Iterate in chat only.** Apply each round of tweaks (tone, structure, adds,
   cuts), keep showing the updated draft, save nothing yet.

7. **Wait for explicit confirmation to save.** Only a clear "save / add / log it"
   proceeds. Proposing more changes or asking for your opinion is **not** a save.

8. **Get the entry number (bump-first) and append.**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number>
   ```
   Prints the consumed `NNN` and refreshes `updated_at`. Append entry `[NNN]`
   with the **`Outbound reply draft`** snippet from
   `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`; the agreed draft sits
   inside as a blockquote.

9. **Update state — only if the reply changed it**; otherwise skip both parts.
   - **Status.** If the reply moves the case, confirm the new value with the
     user, then write it — don't hand-edit the JSON or header. Which value:
     asked the customer for info → **`waiting`** (the ball is in their court);
     still owe an action on our side → **`pending`**; confirmed resolution →
     `resolved`.
     ```bash
     python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <number> --set status=<status>
     python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_header.py" <number>
     ```
     `set_meta` writes `metadata.json` atomically; `render_header` rebuilds the
     timeline header from it, so the header, `/status`, and the metadata never
     drift. `render_header` already maps `pending`/`waiting`/`resolved`/etc. to
     the right label + emoji.
   - **Executive summary.** Refresh the `## 📋 Executive summary` prose (symptom,
     current hypothesis, caveats, pending, status — keep it short). It is the
     single source of truth `/status` and the next `/reply` read instead of the
     full timeline, so keep it self-contained and current.

## Non-substantive outbound messages

A pure holding message ("still investigating, will update soon"), an
acknowledgement, or a scheduling note carries no technical content. Per
`${CLAUDE_PLUGIN_ROOT}/references/classify-entry.md`, log it as a **one-line
entry** — `### [NNN] <date> - 🔔 <one sentence>` — no blockquote, no status or
summary change (still bump for the number). The full draft-and-iterate flow
above is only for replies that advance the case (analysis, a proposed fix, a
request for specific info).

## Don'ts

- **Don't write the timeline entry (or any file) before the user has seen the
  draft in chat and explicitly approved it** — see the invariant at the top. Not
  even if the request said "store it".
- Don't promise SLAs or timelines that aren't already agreed.
- Don't claim a fix is validated unless `timeline.md` has a 🧪 entry showing it
  was reproduced and the fix worked.
- Don't quote internal investigation Q&A in the customer reply.
