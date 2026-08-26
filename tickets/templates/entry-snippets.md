# Timeline entry snippets

Reusable Markdown blocks. The slash commands and Claude itself use these
shapes when appending entries to `timeline.md`. Do not copy this file
verbatim — pick the snippet that fits and substitute the placeholders.

## Generic shape

```markdown
### [NNN] YYYY-MM-DD HH:MM - <emoji> Short title

(One short paragraph describing what happened.)

📎 **Attachments:**
- 🖼️ [received/YYYY-MM-DD/NNN_name.png](received/YYYY-MM-DD/NNN_name.png) — short description
- 📄 [received/YYYY-MM-DD/NNN_name.log](received/YYYY-MM-DD/NNN_name.log) — short description

<details>
<summary>🔍 <b>Investigation</b> (N messages)</summary>

#### Q1: (question)

**Claude:**
(answer)

**Note:** (engineer's takeaway, optional)

</details>

**✅ Takeaway:** (one-line conclusion)

---
```

## Emojis by entry type

- 📥 Inbound message from the customer
- 📤 Outbound reply to the customer (draft or sent)
- 🔒 Internal note (not visible to the customer)
- 🔗 Linked source (Jira, another ticket)
- 🔍 Investigation step (own analysis, log review, similar-ticket search)
- 🧪 Reproduction milestone
- ✅ Resolution / confirmation
- 🛠️ Configuration or environment change applied
- ⚠️ Risk, blocker, open question
- 🔔 Non-substantive one-liner (ack, holding message, ping)

## Incoming update

For an entry logged from a Zendesk comment (customer message, a reply we sent,
an internal note, a linked Jira update, …). **Summarise — don't paste the
literal**; the verbatim text lives in Zendesk, reachable via the comment id in
the footer. Pick the emoji/source label that fits (📥 customer, 📤 our reply,
🔒 internal note, 🔗 linked source).

```markdown
### [NNN] YYYY-MM-DD HH:MM - 📥 Customer: <short subject>

**Summary:** (2–4 lines: the idea, decision, symptom, or request — the main
points, in your own words.)

**Key details (verbatim):** (only the load-bearing specifics where paraphrase
loses information — exact error messages, versions, config values, commands,
ids, inside a fenced code block. Omit this block entirely if there are none.)

📎 **Attachments:**
- 🖼️ [received/YYYY-MM-DD/NNN_xxx.png](received/YYYY-MM-DD/NNN_xxx.png)
  - Shows: …
- 📄 [received/YYYY-MM-DD/NNN_xxx.log](received/YYYY-MM-DD/NNN_xxx.log) (X MB)
  - Contains: …

<details>
<summary>🔍 <b>Initial analysis</b></summary>

(notes from your read of the attachments — only if you actually have something)

</details>

🔗 Zendesk comment #<comment_id>
```

## Outbound reply draft

```markdown
### [NNN] YYYY-MM-DD HH:MM - 📤 Reply to customer

(English draft ready to paste into Zendesk.)

> Hi <team>,
>
> …
>
> Best,
> <your name>
```

## Reproduction milestone

```markdown
### [NNN] YYYY-MM-DD HH:MM - 🧪 Reproduction

(What you did and why. Link to reproduction/steps.md.)

📁 Detailed steps: [reproduction/steps.md](reproduction/steps.md)

**Outcome:** ✅ Reproduced / ❌ Not reproduced
- Evidence: [reproduction/results/NNN_xxx.png](reproduction/results/NNN_xxx.png)
```

## Local stack

For a Gravitee stack spun up locally via `/stack` (gravitee-stacker). One entry
per ticket's stack activity — append lifecycle changes (torn down, version
switched) to the same entry's `<details>` rather than adding new ones.

```markdown
### [NNN] YYYY-MM-DD HH:MM - 🛠️ Local stack

**Up:** APIM <version> (instance `<ticket>`, variant/features if any) — <license mode: OSS / EE>.

**URLs:** console http://localhost:8084 (admin/admin) · gateway :8082 · mgmt-api :8083

<details>
<summary>🛠️ <b>Stack lifecycle</b></summary>

- YYYY-MM-DD HH:MM — up (APIM <version>, instance `<ticket>`)
- YYYY-MM-DD HH:MM — torn down (volumes kept / wiped)

</details>
```

## Resolution

```markdown
### [NNN] YYYY-MM-DD HH:MM - ✅ Resolved

Customer confirmed resolution. Final status: resolved.

**Root cause:** …
**Fix applied:** …
**KB candidate:** yes / no
```
