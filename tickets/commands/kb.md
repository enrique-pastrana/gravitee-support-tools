---
description: Turn a KB candidate into a draft article — generates it from the ticket timeline and opens a draft PR in the KB repo (articles/<slug>.md, labeled kb:draft), closing the candidate Issue on merge.
argument-hint: [ticket]
---

Second step of the KB lifecycle: `/kb-candidate` opened an **Issue**; `/kb`
writes the article and opens a **draft PR** (`kb:draft`) adding
`articles/<slug>.md`, set to close that Issue on merge; `/kb-publish` merges it.
Full model + repo setup → `${CLAUDE_PLUGIN_ROOT}/references/kb-workflow.md`.

**No clone** — the PR is built entirely with `gh api`. **Writes go through `gh`**
(user's own auth); the github MCP is read-only. Repo = **`$KB_REPO`**. Opening the
PR is outward: **generate → show draft in chat → iterate → confirm, then open.**

## Steps

1. **Preflight** — `"${CLAUDE_PLUGIN_ROOT}/scripts/kb-preflight"`. On any `✗` stop
   and relay it (no PR without a working write path).

2. **Resolve the ticket** per `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`
   (chain **arguments > cwd > ask**; run the write-guards). `$ARGUMENTS`
   is the **ticket number**. State it in one line.

3. **Read `metadata.json` + `timeline.md`.** Require a candidate:
   - `kb_issue` **unset** → not flagged: stop, suggest `/kb-candidate <reason>`.
   - `kb_status=draft` + `kb_pr` set → a draft PR **already exists**: link
     `https://github.com/$KB_REPO/pull/<kb_pr>`, ask update-or-skip, **don't open
     a second PR**.

4. **Anti-duplicate** (discipline: `${CLAUDE_PLUGIN_ROOT}/references/search-precedents.md`):
   `gh search code --repo "$KB_REPO"` in `articles/` (or the read-only MCP), open
   `kb:draft` PRs (`gh pr list --label kb:draft`), and `rag_search`. If something
   covers it, **stop**, link it, offer to extend rather than duplicate.

5. **Confirm it's KB-worthy** (one sentence: yes/no + why — reproducible cause,
   non-trivial reusable fix, not a one-off config).

6. **Classify + confirm the type** with the user before generating (may override):
   | Type | Template |
   |---|---|
   | **Problem / Solution** (single root cause + fix) | `templates/kb_article.md` (richer; keeps a Validation section) |
   | **How-to** (proactive task) | `templates/kb_howto.md` |
   | **Troubleshooting** (no single cause → diagnostic tree) | `templates/kb_troubleshooting.md` |
   | **Question / Answer** (explanation, not a fix) | `templates/kb_question_answer.md` |

7. **Generate** from `${CLAUDE_PLUGIN_ROOT}/templates/<chosen>.md`, filled from the
   timeline. Keep everything internal **below** the `<!-- INTERNAL — DO NOT
   PUBLISH -->` separator (a future publish cuts there); keep the public body clean
   of customer names. Substitutions: `{{title}}` (short, **symptom-led**),
   `{{date}}` (today), `{{product}}`/`{{version}}` from metadata; the **Scope**
   block from metadata+timeline; internal block `{{ticket_id}}` + `{{kb_issue_url}}`
   (`…/issues/<kb_issue>`) + related/Jira/repro notes. Problem/Solution: fill
   Symptom (no PII) / Root cause / Solution (distilled, not the back-and-forth) /
   Validation (summarise a `reproduction/` outcome if present) / Related (**doc
   links only**). How-to/Troubleshooting/Q&A: **replace the authoring hints** with
   real content — don't leave "Add steps that are simple…" in.

8. **Show the full draft in chat and iterate** until the user is happy — **write
   nothing yet.** Derive a kebab-case **slug** from the title; if
   `articles/<slug>.md` exists, suffix `-<ticket>`.

9. **On confirmation, open the draft PR** (save the confirmed draft to a local temp
   file — e.g. the scratch dir, not the ticket folder — for the `base64` step):
   ```bash
   BR="kb/<ticket>-<slug>"
   DEF=$(gh repo view "$KB_REPO" --json defaultBranchRef --jq .defaultBranchRef.name)
   SHA=$(gh api "repos/$KB_REPO/git/ref/heads/$DEF" --jq .object.sha)
   gh api -X POST "repos/$KB_REPO/git/refs" -f ref="refs/heads/$BR" -f sha="$SHA"
   gh api -X PUT "repos/$KB_REPO/contents/articles/<slug>.md" \
     -f message="kb: draft for <ticket> — <title>" -f branch="$BR" \
     -f content="$(base64 < /path/to/draft.md | tr -d '\n')"
   PR=$(gh api -X POST "repos/$KB_REPO/pulls" \
     -f title="<title>" -f head="$BR" -f base="$DEF" \
     -f body="Closes #<kb_issue>

   Draft KB article for ticket <ticket>. Type: <type>." --jq '.number')
   gh api -X POST "repos/$KB_REPO/issues/$PR/labels" -f "labels[]=kb:draft"
   ```
   Capture the PR **number** + **URL**.

10. **Best-effort board nudge** (optional, needs `project` scope). The PR lands as
    **Candidate**; move it to **In review** with `gh project item-edit` *if* the
    board + scope exist. If `gh project` errors, **skip silently** — the open PR +
    `kb:draft` label is the source of truth, and the board is optional.

11. **Record on the ticket** (`gh` succeeded → write metadata):
    ```bash
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> \
      --set kb_status=draft --set kb_pr=<PR> --set kb_type="<type>"
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket> --touch
    ```
    `candidate → draft`; `kb_issue` stays. `--touch` = refresh `updated_at`, no
    entry consumed.

12. **Update the `## 📚 KB article draft` section** — keep the "Flagged as KB
    candidate" line, add below it:
    ```
    ✍️ **Draft opened** (YYYY-MM-DD) — [PR #<PR>](https://github.com/<KB_REPO>/pull/<PR>)
    **Title:** _<the KB title>_ · **Type:** <type>

    _In review. Merge with `/kb-publish` once approved._
    ```
    Then a brief response: confirm the draft, give the PR link, say `/kb-publish`
    is next.

## Don'ts

- **Don't open the PR without confirmation**, and **don't duplicate** — on an
  existing `kb_pr` point at that PR; on an existing article (step 4) offer to extend.
- **Don't `git clone`** — branch/write/PR all go through `gh api`.
- **Don't require the board** — the In review move is best-effort.
- **Don't leak internal data into the public body** — keep it below the separator.
- **Don't bump `next_entry`** (`--touch` only) or **write through the github MCP**
  (read-only; writes are `gh`).
