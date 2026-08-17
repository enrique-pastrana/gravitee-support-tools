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
- 📤 Outbound reply to the customer (draft)
- 🔍 Investigation step (own analysis, log review, similar-ticket search)
- 🧪 Reproduction milestone
- ✅ Resolution / confirmation
- 🛠️ Configuration or environment change applied
- ⚠️ Risk, blocker, open question

## Inbound customer message

```markdown
### [NNN] YYYY-MM-DD HH:MM - 📥 Customer: <short subject>

> (quoted message from the customer)

📎 **Attachments:**
- 🖼️ [received/YYYY-MM-DD/NNN_xxx.png](received/YYYY-MM-DD/NNN_xxx.png)
  - Shows: …
- 📄 [received/YYYY-MM-DD/NNN_xxx.log](received/YYYY-MM-DD/NNN_xxx.log) (X MB)
  - Contains: …

<details>
<summary>🔍 <b>Initial analysis</b></summary>

(notes from your read of the attachments)

</details>
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

## Resolution

```markdown
### [NNN] YYYY-MM-DD HH:MM - ✅ Resolved

Customer confirmed resolution. Final status: resolved.

**Root cause:** …
**Fix applied:** …
**KB candidate:** yes / no
```
