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

## Version 2 — owning wiki contract

The reader accepts v1 and v2. For v2 it discovers `.system/knowledge-contract.json` in the owning wiki; `paths.registry` locates the single registry, and canonical/candidate/manual paths must be `sys-wiki`, `candidate`, and `my-wiki`. A machine-local adapter may contain `registry/knowledge-root.json` with `{"schema_version":1,"knowledge_root":"<absolute owning wiki root>"}`. This pointer replaces data copies; an invalid pointer or contract fails closed.

Every v2 entry adds:

- `customer_scope`: the shared customer/project knowledge identity, independent of the Git repository identity.
- `read_scopes`: objects with `path`, `recursive:false`, `security_domain`, and `customer_scope`.
- `canonical_write_target`: the own canonical directory or null. Connected entries retain the same value in legacy `wiki_namespace`.
- `manual_read_bindings`: exact `{id,path,security_domain,customer_scope}` records for explicitly linked user notes. No binding means no read; removing one takes effect on the next route.

Customer canonical scopes are flat `sys-wiki/aidp/<customer_scope>` directories; common scope is **only direct Markdown files** in `sys-wiki/aidp`. Common-only entries actually retrieve common notes and have no write target. Root indexes may list projects for human navigation, but v2 routing never injects indexes or follows their links. `navigation` is a path descriptor, not evidence. `documents` contains only selected knowledge and linked manual notes.

Scope and document security domains must match (`work`, `personal`, or `public`); mixed/unclassified are excluded. Customer scope must be the current customer or explicitly registered common scope. A project tag alone grants nothing. Canonical v2 notes require stable ID, type, owner, source references, status, schema version, security/customer scope, and valid verification/review dates. Stale and contested notes are excluded. Indexes are navigation-only and need no invented verification date.

Manual bindings require matching ID, title, security/customer scope, status and review date in the note. `draft` and `provisional` remain visibly user-authored, unconfirmed context; `contested`/`deprecated` are excluded. Manual notes are always read-only and never become a canonical write destination. Linking does not rewrite the note or silently promote its status. When metadata is missing, report the missing fields and request the user's intended scope as part of the explicit connection work.

Default retrieval policy merges with per-project overrides. V2 scans only scoped Markdown files (maximum 2 MB per file), ranks sections across the entire document, and returns either `read_mode:document` or exact `sections` with inclusive `line_start`/`line_end`. Read **only those line ranges** for section results; loading the whole file would violate the byte budget. Returned byte counts are actual UTF-8 bytes. A single line larger than the section budget cannot be selected and must be split during curation. Maximum documents and combined selected bytes remain bounded. No extra cache is needed at the current corpus size.
