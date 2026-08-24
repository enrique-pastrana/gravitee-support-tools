# Reference: searching prior art in the vectordb

How to query the `vectordb` MCP (`rag_search`) for precedents and how to read
what it returns. Shared by `/new-ticket` (opening-message prior art) and
`/investigate` (precedent search before reasoning from scratch), so the query
mechanics stay consistent and the scoring finding lives in one place. Each
command decides *which* sources to hit and *when*; this is only the how.

## Query by literals, not prose

Extract the high-signal, distinctive tokens and search on those — a paraphrased
sentence flattens the scores and buries the real hit:

- exact error string (`StackOverflowError`, `Connection refused`)
- a log line, an exception class, a config key, a component name
- version / product identifiers when they're load-bearing

Literal > paraphrase. Anchor on **2–6 distinctive tokens**; a full sentence
retrieves worse, not better. Run **one `rag_search` per literal**, not one
blob mixing several. Skip the search entirely if the MCP is unavailable — say so
and carry on.

## Read the score by mode — don't threshold blindly

`rag_search` scores mean different things depending on the `hybrid` flag:

- **`hybrid=true` (default)** → a **positional** RRF score, ~`0.0164, 0.0161,
  0.0159…` for *every* query regardless of relevance. It ranks; it does **not**
  measure similarity. **Never threshold it.** Judge a hit by **reading** its
  source / path, not by the number.
- **`hybrid=false`** → real **cosine** similarity, 0–1, which discriminates:
  `≳0.6` is worth a look, low-`0.5`s is weak. Pass `hybrid=false` when you
  actually want a relevance number to compare hits.

So: default (hybrid) mode is for ranking candidates you then read; flip to
`hybrid=false` when you want a trustworthy similarity figure. Either way the
final call is made by reading the source, never by the score alone.

## What comes back today

The corpus is code/config plus tickets indexed so far — expect **code/doc**
hits as well as past tickets. Keep only genuinely relevant results (id/path,
one-line why); if nothing is relevant, say so in one line rather than forcing a
weak match.
