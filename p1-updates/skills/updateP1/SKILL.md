---
description: Generate a who/what/when P1 status summary for Slack from a Fathom call. With no argument it uses the LATEST Fathom meeting via MCP; or name a meeting ("yesterday's call with X"); or paste a transcript. Reads only its chosen source and prints to chat — writes nothing.
argument-hint: [nothing = latest meeting | "yesterday's X call" | a pasted transcript]
---

You are producing a **who/what/when** summary for a P1 / Slack update, based on
a customer call.

## Input — source selection

Pick the source in this order:

1. **`$ARGUMENTS` is empty (the 90% case — "the latest call"):** call
   `list_meetings` on the `fathom` MCP server and take the most recent meeting
   from the result. Take its `recording_id` and read it per **Reading the
   meeting** below. **Always state which meeting you picked (title + date)** so
   a wrong pick gets caught immediately.

2. **`$ARGUMENTS` is a hint, not a transcript** (e.g. "yesterday's call with
   McDon's", "the OCTO one"): call `search_meetings` with the hint as the query
   and `recorded_by: "anyone"`, unless the user named a specific person.
   `search_meetings` matches keywords against titles and summaries with AND
   logic, so a long hint can match nothing — if it returns empty, retry with
   fewer, more distinctive words. If it still returns nothing, fall back to
   `list_meetings` and filter the returned list yourself by title / date /
   invitee.
   - Exactly one clear match → use it.
   - Several or none → show the candidates (title + date) and ask the user to
     pick. Do not guess.

3. **`$ARGUMENTS` looks like a pasted transcript / notes** (long, multi-line,
   speaker-like): use it directly — the manual fast path. Call no Fathom tool.

4. **Fallback:** if a Fathom tool errors or the server is unavailable, do **not**
   block — tell the user Fathom is unreachable and ask them to paste the
   transcript instead.

## Reading the meeting

Once you have a `recording_id`:

- **Default to `get_meeting_transcript`.** The who/what/when format has to
  attribute each action to Gravitee or to the Customer, and only the transcript
  shows who actually said what.
- **Use `get_meeting_summary` instead when the transcript is too long to work
  with**, or when the user asks for a quick pass. Say so in your reply — a
  summary-based update can blur who committed to what.

Read one source, not both.

## Output

Print the summary **in chat only**, ready for the user to copy and paste into
the Slack channel. Do **not** write it to any file.

## Format

Two sections, **Current status** and **Next steps**. Inside each, one block per
actor. Exactly two possible actors:

- **Gravitee** — our own actions/findings.
- **Customer** — the customer side. Use the generic word **"Customer"**, never
  the real customer name and never third parties by name (e.g. say "the
  customer's upstream provider", not the actual vendor).

Block shape:

```
Current status
Who: Gravitee
What:
- <bullet>
- <bullet>

When: <when>

Who: Customer
What:
- <bullet>

When: <when>

Next steps
Who: Gravitee
What:
- <bullet>

When: <when>

Who: Customer
What:
- <bullet>

When: <when>
```

Rules:
- **Omit any actor that has nothing** in that section — it's normal for only
  Gravitee to appear in *Current status* and only Customer in *Next steps*, etc.
- If a whole section has no content for either actor, omit the section.
- Keep bullets short and factual — this is a glance update, not a report.
- Convert relative dates to concrete ones (use today's date for "today").
- **When** is a single line per block summarising the timing of that block's
  bullets. Always put it on its **own line, with a blank line before it**
  (separated from the What bullets) — never on the same line as a bullet.
- Strip customer/third-party names per the rules above.

## Steps

1. Select the source per **Input** above (latest / hint / pasted / fallback).
2. If you used a Fathom tool, state which meeting you picked (title + date).
3. Read the chosen source; extract who did/established what, and what each
   actor still owes.
4. Build the summary: *Current status* = what each actor has established / done
   so far; *Next steps* = what each actor still owes.
5. **Print** the summary in chat. Then ask if the user wants tweaks before
   pasting it into Slack.
