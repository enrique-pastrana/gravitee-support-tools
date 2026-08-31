# Reference: keeping heavy work out of the main context

The main session's context window is a scarce resource — the room the command has
left to reason, hold the timeline, and talk to the user. Payload-heavy retrieval
and fan-out searches can fill it with raw material the command never needs to see
in full. This is the shared discipline for **delegating that heavy lifting to a
subagent** so only a distilled result lands in the main context. Shared by
`/log-updates`, `/investigate`, `/reproduce`, `/status`, `/reply` and `/kb`, so
the rule reads the same everywhere. Paths assume `${CLAUDE_PLUGIN_ROOT}` (plugin).

## The rule

**Delegate the heavy, mechanical, high-payload work; keep the reasoning and the
user-facing work inline.**

- **Delegate to a subagent** — fetching + parsing a large payload, or fanning out
  across sources, where the raw material is bulky and the command only needs the
  gist:
  - a full Zendesk thread (`zendesk_get_ticket_with_attachments` and friends) —
    the subagent returns the new comments as summaries, not the raw dump;
  - a Jira issue or a batch of them;
  - a fan-out of searches (several `rag_search`, `zendesk_search_tickets`,
    `searchJiraIssuesUsingJql`, `gh search` runs) — the subagent runs them and
    returns the handful of genuinely relevant hits;
  - grinding through a big local artifact (a 30k-token `timeline.md`, a long log)
    to pull out the few lines that matter.
- **Keep inline** — the command's own judgement and anything the user is in the
  loop for:
  - the diagnostic reasoning of `/investigate` — think in the main thread;
  - drafting and iterating a customer reply in `/reply` — that happens *with* the
    user, turn by turn;
  - writing the timeline entry, deciding status, refreshing the summary;
  - every confirmation gate and user-facing decision.

Not a blanket "always delegate." Delegating the reasoning would defeat the point;
delegating the bulky fetch is exactly the point.

## How to delegate

Spawn a subagent with a **narrow brief and a distilled deliverable**: tell it
what to fetch or search, and to return only the digest the command needs — never
the raw payload. For example: "Fetch Zendesk ticket 18242 and its comments; return
each comment after `<cursor>` as `id · date · author · one-line summary`, plus any
attachment filenames — do not paste the raw thread." The subagent burns its own
context on the bulk; the main session receives the short answer.

## Never dump a big payload into the main context

Even without a subagent, a large tool result or file must not be read whole into
the main thread just to grab a fraction of it:

- **Parse on disk first** — `grep`/`find`/`jq`, or `Read` with `offset`/`limit`,
  to reach only the region you need (this is why `/status` and `/reply` grep for
  entry headers instead of reading `timeline.md` end-to-end).
- If the extraction itself is heavy, that *is* a delegation — hand it to a
  subagent per the rule above.

The test is simple: **would the raw material fill context with tokens the command
never uses?** If yes, delegate it or parse it down first; keep only the distilled
result.
