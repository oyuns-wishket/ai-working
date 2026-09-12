# Registry contract

The canonical data file is `<registry-root>/registry/project-registry.json`. The registry root is selected by `--wiki-root`, `AI_WORKING_CONTEXT_REGISTRY_PATH`, or the machine-local default. Its schema and human-readable connection contract live beside it.

## Identity

- `id` is a normalized credential-free remote identity: lowercase host plus repository path without `.git`.
- Match `canonical_remote` first, then `remote_aliases`.
- Multiple local folders and Git worktrees with the same normalized remote resolve to one entry.
- `local_aliases` is diagnostic fallback only; it must not override a conflicting Git remote.

## Classification

- `connected`: a project-specific canonical wiki namespace is available.
- `common-only`: explicitly managed but currently receives only common/core context.
- `archived`: retained for history and excluded from normal retrieval.
- `excluded`: tooling, external clone, fixture, or other deliberately non-project repository.

Every discovered canonical remote must have exactly one registry entry or an explicit alias match. A no-remote local Git directory needs a registry-local exclusion if it is intentionally retained.

## Retrieval safety

- Default allowed status: `canonical`.
- Reject overdue documents (`review_by` before today), invalid/missing frontmatter, paths outside the registered namespace, and symlink escapes.
- Always exclude `raw/`, `derived/`, `.runtime/`, `omc-inbox/`, and `wiki/80-observations/` from ordinary retrieval.
- Enforce registry `max_documents` and `max_total_bytes`.
- The namespace `index.md` is mandatory navigation and does not consume `max_documents`; it still consumes
  `max_total_bytes`. `query_documents` contains only task-selected documents and legacy `documents` combines the index
  plus those documents.
- Optional `intent_routes` map stable query terms to explicit namespace-relative documents. Intent score augments text
  overlap; a pinned document with neither signal is not injected merely because it is pinned.
- Return paths and routing evidence, not document bodies.
- On any parse, identity, containment, status, or freshness failure, return no wiki documents and continue repo-only.

## Health and evidence

- `repo_state` reports the local branch, HEAD, tracking relation, divergence, and dirty-file count without fetching.
- `source_refs` of the resolved repository are checked locally for commit existence, path existence, HEAD ancestry, and
  path changes since the cited commit. Missing commit/path is invalid; non-ancestry is an applicability signal because a
  valid reference may belong to another release branch. No network lookup or credential is allowed.
- `healthy` is retained as connection compatibility. `status` is the user-facing result: `healthy`, `degraded`, or
  `unhealthy`; `knowledge_health` explains overdue canonical and critical pinned failures.

## Authority

Registry metadata routes context; it does not transfer runtime authority to the wiki. Current repo/code/migrations/tests and verified customer infrastructure take precedence over durable wiki knowledge.
