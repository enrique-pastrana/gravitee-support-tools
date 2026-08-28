---
description: Flag a ticket as a KB article candidate — opens a tracking Issue in the KB repo (labeled kb:candidate) and records it on the ticket. Pass a short reason as argument.
argument-hint: [reason] [ticket]
---

Flag a ticket as worth a KB article, mid-flow — before it's written. `$ARGUMENTS`
= the **reason** it's a candidate (and optionally a ticket number). This is the
first step of the KB lifecycle: a **candidate** is a GitHub **Issue** in the KB
repo (`kb:candidate`); `/kb` later turns it into a draft **PR**, and `/kb-publish`
merges it. Full model + repo setup → `${CLAUDE_PLUGIN_ROOT}/references/kb-workflow.md`.

**Writes go through `gh`** (the user's own auth); the github MCP is read-only.
Repo comes from **`$KB_REPO`** (`owner/name`). This step **creates an Issue** —
an outward action: **confirm before creating it.**

## Steps

1. **Preflight.**
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/kb-preflight"
   ```
   Checks `gh` installed + authed, `$KB_REPO` set + reachable, and the labels.
   On any `✗` stop and relay it — no Issue without a working write path.

2. **Resolve the ticket.** Per `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`
   (chain **arguments > cwd > ask**). `$ARGUMENTS` here is mostly the
   *reason*, not a number — treat a bare number in it as the ticket, the rest as
   the reason. State the resolved ticket in one line before writing.

3. **Read `metadata.json`.** If `kb_status` is already set (`candidate` / `draft`
   / `published`) or `kb_issue` is present, it's **already flagged** — link the
   existing Issue (`https://github.com/$KB_REPO/issues/<kb_issue>`) and ask
   whether to update the reason (edit the Issue) or skip. **Don't open a second
   Issue.**

4. **Capture the reason.** From `$ARGUMENTS`. If empty, ask the user briefly
   *why* it's a candidate (one sentence — "undocumented config", "recurring
   customer question", "non-trivial root cause worth distilling"). **Don't
   invent** a reason from the timeline — ask.

5. **Suggest the KB type — only if evident.** The four types (see
   `${CLAUDE_PLUGIN_ROOT}/references/kb-workflow.md`): **Problem / Solution**,
   **How-to**, **Troubleshooting**, **Question / Answer**. If the ticket clearly
   maps to one, note it so the Issue carries a pre-suggested type; if not, skip —
   `/kb` classifies later. Don't force one.

6. **Confirm, then create the Issue.** The KB repo is private / employee-gated,
   so internal references (ticket id, customer, product) are safe in the Issue.
   Preview the title + body, get a yes, then:
   ```bash
   gh issue create --repo "$KB_REPO" \
     --title "<ticket> — <short symptom-led title>" \
     --label "kb:candidate" \
     --body "$(cat <<'EOF'
   **Source ticket:** <ticket>
   **Product / version:** <product> <version>
   **Customer:** <customer>
   **Suggested type:** <type, or "TBD — classify at /kb time">
   **Why it's a candidate:** <reason>

   _Draft pending — run `/kb <ticket>` once the ticket is resolved._
   EOF
   )"
   ```
   The command prints the Issue URL. Capture its **number** (the trailing path
   segment) as `<issue>`.

7. **Record it on the ticket** (`gh` succeeded → now write metadata):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set_meta.py" <ticket> \
     --set kb_status=candidate --set kb_candidate=true --set kb_issue=<issue>
   # add --set kb_type="<type>" only if step 5 produced an evident type
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <ticket> --touch
   ```
   `kb_status` is the pipeline's source of truth; `kb_candidate=true` stays in
   sync so `/close --kb-candidate` and older reads keep working. `--touch`
   refreshes `updated_at` without consuming an entry.

8. **Update the `## 📚 KB article draft` section** of `timeline.md`. If it still
   holds the "Pending…" placeholder, replace it with:
   ```
   🏷️ **Flagged as KB candidate** (YYYY-MM-DD) — <one-line reason>.
   Tracking: [<KB_REPO>#<issue>](https://github.com/<KB_REPO>/issues/<issue>)[ — suggested type: **<type>**]

   _Draft pending. Generate with `/kb` once the ticket is resolved._
   ```
   If a draft link is already there (a prior `/kb` run), leave it and just add
   the flag line above.

9. **No `[NNN]` timeline entry** — this is bookkeeping, not an investigation
   step (that's why step 7 uses `--touch`, not a bump). The GitHub Issue **is**
   the candidate queue now — there are no `_kb/` files to update.

10. **Brief response:** confirm the flag, quote the reason back, and give the
    Issue link.

## Don'ts

- **Don't create the Issue without confirmation** — it's an outward write.
- **Don't open a duplicate** — if `kb_issue` / `kb_status` is set, point at the
  existing Issue and offer to update it.
- **Don't invent the reason** — ask when `$ARGUMENTS` is empty.
- **Don't generate the article** — that's `/kb`, after `/close`.
- **Don't bump `next_entry`** — no entry is created (`--touch` only).
- **Don't write through the github MCP** — it's read-only; writes are `gh`.
