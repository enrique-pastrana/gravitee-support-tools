#!/usr/bin/env python3
"""Report the tickets-plugin version actually running this session.

Reads the version from ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json — i.e.
the cache dir Claude Code loaded for THIS session, not the source repo — and
compares it against the marketplace catalog (what a `/plugin marketplace update`
+ `/reload-plugins` would pull in). Read-only, no args.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def read_version(plugin_json: Path) -> tuple[str | None, str | None]:
    """Return (name, version) from a plugin.json, or (None, None) if unreadable."""
    try:
        data = json.loads(plugin_json.read_text(encoding="utf-8"))
        return data.get("name"), data.get("version")
    except (OSError, json.JSONDecodeError):
        return None, None


def parse_semver(v: str | None) -> tuple[int, ...]:
    """Best-effort numeric tuple for comparison; unknown sorts lowest."""
    if not v:
        return (-1,)
    parts: list[int] = []
    for chunk in v.split("."):
        num = "".join(c for c in chunk if c.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts) or (-1,)


def tilde(p: Path) -> str:
    home = str(Path.home())
    s = str(p)
    return "~" + s[len(home):] if s.startswith(home) else s


def main() -> int:
    root_env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not root_env:
        print("✗ CLAUDE_PLUGIN_ROOT is not set — run this via the /version command "
              "inside Claude Code so the loaded plugin path is resolved.")
        return 1

    root = Path(root_env).resolve()
    running_name, running = read_version(root / ".claude-plugin" / "plugin.json")
    if running is None:
        print(f"✗ Could not read {tilde(root / '.claude-plugin' / 'plugin.json')}")
        return 1
    name = running_name or "tickets"

    # Derive marketplace + plugin from the cache path layout:
    #   ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>
    catalog = None
    highest_installed = None
    try:
        # root == .../cache/<marketplace>/<plugin>/<version>
        version_dir = root
        plugin_dir = version_dir.parent            # .../<plugin>
        marketplace = plugin_dir.parent.name       # <marketplace>
        plugins_home = plugin_dir.parents[2]       # .../plugins

        catalog_json = (plugins_home / "marketplaces" / marketplace
                        / plugin_dir.name / ".claude-plugin" / "plugin.json")
        _, catalog = read_version(catalog_json)

        # Highest version present in the cache (sibling dirs of root)
        installed = [d.name for d in plugin_dir.iterdir()
                     if d.is_dir() and (d / ".claude-plugin" / "plugin.json").exists()]
        if installed:
            highest_installed = max(installed, key=parse_semver)
    except (OSError, IndexError):
        pass

    print(f"{name} plugin")
    print(f"  running (this session):    {running}")
    print(f"  root:                      {tilde(root)}")
    if highest_installed:
        print(f"  highest installed (cache): {highest_installed}")
    print(f"  marketplace catalog:       {catalog or 'unknown'}")
    print()

    # Verdict — compared against the marketplace catalog (the update source).
    if catalog is None:
        print("? Could not read the marketplace catalog version. Try "
              "`/plugin marketplace update`, then re-run /version.")
        return 0

    rv, cv = parse_semver(running), parse_semver(catalog)
    if rv == cv:
        print(f"✓ You are on the latest version ({running}).")
    elif rv < cv:
        print(f"↑ A newer version is available: {catalog} (you have {running}).")
        print("  Update with:  /plugin marketplace update   then   /reload-plugins")
    else:
        print(f"⚠ You are AHEAD of the catalog (running {running}, catalog {catalog}).")
        print("  The marketplace hasn't caught up — run `/plugin marketplace update` "
              "to refresh it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
