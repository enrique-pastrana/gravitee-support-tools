---
description: Create or update the reproduction/ folder for a ticket and log the attempt as a 🧪 timeline entry.
argument-hint: <ticket number (optional)>
---

Set up or update a reproduction: **the user drives the repro, you format and
record it.** `$ARGUMENTS` is an optional **ticket number**; if empty, resolve the
current ticket.

**Conventions**
- Ticket data → workspace `$TICKETS_ROOT` (default `~/TICKETS`).
- Scripts/templates/references → `${CLAUDE_PLUGIN_ROOT}`; never write plugin files
  into the workspace.
- Every helper takes the **bare** number and resolves the folder itself.

## Steps

1. **Resolve the ticket.** Follow `${CLAUDE_PLUGIN_ROOT}/references/resolve-ticket.md`,
   chain **arguments > current > cwd > ask** (an explicit number is a one-off — it
   does **not** move the pointer). State which ticket and how. `/reproduce`
   writes → run the write-guards: explicit ≠ current → confirm · cwd ≠ current →
   ask · ticket doesn't exist → offer `/new-ticket` · content mismatch → flag.
   Resolve the folder once:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ticket_paths.py" <number>
   ```

2. **Look for a reusable precedent before building from scratch** — has this
   symptom already been reproduced (compose, steps, configs worth cloning)?
   Query by literals per `${CLAUDE_PLUGIN_ROOT}/references/search-precedents.md`
   (`rag_search` per literal; Zendesk / Jira for cases handled elsewhere). Cite
   each source; skip if MCP is down or the repro is obviously novel. Offer to
   reuse what you find — never copy it in silently.

3. **Create or open `reproduction/`.**
   - **Doesn't exist** → create the scaffold:
     ```bash
     python3 "${CLAUDE_PLUGIN_ROOT}/scripts/init_reproduction.py" <number>
     ```
     Makes `reproduction/{steps.md,environment.md,configs/,results/}`, rendering
     `steps.md`/`environment.md` from `metadata.json` (subject, product, version,
     engineer, date). Refuses to overwrite an existing folder.
   - **Exists** → read `reproduction/steps.md` to know where to append.

4. **Ask what to log now** — the user picks; don't assume:
   - environment setup, · a new step, · a result (screenshot/log) to attach,
   - the outcome (✅ reproduced / ❌ not), · applying the fix and re-testing.

5. **Write his input into the right place** — format only, invent nothing:
   - **Steps** → numbered list under `## Steps to reproduce` in `steps.md`.
   - **Environment** → fill the target/local sections of `environment.md`.
   - **Configs** → save under `reproduction/configs/` with a descriptive name;
     if he gives a path, copy the file there (versioned repros → a
     `configs/<version>/` subfolder, matching how he already organises them).
   - **Results** → save under `reproduction/results/` as `NNN_<short>.<ext>`,
     where `NNN` is the timeline entry this repro is tied to.
   - **Outcome** → set the `## Outcome` line (✅ / ❌) once he confirms it.

6. **Log a 🧪 entry in `timeline.md`.** Format via the `Reproduction milestone`
   block of `${CLAUDE_PLUGIN_ROOT}/templates/entry-snippets.md` (link to
   `reproduction/steps.md`, state the outcome, link evidence in `results/`):
   - **first repro touch this session** → **new entry `[NNN]`** 🧪
   - **follow-up update this session** → **append to that same entry's
     `<details>`** — don't spawn a new entry per paste.

7. **Stamp `updated_at`** — deterministic, atomic, never hand-edited:
   - new entry → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number>`
     (prints the consumed `NNN`, refreshes `updated_at`) → write entry `[NNN]`
   - appended to existing entry → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bump_entry.py" <number> --touch`
     (refreshes `updated_at`, no bump)
   - `/reproduce` doesn't change `status` (Zendesk-anchored; moved by
     reply/log-updates/close) → **no `set_meta`/`render_header`.**

8. **Refresh `## 📋 Executive summary`** only if the outcome changed the picture
   (reproduced ✅ / couldn't reproduce ❌ / new blocker). Minor paste → leave it.
   It's the single source of truth `/status` and `/reply` read.

9. **Reply briefly:** the outcome + "Logged in entry [NNN]." Point at
   `reproduction/steps.md`; don't repeat what's already in the timeline.

## Don'ts

- **Don't generate a docker-compose / k6 script / config the user didn't ask
  for** — he drives the reproduction; you format it. (Provisioning an
  environment is a separate, explicitly-invoked job — a dedicated `/stack`
  command, coming.)
- **Don't auto-run his steps.** Reproductions spin up local services, change
  config, or consume RAM — that's his call, not yours.
- No hand-editing `metadata.json` — use `bump_entry.py` (`--touch` when appending).
- No fabricated precedents — search finds nothing → say so.
