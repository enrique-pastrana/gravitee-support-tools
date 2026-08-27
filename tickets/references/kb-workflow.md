# Reference: the KB article workflow

How the KB slice works and why. The commands (`/kb-candidate`, `/kb`,
`/kb-publish`) decide *when* to act; this is the *how* and the *why*, plus the
**one-time repo setup** each user does once. Paths assume `${CLAUDE_PLUGIN_ROOT}`
(plugin) and `$TICKETS_ROOT` (data).

## The model: the KB lives in a GitHub repo

KB articles are **not** kept in local disk folders. They live in a dedicated
GitHub repo — one article per Markdown file under `articles/` — and the article's
lifecycle **is** the repo's own git primitives. Nothing to reinvent, everything
auditable, and the "queue" is just GitHub's issue/PR lists.

| Lifecycle stage | Git-native representation | Set by |
|---|---|---|
| **Candidate** — worth writing, not written yet | an **Issue** labeled `kb:candidate` | `/kb-candidate` |
| **Draft / in review** | an **open PR** (label `kb:draft`) adding `articles/<slug>.md`, closing the Issue | `/kb` |
| **Published** | that **PR merged** to `main` | `/kb-publish` |

The board view (Candidate → In review → Published) is a **GitHub Project** with
native automations — see setup below. No workflow files, no Actions, nothing the
plugin has to install into your repo.

### Why a repo, not disk folders + index files

The old `~/TICKETS` KB kept state in `_kb/candidates.md` + `_kb/tickets-index.md`
(hand-maintained Markdown queues) and shared drafts to a Google Doc. The repo
model replaces all of it: the Issue list *is* `candidates.md`, an open PR *is* a
draft under review, a merge *is* "published". Simpler, more reliable, and shared
by construction — no parallel index to drift.

## No local clone — the Contents API

`/kb` and `/kb-publish` never `git clone`. They read and write repo files through
`gh api` (the GitHub Contents API) and manage Issues/PRs through `gh`. So the KB
repo can be anywhere and the user needs no working copy of it on disk.

## Credentials: writes via `gh`, reads via MCP

Two paths, deliberately split:

- **Writes** (create Issue, open PR, merge) → the user's **own `gh` CLI**, already
  authenticated for their GitHub account. It needs the **`repo`** scope.
- **Reads / dedup** → the **`github-mcp-server`** MCP (wired via `ia-tooling`).
  That token is **read-only by design** (ia-tooling provisions it with minimum
  read scope), so it can search the repo but must never be used to write. Do not
  try to open Issues/PRs through the MCP — it will fail, and that's intentional.

`scripts/kb-preflight` checks the **write** path (gh installed + authed, `$KB_REPO`
set + reachable, labels present) before any command tries to create something.

## Configuration: one variable

| Variable | Required? | Default | What it controls |
|---|---|---|---|
| `KB_REPO` | Yes (for the KB commands) | — | The KB repo as `owner/name`, e.g. `your-org/kb-articles`. The single config for the whole slice, in the same spirit as `IA_TOOLING_ROOT` / `TICKETS_ROOT`. |

Set it once in `~/.zshrc` / `~/.bashrc`:
```bash
export KB_REPO="your-org/kb-articles"
```

## The four KB types

Every article is one of four types (Zendesk's classification); `/kb` picks a
matching template:

| Type | When it fits |
|---|---|
| **Problem / Solution** | A failure with a **known single root cause** and a concrete fix. |
| **How-to** | A proactive task ("how to do X"); no failure involved. |
| **Troubleshooting** | A failure **without one cause** — a diagnostic tree. |
| **Question / Answer** | A conceptual doubt / "is this normal?" — an explanation, not a fix. |

## Public vs. internal content

The KB repo is **private / employee-gated**: only Gravitee staff can see it, so
**internal references are safe inside it** — candidate Issues and draft articles
may carry the ticket id, customer, Jira keys, engineering notes, repro details.

Each article still separates a **public body** from an internal block with an
`<!-- INTERNAL — DO NOT PUBLISH -->` separator (everything internal goes *below*
it). That separator is what a **future** customer-facing publish step will cut on
— a plugin-side script that emits only the public body to a public mirror
(e.g. Zendesk Guide). That step is **out of scope for now** and deliberately
**not** an Actions/workflow in the repo, so installing the plugin never requires
the user to add CI to their KB repo. Until then: repo private, internal inline.

## Dedup — don't write the same article twice

Before generating (in `/kb`), check for an existing article covering the same
symptom/component, two ways:

- **Repo search** — the `github-mcp-server` MCP (or `gh search code --repo
  $KB_REPO`) over `articles/`, plus the open `kb:candidate` / `kb:draft` Issues
  and PRs, for the component, error string, or symptom keywords.
- **Semantic** — `rag_search` (vectordb) for a meaning-level match, since the
  same problem is often worded differently.

If something already covers it, stop and offer to **extend** it (link this ticket
to that article/Issue) rather than create a duplicate.

## One-time repo setup (per user)

Each user points `$KB_REPO` at **their own** KB repo — it holds their KB content,
so the plugin can't ship it, the same way it ships no ticket data (that's
`TICKETS_ROOT`) and no ia-tooling checkout (`IA_TOOLING_ROOT`). Do the steps below
once. `/kb-preflight` verifies the mandatory parts (1–3); the Project board (4) is
an **optional** UI step it can't check.

### Mandatory — the repo, labels, and `articles/`

Steps 1–3 are all the commands actually need. They're mechanical and idempotent —
`gh` does them in a few seconds.

1. **Create it private.** One article per file will live under `articles/`.
   (Private = employee-gated, so internal references are safe inside it.)
2. **Labels** (a candidate Issue needs `kb:candidate`; a draft PR uses `kb:draft`):
   ```bash
   gh label create "kb:candidate" --repo "$KB_REPO" --color FBCA04 \
     --description "Ticket flagged as a KB article candidate"
   gh label create "kb:draft" --repo "$KB_REPO" --color 1D76DB \
     --description "KB article draft in review (open PR)"
   ```
3. **`articles/` folder** — seed it so it exists before the first PR:
   ```bash
   printf '# KB articles live here, one Markdown file per article.\n' \
     | base64 | xargs -I{} gh api -X PUT "repos/$KB_REPO/contents/articles/.gitkeep" \
       -f message="chore: seed articles/ folder" -f content={}
   ```

### Optional — the Project board (a kanban view)

**The KB commands work fully without this.** The lifecycle state lives in the
Issues/PRs and their labels, not in a board — so the board is purely a nice
kanban *view* (Candidate → In review → Published). Skip it if you don't want it;
set it up if you like seeing the pipeline at a glance.

It's a GitHub **Project v2** with two native **built-in workflows** (no Actions
file, nothing installed into your repo). All in the web UI — one time, ~5 min:

1. **Create the Project.** github.com/users/`<you>`/projects → **New project** →
   Table template → name it **`KB pipeline`**.
2. **Status field** — the default `Status` field ships with `Todo / In Progress /
   Done`; rename its options to exactly: **`Candidate`**, **`In review`**,
   **`Published`** (⋯ → Settings → Custom fields → Status).
3. **Auto-add the repo.** ⋯ → **Workflows** → **Auto-add to project** → pick
   `$KB_REPO`, set the filter to **`is:open`** (so both Issues *and* draft PRs are
   pulled in — `is:issue is:open` would miss the PRs), **Save and turn on**.
4. **Two status automations** (same Workflows list, both native):
   - **Item added to project** → *Set* `Status` = **`Candidate`** → turn on.
   - **Item closed** → *Set* `Status` = **`Published`** → turn on.
     (A merged PR is a closed item, so this covers publish too.)

Reading/managing the board via `gh` (e.g. `gh project item-list`) needs the
`project` scope: `gh auth refresh -s project` (or `read:project` for read-only).
The web UI needs no extra scope. **`In review`** has no automation — a draft PR
lands as `Candidate` like any item. `/kb` makes a **best-effort** move to
`In review` when it opens the PR *only if* the token has the `project` scope;
without it (or without a board) it skips silently, since the board is optional and
the open `kb:draft` PR is the real source of truth. Move it yourself in the UI if
you prefer (one drag).

> **Automating it?** Steps 1–3 (repo/labels/`articles/`) are trivial to script and
> a `/kb-setup` command may fold them in. The board's built-in workflows (step 4)
> are UI-configured and not worth scripting for an optional view — so it stays a
> documented manual step.
