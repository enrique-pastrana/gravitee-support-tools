---
description: Draft a reply to the customer based on what we know so far, and log it in the timeline.
argument-hint: [ticket-number]
---

You are drafting an outbound reply.

Ticket data lives in the user's tickets workspace, `$TICKETS_ROOT` (default
`~/TICKETS`). The plugin's machinery lives under `${CLAUDE_PLUGIN_ROOT}` — refer
to scripts and templates there, never inside the tickets workspace.

## Steps

1. **Resolve the current ticket:** `$ARGUMENTS` if provided, else infer from the
   cwd. If still ambiguous, ask. Tickets are grouped by thousand, so the folder
   is `$TICKETS_ROOT/<thousand>/<number>/` (e.g. `16000/16575/`), not flat.
   Resolve it once with the shared helper:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
   ```
   The `bump_entry` helper takes the **bare number** and resolves the bucket
   itself; timeline edits happen in that folder.
2. **Read the timeline cheaply, not end-to-end** (large timelines are 30k+
   tokens). Ground the draft in:
   - The `## 📋 Executive summary` section — the current state of play.
   - The **last few entries** (roughly the last 3–5), since a reply almost
     always answers the most recent exchange. Locate them with
     `grep -nE "^### \[" timeline.md` and `Read` from the offset of the
     N-th-from-last header onward.
   Only read further back if the summary or recent entries point at an
   earlier finding (a reproduction, a root cause) that you actually need to
   quote. Don't load the whole timeline by default.
3. **Ask the user** (in chat, not in the file):
   - tone: standard / formal / more direct?
   - any specific points to emphasise or omit?
   - if a fix is involved: do we have it validated locally, or are we
     proposing it without reproduction?
   Skip questions whose answer is obvious from the timeline.
4. **Write the draft** in English, ready to paste into Zendesk. Structure:
   - Greeting (no first names unless the timeline shows them).
   - One short paragraph framing the problem the way the customer sees it.
   - The analysis you ran (one or two paragraphs, no jargon dump).
   - The proposed action: numbered steps, with config snippets in fenced
     code blocks.
   - A confirmation request ("could you apply this and let us know?").
   - Sign-off: `Best,\n<your name>` (use the current user's first name).
5. **Show the draft in chat first.** Do NOT touch `timeline.md` yet. Print
   the full draft as a blockquote so the user can read it.
6. **Iterate.** The user will likely ask for tweaks (tone, structure,
   additions, cuts). Apply each round in chat only — keep showing the
   updated draft in chat, don't save anything yet.
7. **Wait for explicit confirmation to save.** Only when the user clearly
   says to save/add/log it, proceed with the steps below. Proposing more
   changes or asking for your opinion does NOT mean save.
8. **Get the entry number (bump-first) and append.** Run
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket>` once — it
   increments `next_entry`, refreshes `updated_at`, and **prints the number it
   just consumed**; use that as `NNN`. Then append entry `[NNN]` to
   `timeline.md` using the `outbound reply draft` snippet from
   `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md`. The final agreed draft
   sits inside the entry as a blockquote.
9. **Refresh the `## 📋 Executive summary` section** of `timeline.md` if the
    reply changes the state of play (asking for new info, proposing a fix,
    confirming resolution). Keep it short: symptom, current hypothesis,
    caveats, pending, status. Skip if the reply doesn't change anything.
    This summary is the **single source of truth** that `/status` and the next
    `/reply` read instead of the full timeline — keep it self-contained and
    current so those commands never need to re-read the whole document.

## Logging non-substantive outbound messages

Not every outbound message is a real reply. A pure holding message ("we're
still investigating, will update soon"), an acknowledgement, or a scheduling
note carries no technical content. Classify as in
`${CLAUDE_PLUGIN_ROOT}/references/classify-entry.md`: log those as a **one-line
entry** — `### [NNN] <date> - 🔔 <one sentence>`, no blockquote, no summary
refresh — the same way `/log-updates` treats non-substantive incoming messages.
The full draft-and-iterate flow above is for replies that actually advance the
case (analysis, a proposed fix, a request for specific info).

## Don'ts

- Don't promise SLAs or timelines that aren't already agreed.
- Don't claim a fix is validated unless `timeline.md` has a 🧪 entry showing
  it was reproduced and the fix worked.
- Don't quote internal investigation Q&A in the customer reply.
