# Porting `~/TICKETS` → `tickets` plugin

The journal of turning the standalone `~/TICKETS` workspace into a portable
Claude Code plugin in the `gravitee-support-tools` marketplace. This is a
development document — the user-facing doc is [README.md](README.md).

## Why

`~/TICKETS` is a full Claude-Code-driven system for handling Zendesk tickets: a
folder per ticket with a chronological `timeline.md`, driven by slash commands.
It only works from that one checkout, with hardcoded paths. Porting it to a
plugin makes it installable, portable and shareable through the marketplace.

## Source

- Workspace: `/Users/enrique.pastrana/TICKETS`
- Its own git repo (`tickets-tool`), separate from this marketplace.
- The `updateP1` command from this workspace already shipped separately as the
  `p1-updates` plugin — this plugin ports the rest.

## Component mapping

What lives in `~/TICKETS` and where it lands in the plugin:

| Source (`~/TICKETS`)            | Plugin destination        | Notes |
|---------------------------------|---------------------------|-------|
| `.claude/commands/*.md` (19)    | `commands/`               | Straight port; drop `updateP1` (already in `p1-updates`). |
| `.claude/agents/queue-health.md`| `agents/`                 | Straight port. |
| `_system/scripts/*.py`          | `scripts/`                | Reference via `${CLAUDE_PLUGIN_ROOT}`; fix `~/TICKETS` path assumptions. |
| `_system/templates/*`           | `templates/`              | Straight port. |
| `CLAUDE.md` (behavioural contract) | `skills/` (likely)     | Cannot ship as a root `CLAUDE.md`; see open question 3. |
| ticket data (`13000-15000/`, `16000/`, …) | **not ported**   | User data, not machinery — stays in the user's workspace. |
| `.mcp.json`                     | `.mcp.json` (TBD)         | Hardcoded absolute paths today; see open question 2. |

## Open questions (decide before/while porting)

### 1. Where does the ticket data live?
Today the scripts default to `~/TICKETS` (overridable with `TICKETS_ROOT`) and
the permission allowlist assumes that path. As a plugin, the machinery ships but
the ticket folders belong to the user. Need a portable way for the plugin to
locate the tickets root — env var, a config file, or the current working
directory. **Undecided.**

### 2. The `ia-tooling` MCP wiring — DECIDED (2026-08-17)
`~/TICKETS/.mcp.json` hardcoded `/Users/enrique.pastrana/ia-tooling/...` for the
`zendesk`, `vectordb`, `github`, `atlassian`, `kapa` servers. Not portable.

**Decision:** declare the servers in the plugin's own `.mcp.json`, replacing the
hardcoded prefix with a single per-user environment variable
**`${IA_TOOLING_ROOT}`** (Claude Code expands it at load time). The user sets it
once in their shell (`export IA_TOOLING_ROOT="$HOME/ia-tooling"`). No absolute
path lives in the repo. Scoped down for now:

- **6 servers** ported: `zendesk`, `vectordb`, `github-mcp-server`,
  `atlassian-mcp-server`, `kapa`, `grafana-mcp-server`. Only `zendesk` (env-file)
  and the four `local-tooling` commands carried a path; `vectordb` had none.
- **`fathom` dropped** here — already shipped in `p1-updates`.
- **`grafana-mcp-server` added** (read-only) once `ia-tooling` exposed it via
  `local-tooling mcp grafana` — see the 2026-09-01 progress-log entry.

**Verified** in the clean `sandbox/` via `claude --plugin-dir ../gravitee-support-tools/tickets`:
`/mcp` showed all servers prefixed `plugin:tickets:` (proving the plugin, not
`~/TICKETS`, provides them). 4 of 5 connected with tools (zendesk 11, vectordb 4,
github 23, atlassian 31). `kapa` failed on a pre-existing, unrelated `ia-tooling`
issue (the user's global `kapa` MCP fails identically) — parked.

### 3. The behavioural contract (`CLAUDE.md`)
The 15KB `CLAUDE.md` is the rulebook Claude follows in the workspace (response
style, ticket conventions, MCP usage, pre-authorised actions). A plugin cannot
inject a root `CLAUDE.md` into the user's directory. Candidate: turn it into a
plugin **skill** (or split it across command prompts). **Undecided.**

## Backlog / ideas (user, 2026-08-17)

Captured at the close of the PR #4 session — to shape upcoming slices, not yet
scheduled:

- **KB articles area.** Port the KB workflow (`kb`, `kb-candidate`, `kb-shared`)
  — a proper "KB articles" section built from resolved tickets.
- **`investigate`** — port the investigation command.
- **`reproduce`** — port the reproduction command. **Design work needed first:**
  think through *how* we tackle reproduction (what a repro run actually does,
  what it needs, how it records results) before porting — not a blind copy.
- **Environment variables audit.** Review carefully **all** the env vars the
  plugin needs to work end-to-end (`IA_TOOLING_ROOT`, `TICKETS_ROOT`,
  `IA_TOOLING_ENV`, Zendesk auth in the ia-tooling `.env`, …) — confirm the full
  set, defaults, and failure modes.
- **Clear onboarding docs.** Explain all of the above (setup, env vars, the repro
  approach) **simply and clearly for a brand-new user** — extend
  `docs/getting-started.md` so someone using it for the first time can get
  running without prior context.
- **Copy/paste-out commands (NEW, not in the source set).** Commands that emit
  ready-to-paste text for external trackers: a **Jira bug** report, a **feature
  request**, etc. The user will provide the **templates** for each; the command's
  job is to fill a template from the ticket timeline and hand back the text to
  paste. Likely new `templates/` + a small command per output type.
- **P1 section (NEW).** Even though `p1-updates` already ships separately, the
  user expects to need a **P1-specific section** inside (or alongside) this
  plugin. Scope TBD — clarify what it should cover vs. what `p1-updates` already
  does, to avoid overlap.

## Progress log

- **2026-08-17** — Created branch `add-tickets-plugin`. Scaffolded the empty
  plugin: `plugin.json`, README stub, this journal, and empty
  `commands/ agents/ skills/ scripts/ templates/` dirs. Added the plugin to the
  marketplace catalogue. No logic ported yet.
- **2026-08-17** — Resolved open question 2 (MCP wiring). Wrote a portable
  `.mcp.json` using `${IA_TOOLING_ROOT}` for 5 ia-tooling servers (fathom
  dropped, grafana parked). Validated JSON + `plugin validate --strict`, then
  tested from the clean `sandbox/` with `--plugin-dir`: 4/5 servers connected
  (kapa parked). Documented the `IA_TOOLING_ROOT` requirement in the README.
  Commands, agent, scripts, templates and the `CLAUDE.md` contract still to port.
- **2026-08-17** — Branch `add-tickets-core-commands`. Ported the first command
  slice: `new-ticket` + `status`. Scope grew from the two "base" scripts to the
  **five** the commands actually need — `new-ticket` pulls in `bump_entry`
  (entry counter), `fetch_attachments` (Zendesk auto-download) and `attach`
  (manual fallback), on top of `ticket_paths` + `init_ticket`; kept the slice
  whole so the merged command is fully usable rather than referencing scripts
  that don't exist yet. Cleanup on the way in: command paths rewritten from
  `~/TICKETS/_system/scripts/*` to `${CLAUDE_PLUGIN_ROOT}/scripts/*`, templates
  to `${CLAUDE_PLUGIN_ROOT}/templates/*`, `~/ia-tooling` → `${IA_TOOLING_ROOT}`;
  dropped `new-ticket`'s redundant manual `ls` existence check (init_ticket
  already refuses to overwrite); made `fetch_attachments` default its `.env` to
  `$IA_TOOLING_ROOT/.env` to match the `.mcp.json` convention; `_kb` index read
  now guarded as optional (user data, may not exist). Templates ported:
  `timeline.md`, `metadata.json`, `entry-snippets.md`. Verified end-to-end
  against a temp `TICKETS_ROOT`: bucket creation, template render, entry bump,
  overwrite refusal, filename normalisation, and the `status` path resolver all
  work through `${CLAUDE_PLUGIN_ROOT}`; `plugin validate --strict` passes.
- **2026-08-17** — Branch `add-tickets-up-command`. Ported the `tickets-up`
  command + `scripts/tickets-up` (start/verify the ia-tooling stack: Docker,
  Ollama, vectordb health, restart policy). Renamed the env var `IA_TOOLING` →
  `IA_TOOLING_ROOT` to match `.mcp.json`; translated the remaining Spanish to
  English; the command doc explains what it does and the two-layer fallback
  story. Verified by running the script (exit 0, healthy) and via
  `/tickets:tickets-up` in the sandbox. `plugin validate --strict` passes.
- **2026-08-17** — Branch `add-customer-reply-commands`. Ported the next
  command slice: `reply` (draft-and-iterate outbound reply) plus a **redesigned**
  version of the source's `customer` command. Design discussed with the user;
  four decisions shaped it:
  - **Renamed `customer` → `log-updates`** and broadened its scope. The source
    `customer` was paste-driven and customer-only; a Zendesk entry can just as
    well be an internal note, a reply we sent, or a linked Jira. `log-updates`
    is source-agnostic and **Zendesk-driven**: it calls the `zendesk` MCP
    (`zendesk_get_ticket_with_attachments`), selects comments newer than
    `metadata.json`'s `last_comment_id`, and logs each — falling back to the
    paste flow when the stack is down. Added `last_comment_id` to the metadata
    template; `new-ticket` seeds it with the opening comment's id.
  - **Summarise, don't store the literal.** Entries now carry a short summary +
    a `Key details (verbatim)` block only for load-bearing specifics (errors,
    versions, config, ids) + a `🔗 Zendesk comment #<id>` footer as the pointer
    to the exact words. Keeps the timeline cheap for `/reply` and `/status` to
    read. Reworked the `entry-snippets.md` snippet (`Inbound customer message`
    → `Incoming update`) accordingly and extended the emoji table (🔒 internal
    note, 🔗 linked source, 🔔 one-liner).
  - **Extracted shared logic to `references/`**, read explicitly by the commands
    (deterministic, unlike ambient skill-loading): `attachments.md` (download
    with `fetch_attachments.py` → view with `Read`; the MCP only explores, never
    routes binaries through context) and `classify-entry.md` (substantive vs.
    non-substantive). `log-updates`, `reply` and `new-ticket` now point here
    instead of repeating the blocks.
  - **Bump-first everywhere.** Replaced the peek+commit split with a single
    `bump_entry` call that returns the consumed `NNN` — fixes a real hole in
    `reply` (it referenced `[NNN]` with no source) and trades the duplicate-id
    risk for a harmless gap. Also added a tiny `__main__` CLI to
    `ticket_paths.py` so all three commands resolve the folder with one short
    call instead of the inline `python3 -c …` that `status` carried.
  Verified mechanically against an isolated `TICKETS_ROOT`: the path resolver,
  `last_comment_id` propagation from the template, and the bump-first cycle
  (001→002, `next_entry`→3) all work through `${CLAUDE_PLUGIN_ROOT}`. `plugin
  validate --strict` passes. The interactive Zendesk-pull / draft flow still
  needs a live-session test.
- **2026-08-17** — Live-tested the whole slice end-to-end against real Zendesk
  ticket 17337 in an isolated `TICKETS_ROOT` (`~/tickets-test-0817`; the real
  `~/TICKETS/17000/17337` left untouched). `/new-ticket` (11 attachments,
  `opened_at` from Zendesk, `[001]` in summary+verbatim+`comment_id` format),
  `/log-updates` (seeded the cursor to comment #68 to bound the pull to the last
  5 comments — validated classification, per-source emoji 📥/📤/🔒/🔔,
  summary-vs-verbatim, `comment_id` footers, and cursor advance), `/reply`
  (draft→iterate→confirm→save: wrote `[007]` only on confirmation, bump-first,
  refreshed the exec summary) and `/status` (7 entries, `[008]` next, 11
  attachments excluding the ledger, read-only) all worked. Two findings the live
  run surfaced, both fixed in this PR:
  - **A — `new-ticket` over-downloaded attachments when adopting an old ticket.**
    It scanned the whole thread and tagged every attachment `001_` + logged the
    tokens in the idempotency ledger, so a later `/log-updates --comment-id`
    would skip them and those entries would lose their attachment links. Fixed:
    `new-ticket` now fetches **only the opening comment's** attachments
    (`--comment-id <opening_id>`), matching `[001]`'s scope; later comments'
    attachments are pulled under their own entry by `/log-updates`. No change for
    a fresh ticket (thread = opening comment).
  - **B — `log-updates` trusted a cursor that ran ahead of the timeline.** If
    `last_comment_id` points past the newest comment actually logged, the gap was
    skipped silently (exactly what the manual test seed created). Fixed: step 1
    now cross-checks the cursor against the timeline's `🔗 Zendesk comment #<id>`
    footers and, on a gap, asks the user to backfill from the last logged id or
    trust the cursor. `plugin validate --strict` passes.
- **2026-08-18** — Branch `document-env-configuration`. Documented the plugin's
  configuration in one visible place — addresses backlog items **env-vars audit**
  and **onboarding docs**. Added a `## Configuration` section to the README with
  the full env-var table (`IA_TOOLING_ROOT`, `TICKETS_ROOT`, `IA_TOOLING_ENV`,
  `CLAUDE_PLUGIN_ROOT`) — required?/default/what it controls/failure mode — plus
  a sub-table for the Zendesk keys that live inside the `ia-tooling` `.env`
  (`ZENDESK_AUTH_MODE`/`_EMAIL`/`_API_TOKEN`/`_OAUTH_ACCESS_TOKEN`/`_BASE_URL`).
  Design decision confirmed with the user: **no plugin-owned config file** and
  **not folded into the ia-tooling `.env`** — `IA_TOOLING_ROOT` is chicken-and-egg
  (needed to *find* ia-tooling), that `.env` is a secrets file (path config
  doesn't belong there), and the scripts read the shell env (`os.environ`), not
  that file, so it wouldn't be picked up anyway. Shell env vars stay the
  mechanism; `getting-started.md` now covers `IA_TOOLING_ENV` and links to the
  README table as the authoritative reference.
- **2026-08-27** — Branch `kb-articles-slice-1-candidate`. Started the **KB
  articles slice** (PR 1 of 3: foundation + `/kb-candidate`). Big design change
  from the source, agreed with the user: **the KB lives in a GitHub repo**, not
  local disk folders + hand-maintained index files (`_kb/candidates.md`,
  `_kb/tickets-index.md`). The article lifecycle *is* the repo's git primitives —
  **candidate = Issue** (`kb:candidate`), **draft/review = open PR** (`kb:draft`),
  **published = PR merged**; the board is a native GitHub **Project** (auto-add +
  closed→Published), configured once in the UI (no Actions/workflow files, so
  installing the plugin never forces CI into the user's repo). One config var,
  **`KB_REPO=owner/name`**. Credentials split deliberately: **writes** (Issue/PR/
  merge) via the user's own **`gh`** CLI (`repo` scope); **reads/dedup** via the
  read-only `github-mcp-server` MCP + semantic `rag_search`. No local clone —
  `/kb` and `/kb-publish` (later PRs) will use the `gh api` Contents API. Repo is
  **private / employee-gated**, so internal refs are safe inline; a *future*
  plugin-side sanitized-publish step (cutting at `<!-- INTERNAL — DO NOT PUBLISH
  -->`) will feed a public mirror — out of scope here, and not an Actions
  dependency by design. Shipped in this PR:
  - **schema** — added KB fields to `templates/metadata.json` and `set_meta.py`
    (`kb_status`, `kb_type`, `kb_url`, `kb_published_at` as nullable strings;
    `kb_issue`, `kb_pr` as nullable ints). Kept the legacy `kb_candidate` bool and
    have `/kb-candidate` set it alongside `kb_status` so `/close --kb-candidate`
    and older reads stay in sync; `kb_status` is the new source of truth.
  - **`scripts/kb-preflight`** — mirrors `stack-preflight`: checks `gh` installed
    + authed, `$KB_REPO` set + reachable, and the `kb:candidate`/`kb:draft`
    labels; checks the **write** path only (the MCP read path is separate).
  - **`commands/kb-candidate.md`** — reworked for the new model: resolves the
    ticket (shared `resolve-ticket.md` chain), preflights, dedup-guards on an
    existing `kb_issue`, creates the Issue via `gh` **on confirmation** (outward
    write), records `kb_status=candidate`/`kb_candidate=true`/`kb_issue` via
    `set_meta.py` + `bump_entry.py --touch`, and links the Issue in the timeline's
    `## 📚 KB article draft` section. No `[NNN]` entry, no `_kb/` files.
  - **`references/kb-workflow.md`** — the deep doc: the lifecycle↔git mapping, the
    4 types, the credential split, dedup, the public/internal policy, and the
    **one-time repo setup** spec (labels, `articles/`, Project board + its 2
    native automations).
  - **README** — `KB_REPO` config row + a "Knowledge base" subsection + the
    `/kb-candidate` command entry.
  User's KB repo (`enrique-pastrana/kb-articles`) provisioned to spec: private,
  labels + `articles/` created via `gh`; the Project board is the user's UI step
  (gh token lacks `project` scope). `kb-preflight` passes live against it. Next:
  PR 2 (`/kb` — generate draft, open PR via Contents API, port the 4 templates) and
  PR 3 (`/kb-publish` — merge, index into vectordb, record the URL).
  PR 1 merged to `main` 2026-08-27 (squash `469545a`); a follow-up commit added
  the KB onboarding docs (setup split Mandatory vs Optional-board, `KB_REPO` in
  getting-started, board LIVE-verified e2e). `/kb-candidate` live-tested e2e too
  (real Issue created, dedup guard held).
- **2026-08-27** — Branch `kb-articles-slice-2-kb`. **KB slice PR 2: `/kb`** —
  turn a candidate into a **draft article** as an open PR. `commands/kb.md`:
  preflight → resolve ticket (`$ARGUMENTS` = number) → require a `kb_issue`
  candidate → anti-duplicate (repo code search + open `kb:draft` PRs + `rag_search`)
  → decide KB-worthy + classify into one of the 4 types (confirm with user) →
  **generate the article from the template, show it in chat, iterate** → **on
  confirmation open the PR with zero clone, all `gh api`**: branch `kb/<ticket>-<slug>`
  off the default branch, PUT `articles/<slug>.md` (base64) on it, `POST …/pulls`
  with body `Closes #<kb_issue>`, label it `kb:draft` → **best-effort** board move
  to *In review* (skipped silently without the `project` scope — board is optional)
  → `set_meta.py kb_status=draft/kb_pr=<n>/kb_type` + `bump_entry.py --touch` →
  link the PR in the timeline's `## 📚 KB article draft` section. No `[NNN]` entry.
  Ported the **4 KB templates** to `templates/` (`kb_article.md` — our richer
  Problem/Solution format with a Validation section; `kb_howto.md`,
  `kb_troubleshooting.md`, `kb_question_answer.md` — the Zendesk-classification
  templates), each keeping the `<!-- INTERNAL — DO NOT PUBLISH -->` separator with
  the internal block below it (source ticket, KB Issue URL, related/Jira/repro).
  Board fork settled with the user: **best-effort if scope**. Updated
  `references/kb-workflow.md` (In-review note → best-effort), README (`/kb` command
  entry + lifecycle bullet), getting-started (command row + WIP banner).
  **Live-tested e2e (Claude headless, sandbox ticket 99999 with a realistic
  timeline + a real candidate Issue via `/kb-candidate`):** `/kb` opened PR #4
  (`kb:draft`, `Closes #3`), wrote `articles/apim-gateway-oom-response-template-policy.md`
  with a genuinely good Problem/Solution article — **public body clean of the
  customer name** (AcmeCorp only appears below the INTERNAL separator), specific
  root cause, YAML solution, validation, doc-only Related; metadata moved
  `candidate → draft` with `kb_pr=4`, `next_entry` unchanged, timeline updated; the
  board nudge skipped cleanly (no scope). Test PR/Issue/branch deleted, `main`'s
  `articles/` back to just `.gitkeep`, sandbox wiped. `plugin validate --strict` ✔.
- **2026-08-27** — Branch `kb-articles-slice-3-publish`. **KB slice PR 3:
  `/kb-publish`** — the final KB step, publishes the draft. `commands/kb-publish.md`:
  preflight → resolve ticket (`$ARGUMENTS` = number) → require `kb_pr` set (else
  suggest `/kb`/`/kb-candidate`) and refuse if already `published` → **inspect the
  PR** via `gh pr view --json state,mergeable,url,title,reviewDecision,files`
  (MERGED out-of-band → reconcile-only; CLOSED → rejected, stop; OPEN+CONFLICTING
  or missing review → surface, stop; OPEN+mergeable → report) → **confirm, then
  merge** `gh pr merge <kb_pr> --squash --delete-branch` (squash → one commit; the
  PR body's `Closes #<kb_issue>` closes the candidate Issue; branch deleted) →
  resolve canonical URL `https://github.com/$KB_REPO/blob/<def>/articles/<slug>.md`
  (git-native, replaces the old Google Doc URL — no user input) + **fetch the merged
  article raw** (`gh api …/contents/<file>?ref=<def> -H "Accept:
  application/vnd.github.raw"`, no base64) → **index into vectordb** with the ported
  `scripts/index_kb.py` → `set_meta.py kb_status=published/kb_url/kb_published_at`
  + `bump_entry.py --touch` (kb_issue/kb_pr kept for traceability) → append a ✅
  Published line to the timeline's `## 📚 KB article draft` section. No `[NNN]` entry.
  **Ported `scripts/index_kb.py`** — decoupled from ticket folders (the article now
  lives in the KB repo, not local disk): takes `<ticket> --file <article.md> --url
  <kb_url> [--path <rel>]` instead of reading `kb_article_draft.md`; drops the
  `ticket_paths` import; indexes the FULL article (INTERNAL block included — private
  db) with a prepended title+URL header; upsert identity = (source="tickets",
  path=`articles/<slug>.md`); exit 2 on vectordb-down is non-blocking (record, tell
  user to `/tickets:tickets-up` + re-run). Docs: README (`/kb-publish` command entry
  + lifecycle "published = PR merged" bullet), getting-started (command row + WIP
  banner now lists the full KB slice). `plugin validate --strict` ✔; `index_kb.py`
  error paths smoke-tested (missing file → 1, vectordb down → 2 graceful); step-6
  raw-fetch mechanism proven **live read-only** against `enrique-pastrana/kb-articles`
  (default branch `main`, `Accept: raw` returns file body). Destructive e2e (real
  `gh pr merge` + real ingest) deliberately deferred with the user to a real-ticket
  run once the slice is complete.

- **2026-09-01** — Branch `feat/grafana-mcp`. `ia-tooling` now exposes a
  read-only **grafana** MCP via `local-tooling mcp grafana` (commit `722831e`:
  `grafana_health`, `grafana_list_datasources`, `grafana_query`, `grafana_logs_link`
  — dashboard/metric reads + Loki "Logs Drilldown" deep-links). Declared it in
  `.mcp.json` as `grafana-mcp-server` (same `${IA_TOOLING_ROOT}/bin/local-tooling`
  pattern as github/atlassian/kapa; opt-in on the `ia-tooling` side via
  `GRAFANA_ENABLED`+`GRAFANA_BASE_URL`/`GRAFANA_TOKEN`). Wired it into `/investigate`
  (new Grafana row in the source table) and `/reproduce` (optional live metric/log
  link when recording a result); refreshed README (server list + dropped the
  "grafana parked" omission) and getting-started. 0.0.10 + CHANGELOG.
