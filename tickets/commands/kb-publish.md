---
description: Publish a ticket's KB draft — merges its draft PR in the KB repo (closing the candidate Issue), indexes the article into the vectordb, and records the published URL on the ticket.
argument-hint: [ticket]
---

Final step of the KB lifecycle: `/kb-candidate` opened an **Issue**, `/kb`
opened a **draft PR** (`kb:draft`); `/kb-publish` **merges** that PR to `main`
— which closes the candidate Issue (`Closes #`) and makes the article canonical.
Full model → `${CLAUDE_PLUGIN_ROOT}/references/kb-workflow.md`.

**No clone** — merge + fetch go through `gh` / `gh api` (user's own auth; the
github MCP is read-only). Repo = **`$KB_REPO`**. Merging is outward and closes
the Issue: **inspect → confirm, then merge.**

## Steps

1. **Preflight** — `"${CLAUDE_PLUGIN_ROOT}/scripts/kb-preflight"`. On any `✗` stop
   and relay it (no merge without a working write path).

2. **Resolve the ticket** per `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`
   (chain **arguments > cwd > ask**; run the write-guards). `$ARGUMENTS`
   is the **ticket number**. State it in one line.

3. **Read `metadata.json`.** Require a draft:
   - `kb_status=published` → already published: link `kb_url`, stop (no re-merge).
   - `kb_pr` **unset** → nothing to publish: if `kb_issue` is set suggest `/kb`
     (write the draft first); else suggest `/kb-candidate`. Stop.

4. **Inspect the PR** — `gh pr view <kb_pr> --repo "$KB_REPO" --json
   state,mergeable,url,title,reviewDecision,files`:
   - `state=MERGED` → merged out-of-band: **skip the merge**, jump to step 6 to
     reconcile (index + record). Say so.
   - `state=CLOSED` (not merged) → the draft was rejected: tell the user, stop.
   - `state=OPEN` but `mergeable=CONFLICTING` (or a required review is missing) →
     surface it, tell the user to resolve it on the PR, stop. **Don't force it.**
   - `state=OPEN` and mergeable → report title + URL + review status for step 5.

5. **Confirm the merge** (one line: "Merge PR #<n> _<title>_ into `main`? This
   closes candidate Issue #<kb_issue> and publishes the article."). Merge only on
   an explicit yes:
   ```bash
   gh pr merge <kb_pr> --repo "$KB_REPO" --squash --delete-branch
   ```
   Squash-merge → one commit on `main`; the PR body's `Closes #<kb_issue>` closes
   the Issue; `--delete-branch` removes the `kb/…` branch.

6. **Resolve the canonical URL and fetch the merged article** (raw, no base64):
   ```bash
   DEF=$(gh repo view "$KB_REPO" --json defaultBranchRef --jq .defaultBranchRef.name)
   FILE=$(gh api "repos/$KB_REPO/pulls/<kb_pr>/files" --jq '.[].filename')
   KB_URL="https://github.com/$KB_REPO/blob/$DEF/$FILE"
   gh api "repos/$KB_REPO/contents/$FILE?ref=$DEF" \
     -H "Accept: application/vnd.github.raw" > /tmp/kb-article.md
   ```
   (Use the scratch dir, not the ticket folder, for the temp file.)

7. **Index into the vectordb** so future `rag_search` surfaces the distilled KB
   answer (private db → the full article, INTERNAL block included, is indexed on
   purpose):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/index_kb.py" <ticket> \
     --file /tmp/kb-article.md --url "$KB_URL" --path "$FILE"
   ```
   Report the one-line result. If it exits **2** (vectordb unreachable / stack
   down), tell the user to run `/tickets:tickets-up` and re-run this command
   later — **don't block** the publish bookkeeping on it.

8. **Record on the ticket** (`gh` merge succeeded → write metadata):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> \
     --set kb_status=published --set kb_url="$KB_URL" --set kb_published_at=<today>
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket> --touch
   ```
   `<today>` = YYYY-MM-DD. `kb_issue`/`kb_pr` stay for traceability. `--touch` =
   refresh `updated_at`, no entry consumed.

9. **Update the `## 📚 KB article draft` section** — keep the "Draft opened" line,
   add below it:
   ```
   ✅ **Published** (YYYY-MM-DD) — merged [PR #<PR>](https://github.com/<KB_REPO>/pull/<PR>) → [KB article](<KB_URL>)
   ```
   Then a brief response: confirm published, give the article URL, note the
   candidate Issue is closed and the article is indexed in the vectordb.

## Don'ts

- **Don't merge without confirmation**, and **don't merge a non-mergeable PR**
  (conflicts / missing required review) — surface it and stop.
- **Don't re-publish** an already-`published` ticket — link the existing URL.
- **Don't `git clone`** — merge + fetch go through `gh` / `gh api`.
- **Don't fabricate** `kb_published_at` — use today's date.
- **Don't block** the publish on an indexing failure (exit 2) — record it, tell
  the user to re-run after `/tickets:tickets-up`.
- **Don't bump `next_entry`** (`--touch` only) or **write through the github MCP**
  (read-only; writes are `gh`).
