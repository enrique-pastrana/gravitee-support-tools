# Reproduction steps — TICKET-{{ticket_id}}

**Date:** {{date}}
**Engineer:** {{engineer}}
**Issue:** {{subject}}

---

## Environment

See [environment.md](environment.md) for the full setup.

**Summary:**
- Product / version: {{product}} {{version}}
- (Add stack, DB, OS, resources…)

---

## Steps to reproduce

### 1. (first step)

```bash
# command(s)
```

**Result:**
- (what happened)
- Evidence: [results/before_fix.png](results/before_fix.png)

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
- Evidence: [results/after_fix.png](results/after_fix.png)

---

## Files

- [environment.md](environment.md)
- [configs/](configs/)
- [results/](results/)

---

## Quick-start (for the team)

```bash
# 1. Use these configs
cp reproduction/configs/* .

# 2. Bring up
docker-compose up -d

# 3. Reproduce
# (the exact command)
```
