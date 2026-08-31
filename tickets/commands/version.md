---
description: Report which tickets-plugin version is running in this session and whether it's the latest.
---

You are reporting the version of the **tickets** plugin actually loaded in this
session — the cache under `${CLAUDE_PLUGIN_ROOT}`, not the source repo — and
whether it is the latest available.

## Steps

1. **Run** the version script and show its output verbatim:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/version.py"
   ```

2. **Relay the verdict** in one line:
   - `✓` on the latest → confirm; nothing to do.
   - `↑` a newer version exists → tell the user to run
     `/plugin marketplace update` then `/reload-plugins` to pull it in.
   - `⚠` ahead of the catalog, or `?` catalog unreadable → the marketplace is
     stale; suggest `/plugin marketplace update`.

Read-only. Takes no arguments. Do not edit any files.

> **Note:** "latest" means the marketplace **catalog** version — only as fresh
> as the last `/plugin marketplace update`. The source repo may be ahead of the
> catalog until it's published and the catalog is refreshed.
