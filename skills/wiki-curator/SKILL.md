---
name: wiki-curator
description: Curate contradictions, stale documents, and supersession links in a governed knowledge workspace. Use when asked to clean or reconcile a wiki, especially after a large ingestion. Produces reviewable proposals instead of silently rewriting canonical knowledge.
---

# Wiki curator

Use the configured `knowledge-wiki` adapter to run a bounded detect → label → resolve → compact loop. The model proposes changes; the workspace's normal review process decides canonical state.

## Detect

Start with recent changes, contested documents, stale-document lint, and a narrow search for overlapping claims. Expand to linked neighbors only when needed. Do not scan raw ingestion stores or the whole workspace by default.

For each candidate, record document titles, claim summaries, dates, source references, and why the claims conflict. Avoid copying long passages.

## Classify

Choose one:

- `duplicate`: same claim and scope;
- `supersedes`: a newer claim has objective version/date evidence;
- `scope-split`: both are valid for different products, environments, or periods;
- `contested`: evidence cannot determine the current claim;
- `stale`: review date passed without a direct contradiction.

Never infer supersession from writing style or confidence alone.

## Propose resolution

Create one review batch containing the affected documents, recommended classification, exact proposed edits/links, and unresolved choices. If direction is ambiguous, ask one concise choice through the workspace's review mechanism rather than choosing a winner.

Apply accepted proposals with base-version checks. On conflict, pull and merge once; stop after a second conflict. Preserve source references and add explicit supersession or scope metadata rather than deleting historical context.

## Compact and verify

After accepted resolutions, rerun contradiction/staleness lint on only the affected neighborhood. Compact duplicates when policy permits, preserving redirects or replacement links. Report counts for proposed, accepted, unresolved, stale, and conflict-blocked items.

Never include credentials, personal data, customer-only payloads, or unreviewed source dumps in proposals.
