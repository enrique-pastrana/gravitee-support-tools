---
description: Draft a reply to the customer based on what we know so far, and log it in the timeline.
argument-hint: [ticket-number]
---

You are drafting an outbound reply to the customer and logging it in the timeline.

- Ticket data → the user's workspace `$TICKETS_ROOT` (default `~/TICKETS`).
- Plugin scripts/templates → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files
  into the workspace.
- Every helper takes the **bare** number and resolves the folder itself.

## Steps

1. **Resolve the ticket** — `$ARGUMENTS` if given, else infer from the cwd, else
   ask. Tickets are grouped by thousand, so the folder is
   `$TICKETS_ROOT/<thousand>/<number>/` (e.g. `16000/16575/`), not flat. Resolve
   it once:
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
   finding (a reproduction, a root cause) you actually need to quote.

3. **Ask the user** (in chat, not the file), skipping anything obvious from the
   timeline:
   - tone: standard / formal / more direct?
   - points to emphasise or omit?
   - if a fix is involved: validated locally, or proposed without reproduction?

4. **Write the draft** in English, ready to paste into Zendesk:
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
   - **Status.** If the reply moves the case (asked the customer for info →
     `pending`/`waiting`; confirmed resolution → `resolved`), confirm the new
     value with the user, then write it — don't hand-edit the JSON or header:
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

- Don't promise SLAs or timelines that aren't already agreed.
- Don't claim a fix is validated unless `timeline.md` has a 🧪 entry showing it
  was reproduced and the fix worked.
- Don't quote internal investigation Q&A in the customer reply.
