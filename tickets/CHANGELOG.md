# Changelog

All notable changes to the **tickets** plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Rule of thumb:** every bump of `version` in
> [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) gets a matching entry
> here, in the same PR — so the changelog never drifts from what shipped.

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
