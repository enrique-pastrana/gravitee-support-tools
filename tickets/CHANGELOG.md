# Changelog

All notable changes to the **tickets** plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Rule of thumb:** every bump of `version` in
> [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) gets a matching entry
> here, in the same PR — so the changelog never drifts from what shipped.

## [0.0.14] - 2026-09-02

### Added
- **`/escalate` command — draft an L3 / engineering escalation (bug / problem /
  question).** Second PR of the escalation / feature-request slice (foundation
  landed in 0.0.13). Resolves the ticket, picks the type (from your words or
  `$ARGUMENTS`, else asks), and fills the matching template —
  `templates/bug-report.md`, `templates/l3-problem.md`, or
  `templates/l3-question.md` — autofilling Open Date, installation type, component
  versions (APIM/GKO/AM), database and the investigation/repro from
  `metadata.json` + the timeline. Reads the timeline cheaply
  (`references/context-economy.md`); **never fabricates** engineering-facing
  content (asks or leaves `‹TODO›`). Shows the draft verbatim in a code block,
  iterates in chat, and — following the same show-before-store rule as `/reply` —
  logs nothing until **you** have pasted it into Zendesk and confirmed: then it
  appends a 🚀 `L3 escalation` timeline entry (new snippet in
  `templates/entry-snippets.md`) and offers to move the ticket to `on hold`. Any
  L3-context fields you supply are persisted via `set_meta.py` so future
  escalations autofill.

## [0.0.13] - 2026-09-02

### Added
- **Metadata fields for the escalation / feature-request slice.** New nullable
  fields in `templates/metadata.json` and `scripts/set_meta.py`:
  `installation_type`, `apim_version`, `gko_version`, `am_version`, `database`
  (L3 escalation context, shared by the upcoming `/escalate problem|question`);
  `csm`, `tam`, `ae` (account contacts, used by the `/feature-request` closing
  message); and `fr_status` (feature-request lifecycle: `null → intake_sent →
  submitted`). All are plain nullable strings — set them with `set_meta.py`, clear
  with the literal `null`, same as the `kb_*` fields. Foundation only; the
  `/escalate` and `/feature-request` commands land in follow-up PRs.

## [0.0.12] - 2026-09-01

### Added
- **`/remove-ticket` command — delete a ticket folder (destructive).** Ported from the
  standalone `~/TICKETS` workspace. Resolves the ticket (via the shared
  `references/resolve-ticket.md` chain, `$ARGUMENTS` > cwd > ask), resolves the folder
  through `ticket_paths.py` (thousand-bucket aware), shows a **recap** of what will be
  deleted (subject / customer / status from metadata, entry count, attachment count,
  raw `ls -la`), then requires an explicit **AskUserQuestion** confirmation before
  `rm -rf`-ing the resolved path. A **safety guard** refuses to delete `$TICKETS_ROOT`
  itself, a bare thousand-bucket, or any path resolving outside `$TICKETS_ROOT`. On
  confirmation, if the shell's cwd was inside the deleted folder it `cd`s back to
  `$TICKETS_ROOT` so the window isn't stranded (the current-ticket signal is the cwd
  since 0.0.5), and the empty thousand-bucket is left in place. Prompt-only; new
  [`commands/remove-ticket.md`](commands/remove-ticket.md); README and getting-started
  updated.

## [0.0.11] - 2026-09-01

### Added
- **`/sync` command — local ↔ Zendesk reconciliation (read-only).** Ported from the
  standalone `~/TICKETS` workspace. Compares local ticket folders against live
  Zendesk (the source of truth) and reports the drift, sorted into severity buckets:
  🔴 closed in Zendesk but active locally (suggest `/close`), 🟠 new Zendesk activity
  newer than the local `updated_at` (suggest `/log-updates`), 🟡 metadata mismatch on
  customer / version / priority / Jira key (Zendesk wins), 🟢 aligned. With a ticket
  number it syncs just that one; with no argument it sweeps the **active queue** —
  every numeric folder whose local `status` isn't terminal (`resolved`/`closed`),
  enumerated across the thousand-bucket layout. Shows Zendesk's **raw** status (`hold`
  = engineering, `pending` = customer) without translating it to local vocabulary,
  checks Zendesk reachability via `zendesk_health` first (→ `/tickets-up` on failure),
  and runs the full-queue fan-out through a subagent to keep the JSON dumps off the
  main context. **Strictly read-only** — it suggests the fix command but never writes
  to Zendesk or any local file. The Jira-key check reads both the local `jira` field
  and `related_tickets` to avoid false positives. Prompt-only; new
  [`commands/sync.md`](commands/sync.md); README and getting-started updated.

## [0.0.10] - 2026-09-01

### Added
- **Read-only Grafana MCP wired in.** `ia-tooling` now exposes a `grafana` server
  through `local-tooling mcp grafana` (`grafana_health`, `grafana_list_datasources`,
  `grafana_query`, `grafana_logs_link` — dashboard/metric reads plus Loki "Logs
  Drilldown" deep-links for a customer's namespace/service). The plugin declares it
  in [`.mcp.json`](.mcp.json) as `grafana-mcp-server`, using the same
  `${IA_TOOLING_ROOT}/bin/local-tooling` pattern as `github-mcp-server`,
  `atlassian-mcp-server` and `kapa`. It is opt-in on the `ia-tooling` side
  (`GRAFANA_ENABLED=true` + `GRAFANA_BASE_URL`/`GRAFANA_TOKEN`); when disabled or
  unconfigured it simply fails to start, like any other server, without affecting the
  rest. `/investigate` gains a **Grafana** row in its source table (a live metric via
  `grafana_query`, or a Loki Logs Drilldown link via `grafana_logs_link`), and
  `/reproduce` can pull a live metric/log link when recording a result. README,
  getting-started and PORTING updated to match. Prompt/config only; no script change.

## [0.0.9] - 2026-08-31

### Added
- **Context-economy convention, codified in the plugin.** New shared reference
  [`references/context-economy.md`](references/context-economy.md): delegate the
  heavy, mechanical, high-payload work — fetching + parsing a large payload (a full
  Zendesk thread, a Jira batch) or fanning out across sources (`rag_search`,
  `zendesk_search_tickets`, `searchJiraIssuesUsingJql`, `gh search`) — to a
  subagent that returns only a distilled digest, and never dump a big tool result
  or file into the main context (parse it down with `grep`/`jq`/`Read` offsets
  first). Reasoning and user-facing work stay **inline** — the diagnostic thinking
  in `/investigate`, and drafting a reply *with* the user in `/reply`, are not
  delegated. The six payload-heavy commands now point at it at their heavy step:
  `/log-updates` (Zendesk fetch), `/investigate` and `/reproduce` (precedent
  fan-out), `/kb` (anti-duplicate fan-out), `/status` and `/reply` (reading a large
  `timeline.md`). Prompt-only; no script or behaviour-contract change.

## [0.0.8] - 2026-08-31

### Fixed
- **`/close` can now backfill a half-closed ticket instead of refusing it.** When a
  ticket's `status` was moved to a terminal value outside `/close` — e.g.
  `/log-updates` syncing status from Zendesk — `resolved_at` and
  `resolution_time_hours` were never stamped (only `close_meta.py` writes them), yet
  the step-2 guard treated the ticket as already closed and stopped. Such tickets
  were stuck with `resolved_at: null` and no clean way to fix it. `close_meta.py`
  gains **`--stamp-only`**: it backfills `resolved_at` + `resolution_time_hours` on
  an already-terminal ticket without touching `status`/`updated_at` and without
  adding a timeline entry — idempotent (no-op if `resolved_at` is already set) and
  refuses a non-terminal ticket. `close.md` step 2 now branches: terminal +
  stamped → stop; terminal + missing `resolved_at` → backfill via `--stamp-only`;
  not terminal → normal close.
- **`/reproduce` evidence filenames match the documented convention.** The
  `reproduction-steps.md` template hardcoded `results/before_fix.png` /
  `after_fix.png`, diverging from step 5's `results/NNN_<short>.<ext>` rule (NNN =
  the linked timeline entry). Template now uses `results/NNN_before.png` /
  `NNN_after.png` and carries a comment stating the convention.
- **`/reproduce` docs corrected.** `reproduce.md` said `steps.md`/`environment.md`
  render `engineer` and `date` from `metadata.json`; they don't — `engineer` comes
  from `$TICKETS_ENGINEER` (else the OS login) and `date` is today. Wording fixed.

### Changed
- **Reproduction templates are no longer stack/docker-only.** `reproduction-steps.md`
  and `reproduction-environment.md` now cover both a stack-based repro and a
  **browser/UI repro with no stack** (URL, browser + version, viewport/resolution),
  so a pure front-end/CSS reproduction isn't forced through dead docker boilerplate.
  `docker-compose` → `docker compose`.
- **`/reply` prompt guidance sharpened.** Step 3 now tells the drafter to check the
  previous outbound entry and not repeat a request the customer hasn't answered yet;
  step 9 clarifies the status choice — asked the customer for info → `waiting`; an
  action still pending on our side → `pending`; confirmed resolution → `resolved`.

## [0.0.7] - 2026-08-31

### Added
- **`/version` reports the plugin version running in the current session.** Reads
  the version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` — the cache
  Claude Code actually loaded for this session, not the source repo — and compares
  it against the marketplace catalog (`highest installed` in the cache is shown
  too). The verdict says whether you're on the latest and, when behind, prints the
  exact update path (`/plugin marketplace update` → `/reload-plugins`); when ahead
  of the catalog it flags the marketplace as stale. Read-only, no arguments. New
  `commands/version.md` + `scripts/version.py`.

## [0.0.6] - 2026-08-31

### Fixed
- **`/log-updates` no longer skips comments with out-of-order ids.** The baseline
  cursor was `last_comment_id` and selection assumed comment ids increase with
  time — but Zendesk can mint a later comment (e.g. an auto-generated identity
  card) with a *lower* id than an earlier one, so a strict id cursor would silently
  skip it. Selection is now driven by the comment's `created_at` timestamp: a new
  nullable `last_comment_at` field is the cursor, comments are selected/ordered by
  time (not id), and a de-dup guard skips any comment id already footed in the
  timeline. `last_comment_id` is kept as a human pointer. Older tickets migrate
  transparently — the first run translates their `last_comment_id` to a timestamp
  from the fetched thread.

### Changed
- `templates/metadata.json` gains `last_comment_at` (nullable); `set_meta.py` knows
  it as a nullable string; `/new-ticket` seeds it from the opening comment's
  `created_at`.

## [0.0.5] - 2026-08-28

### Removed
- **The global current-ticket pointer is gone.** Now that each window resolves its
  ticket from the shell's cwd (0.0.4), the `$TICKETS_ROOT/.current-ticket` file and
  its `current_ticket.py` helper served no purpose — deleted, along with every
  reference to them. The resolution chain across all commands is now simply
  **arguments → cwd → ask** (or **cwd → ask** for `/investigate`, whose argument is
  the question). Switching a window to a ticket is a plain `cd` into its folder.

### Changed
- Write-guards simplified: the old "cwd ≠ pointer" check is dropped; commands that
  take an explicit ticket number still confirm when it differs from the cwd
  ("explicit ≠ cwd").

## [0.0.4] - 2026-08-28

### Changed
- **Current-ticket resolution is now per-window via cwd.** The window a command
  acts on is the ticket whose folder the shell sits in, so working two tickets in
  two windows no longer collides. Saying "let's work on `<number>`" (and
  `/new-ticket`) now `cd`s the window into that ticket's folder instead of writing
  the shared global pointer. The `$TICKETS_ROOT/.current-ticket` file remains only
  as a single-window fallback for when the shell isn't in a ticket folder.
  Requires the session's working directory to contain `$TICKETS_ROOT` (launch
  there or `/add-dir`). Resolution chain reordered: arguments → cwd → pointer →
  ask; the old "cwd ≠ pointer → ask" friction is gone.

## [0.0.3] - 2026-08-28

### Changed
- `/new-ticket`: the automatic thread fold-in now runs its `/log-updates` subagent
  in the **background** instead of blocking the session. A long thread (many
  comments, big logs, attachments) no longer floods the window or stalls the open —
  its report arrives via notification while you keep working. (#27)

## [0.0.2] - 2026-08-28

### Added
- `/new-ticket`: when a freshly opened ticket has more than the opening comment, it
  now **automatically** folds the rest of the thread into the timeline via a
  `/log-updates` subagent — no need to run `/log-updates` by hand afterwards. The
  baseline cursor (`last_comment_id`) is already set, so only comments after `[001]`
  are pulled: no overlap, no gap. (#26)

## [0.0.1] - 2026-08-27

Initial development release — the hand-built `~/TICKETS` workflow, ported into a
versioned Claude Code plugin. Covers development from 2026-08-17 to 2026-08-27
(PRs #1–#25); summarized by area rather than per-PR.

### Added
- **Core ticket lifecycle** — commands driving a per-ticket chronological timeline
  (`timeline.md` + `metadata.json`): `/new-ticket`, `/status`, `/log-updates`,
  `/reply`, `/close`, `/investigate`, `/reproduce`. `/new-ticket` also resumes an
  existing folder instead of overwriting, and searches prior art by literals.
  (#2, #4, #9, #11, #12, #13, #15)
- **Deterministic metadata & headers** — `set_meta.py` (atomic, typed writes) and
  `render_header.py` (header rebuilt from metadata, body untouched), plus a shared
  "current ticket" notion and unified ticket resolution so commands don't re-ask the
  number. `/reply` and the write path keep ticket status in sync. (#6, #7, #8)
- **Local environment** — `/tickets-up` starts and verifies the ia-tooling stack;
  `/stack` drives the `gravitee-stacker` MCP server to bring up APIM / AM / Gamma
  stacks (version-selectable singletons, canonical ports, an Access-URLs table on
  bring-up, and OSS-vs-EE license resolution). (#3, #14, #16, #18, #19, #20, #21)
- **Knowledge base** — a GitHub-repo-backed KB lifecycle: `/kb-candidate` (open a
  candidate Issue), `/kb` (draft an article as an open PR), `/kb-publish` (merge the
  draft, resolve its canonical URL, index it). (#23, #24, #25)
- **Prior-art search & MCP wiring** — precedent search via the `vectordb` MCP, and
  portable wiring for the Zendesk, GitHub, Atlassian, vectordb and gravitee-stacker
  MCP servers. (#1)
- **Documentation** — a getting-started guide (install → configure → use) and a
  single visible place documenting the plugin's configuration env vars. (#1, #5, #17)
