# Reference: substantive vs. non-substantive entries

Shared by `/log-updates` (incoming messages) and `/reply` (outgoing messages).
Classifying a message controls how much of it goes into `timeline.md` — don't
pay tokens to store process noise verbatim.

## Substantive

Answers a question we asked, brings a new technical fact, a decision, a new
symptom, or confirms a fix. → Log a **full entry**:

- A short **summary** of the main points in your own words — the idea, the
  decision, the symptom, the request. Do **not** paste the literal message; the
  verbatim text lives in the source (Zendesk), reachable via the comment id.
- A **"Key details (verbatim)"** block *only* for the load-bearing specifics
  where paraphrasing loses information — exact error messages, stack traces,
  version numbers, config values, commands, ids. Omit it when there are none.

## Non-substantive

Process noise with no technical content: "any update?", a reminder, an
acknowledgement, an out-of-office, "we're still looking into it", a pure holding
message. → Log a **one-line entry** only:

```
### [NNN] <date> - 🔔 <one sentence>
```

No `<details>`, no pasted body, no analysis, and **do not touch the Executive
summary**. (Still assign it an entry number and bump, so the timeline stays
chronological and complete.)

## When in doubt → full entry

The default bias is never to lose information; the one-line treatment is only
for what is clearly process noise. **Never drop a message entirely** — every
message becomes at least a one-line entry.
