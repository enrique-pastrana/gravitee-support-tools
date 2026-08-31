# Reproduction steps — TICKET-{{ticket_id}}

**Date:** {{date}}
**Engineer:** {{engineer}}
**Issue:** {{subject}}

---

## Environment

See [environment.md](environment.md) for the full setup.

**Summary:**
- Product / version: {{product}} {{version}}
- Stack repro → (stack, DB, OS, resources…) · Browser/UI repro → (URL, browser +
  version, viewport/resolution)

<!-- Name evidence files results/<NNN>_<short>.<ext>, where <NNN> is the timeline
     entry this repro is logged under (see /reproduce step 5). -->

---

## Steps to reproduce

### 1. (first step)

```bash
# command(s)
```

**Result:**
- (what happened)
- Evidence: [results/NNN_before.png](results/NNN_before.png)

### 2. (second step)

…

---

## Outcome

✅ / ❌ Issue reproduced.

---

## Validation of the fix

### Change applied

```yaml
# before
…
# after
…
```

### Re-test

```bash
# command(s)
```

**Result:**
- Evidence: [results/NNN_after.png](results/NNN_after.png)

---

## Files

- [environment.md](environment.md)
- [configs/](configs/)
- [results/](results/)

---

## Quick-start (for the team)

**Stack-based repro:**

```bash
# 1. Use these configs
cp reproduction/configs/* .
# 2. Bring up
docker compose up -d
# 3. Reproduce — the exact command
```

**Browser / UI repro (no stack):** open `<URL>` in `<browser + version>` at
`<viewport/resolution>`, then follow the steps above and capture the result in
`results/`.
