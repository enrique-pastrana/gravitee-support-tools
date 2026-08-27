#!/usr/bin/env python3
"""Set one or more fields in a ticket's metadata.json, atomically and validated.

Usage:
    set_meta.py <ticket-number> --set key=value [--set key=value ...]

Values are coerced by the KIND of the field (per-key typing), never guessed
from the value — so a version like "2.0" or "3.10" stays a string instead of
being silently turned into a float. Kinds:

    string   subject, customer, product, version, priority, ...
             stored verbatim; the literal "null" clears a nullable field.
    list     tags, related_tickets
             a JSON array (["a","b"]) or a comma-separated list (a,b,c);
             empty string -> [].
    bool     kb_candidate               true / false
    int      next_entry,                whole number; kb_issue / kb_pr are
             kb_issue, kb_pr            nullable ("null" clears them)
    number   resolution_time_hours,     int or float; "null" clears it
             last_comment_id

Keys are validated against the known schema, so a typo is rejected instead of
silently adding a junk field. Writes atomically (temp file + os.replace) and
re-validates the whole file as JSON before committing.

Refuses to act if metadata.json is missing or invalid.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from ticket_paths import resolve_ticket_dir

# Field kinds — the single source of truth for how each metadata field is
# typed. Keep in sync with templates/metadata.json. Anything not listed in the
# non-string sets below is treated as a plain string.
LIST_KEYS = {"tags", "related_tickets"}
BOOL_KEYS = {"kb_candidate"}
INT_KEYS = {"next_entry", "kb_issue", "kb_pr"}
NUMBER_KEYS = {"resolution_time_hours", "last_comment_id"}  # int/float, nullable
STRING_KEYS = {
    "ticket_id", "zendesk_url", "subject", "customer", "product", "version",
    "priority", "status", "opened_at", "updated_at", "resolved_at",
    "kb_status", "kb_type", "kb_url", "kb_published_at",
}
# Fields whose literal "null" means JSON null (clear the field).
NULLABLE_KEYS = {
    "resolved_at", "resolution_time_hours", "last_comment_id",
    "kb_issue", "kb_pr", "kb_status", "kb_type", "kb_url", "kb_published_at",
}

KNOWN_KEYS = LIST_KEYS | BOOL_KEYS | INT_KEYS | NUMBER_KEYS | STRING_KEYS


def coerce(key: str, raw: str):
    """Turn a raw CLI string into the correctly-typed value for `key`."""
    if key in NULLABLE_KEYS and raw == "null":
        return None
    if key in LIST_KEYS:
        raw = raw.strip()
        if not raw:
            return []
        if raw.startswith("["):
            value = json.loads(raw)  # a JSON array
            if not isinstance(value, list):
                raise ValueError(f"{key} expects a list, got {value!r}")
            return value
        return [item.strip() for item in raw.split(",") if item.strip()]
    if key in BOOL_KEYS:
        low = raw.strip().lower()
        if low not in {"true", "false"}:
            raise ValueError(f"{key} expects true/false, got {raw!r}")
        return low == "true"
    if key in INT_KEYS:
        return int(raw)
    if key in NUMBER_KEYS:
        try:
            return int(raw)
        except ValueError:
            return float(raw)
    return raw  # string, verbatim


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ticket")
    p.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        dest="assignments",
        help='Field to set, e.g. --set subject="Login fails". Repeatable.',
    )
    args = p.parse_args()

    if not args.assignments:
        print("error: nothing to set; pass at least one --set KEY=VALUE",
              file=sys.stderr)
        return 2

    # Parse, validate and type-coerce every assignment before touching disk.
    updates: dict[str, object] = {}
    for item in args.assignments:
        if "=" not in item:
            print(f"error: bad --set {item!r}; expected KEY=VALUE",
                  file=sys.stderr)
            return 2
        key, raw = item.split("=", 1)
        key = key.strip()
        if key not in KNOWN_KEYS:
            print(f"error: unknown metadata key {key!r}; known keys: "
                  f"{', '.join(sorted(KNOWN_KEYS))}", file=sys.stderr)
            return 2
        try:
            updates[key] = coerce(key, raw)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"error: bad value for {key!r}: {exc}", file=sys.stderr)
            return 2

    meta_path = resolve_ticket_dir(args.ticket) / "metadata.json"
    if not meta_path.is_file():
        print(f"error: {meta_path} not found", file=sys.stderr)
        return 1

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: {meta_path} not valid JSON: {exc}", file=sys.stderr)
        return 1

    meta.update(updates)

    # Serialise + validate before committing, then write atomically.
    rendered = json.dumps(meta, indent=2, ensure_ascii=False) + "\n"
    json.loads(rendered)  # sanity check
    tmp = meta_path.with_suffix(".json.tmp")
    tmp.write_text(rendered, encoding="utf-8")
    os.replace(tmp, meta_path)

    print(f"updated {', '.join(sorted(updates))} in {meta_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
