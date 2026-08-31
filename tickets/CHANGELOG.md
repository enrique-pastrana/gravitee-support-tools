# Changelog

All notable changes to the **tickets** plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Rule of thumb:** every bump of `version` in
> [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) gets a matching entry
> here, in the same PR — so the changelog never drifts from what shipped.

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
