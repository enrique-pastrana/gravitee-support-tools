---
description: Turn a KB candidate into a draft article — generates it from the ticket timeline and opens a draft PR in the KB repo (articles/<slug>.md, labeled kb:draft), closing the candidate Issue on merge.
argument-hint: [ticket]
---

Turn a flagged candidate into a **draft KB article**. This is the second step of
the KB lifecycle: `/kb-candidate` opened an **Issue**; `/kb` writes the article
and opens a **draft PR** (`kb:draft`) adding `articles/<slug>.md`, set to close
that Issue on merge; `/kb-publish` later merges it. Full model + repo setup →
`${CLAUDE_PLUGIN_ROOT}/references/kb-workflow.md`.

**No local clone** — the PR is built entirely with `gh api` (Contents API).
**Writes go through `gh`** (the user's own auth); the github MCP is read-only.
Repo comes from **`$KB_REPO`** (`owner/name`). Opening the PR is an outward
action: **generate → show the draft in chat → iterate → confirm, then open it.**

## Steps

1. **Preflight.**
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/kb-preflight"
   ```
   On any `✗` stop and relay it — no PR without a working write path.

2. **Resolve the ticket.** Per `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`
   (chain **arguments > current > cwd > ask**; run the write-guards). `$ARGUMENTS`
   here is the **ticket number**. State the resolved ticket in one line.

3. **Read `metadata.json` + `timeline.md` end-to-end.** Require a candidate:
   - If `kb_issue` is **unset**, the ticket isn't flagged — stop and suggest
     `/kb-candidate <reason>` first (don't open a PR without a tracking Issue).
   - If `kb_status` is already `draft` and `kb_pr` is set, a draft PR **already
     exists** — link it (`https://github.com/$KB_REPO/pull/<kb_pr>`) and ask
     whether to update that draft (push a new commit to its branch) or skip.
     **Don't open a second PR.**

4. **Anti-duplicate.** Before generating, check nothing already covers this
   symptom/component (per `${CLAUDE_PLUGIN_ROOT}/references/search-precedents.md`
   for the search discipline):
   - existing articles — `gh search code --repo "$KB_REPO" "<component/error>"`
     scoped to `articles/`, or the read-only `github-mcp-server` MCP;
   - open `kb:draft` PRs — `gh pr list --repo "$KB_REPO" --label kb:draft`;
   - semantic — `rag_search` for a meaning-level match.
   If something already covers it, **stop**, name/link it, and offer to extend
   that article (or link this ticket to it) instead of creating a duplicate.

5. **Decide it's KB-worthy** (one sentence: yes/no + why) and confirm with the
   user. KB-worthy ≈ reproducible root cause, non-trivial fix worth keeping, not
   a one-off customer-specific config.

6. **Classify into one of the four types** and **confirm the type with the user**
   before generating (they may override). The types + templates:
   | Type | Template |
   |---|---|
   | **Problem / Solution** (known single root cause + fix) | `templates/kb_article.md` (our richer format, keeps a Validation section) |
   | **How-to** (proactive task) | `templates/kb_howto.md` |
   | **Troubleshooting** (failure, no single cause → diagnostic tree) | `templates/kb_troubleshooting.md` |
   | **Question / Answer** (conceptual, an explanation not a fix) | `templates/kb_question_answer.md` |

7. **Generate the draft** from `${CLAUDE_PLUGIN_ROOT}/templates/<chosen>.md`,
   filling it from the timeline. The repo is **private / employee-gated**, so
   internal references are safe — but still keep everything internal **below** the
   `<!-- INTERNAL — DO NOT PUBLISH -->` separator (a future publish step cuts
   there), and keep the public body above it clean of customer names.
   Substitutions (all templates):
   - `{{title}}` — short, **symptom-led** search-friendly title (not ticket-led);
   - `{{date}}` — today; `{{product}}`/`{{version}}` from `metadata.json`;
   - fill the **Scope** block (Zendesk templates) from metadata + timeline;
     leave a placeholder only if genuinely unknown;
   - internal block: `{{ticket_id}}`, `{{kb_issue_url}}` =
     `https://github.com/$KB_REPO/issues/<kb_issue>`, related tickets
     (`metadata.related_tickets`), Jira, key engineering/repro notes.
   For **Problem / Solution** also fill Symptom (paraphrased, no PII) / Root cause
   (specific) / Solution (distilled final steps, not the back-and-forth) /
   Validation (how to confirm; summarise a `reproduction/` outcome if present) /
   Related (**documentation links only** — don't invent links; tickets+Jira go
   internal). For How-to / Troubleshooting / Q&A **replace the authoring hints**
   with the real distilled content — don't leave "Add steps that are simple…" in.

8. **Show the full draft in chat and iterate** until the user is happy. **Write
   nothing to the repo yet.** Derive a kebab-case **slug** from the title
   (lowercase, non-alphanumeric → `-`, collapsed); if `articles/<slug>.md`
   already exists in the repo, suffix `-<ticket>`.

9. **On confirmation, open the draft PR — no clone, all `gh api`:**
   ```bash
   BR="kb/<ticket>-<slug>"
   DEF=$(gh repo view "$KB_REPO" --json defaultBranchRef --jq .defaultBranchRef.name)
   SHA=$(gh api "repos/$KB_REPO/git/ref/heads/$DEF" --jq .object.sha)
   # branch off the default branch
   gh api -X POST "repos/$KB_REPO/git/refs" -f ref="refs/heads/$BR" -f sha="$SHA"
   # write articles/<slug>.md on that branch (draft saved to a local temp file first)
   gh api -X PUT "repos/$KB_REPO/contents/articles/<slug>.md" \
     -f message="kb: draft for <ticket> — <title>" \
     -f branch="$BR" \
     -f content="$(base64 < /path/to/draft.md | tr -d '\n')"
   # open the PR, set to close the candidate Issue on merge
   PR=$(gh api -X POST "repos/$KB_REPO/pulls" \
     -f title="<title>" -f head="$BR" -f base="$DEF" \
     -f body="Closes #<kb_issue>

   Draft KB article for ticket <ticket>. Type: <type>." \
     --jq '.number')
   # label it kb:draft (PRs are issues for labeling)
   gh api -X POST "repos/$KB_REPO/issues/$PR/labels" -f "labels[]=kb:draft"
   ```
   Write the confirmed draft to a local temp file (e.g. under the scratch dir) for
   the `base64` step; it doesn't live in the ticket folder. Capture the PR
   **number** and **URL**.

10. **Best-effort board nudge (optional, needs `project` scope).** The PR
    auto-lands on the board as **Candidate**; move it to **In review** *if* the
    user keeps the board and the token has the scope:
    ```bash
    gh project item-edit ...   # set Status = In review for the PR's item
    ```
    If `gh project` errors (no scope, no board) **skip silently** — the open PR +
    `kb:draft` label is the source of truth, and the board is optional.

11. **Record it on the ticket** (`gh` succeeded → now write metadata):
    ```bash
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> \
      --set kb_status=draft --set kb_pr=<PR> --set kb_type="<type>"
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket> --touch
    ```
    `kb_status` moves `candidate → draft`; `kb_issue` stays. `--touch` refreshes
    `updated_at` without consuming an entry.

12. **Update the `## 📚 KB article draft` section** of `timeline.md` — replace the
    "Draft pending…" line with the draft link, title and type:
    ```
    ✍️ **Draft opened** (YYYY-MM-DD) — [PR #<PR>](https://github.com/<KB_REPO>/pull/<PR>)
    **Title:** _<the KB title>_ · **Type:** <type>

    _In review. Merge with `/kb-publish` once approved._
    ```
    Keep the earlier "Flagged as KB candidate" line above it.

13. **No `[NNN]` timeline entry** — bookkeeping, not an investigation step (step
    11 uses `--touch`). Brief response: confirm the draft, give the PR link, and
    say `/kb-publish` is next.

## Don'ts

- **Don't open the PR without confirmation** — generate + iterate in chat first.
- **Don't open a duplicate** — if `kb_pr`/`kb_status=draft` is set, point at the
  existing PR; if an article already covers it (step 4), offer to extend it.
- **Don't `git clone`** — branch, write, and PR all go through `gh api`.
- **Don't require the board** — the In review move is best-effort; skip on no scope.
- **Don't leak internal data into the public body** — keep it below the separator.
- **Don't bump `next_entry`** — no entry is created (`--touch` only).
- **Don't write through the github MCP** — it's read-only; writes are `gh`.
