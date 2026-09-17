# Registry contract

The reader supports two layouts. V1 reads `<registry-root>/registry/project-registry.json`. V2 discovers the owning wiki’s `.system/knowledge-contract.json` and reads its `paths.registry`; a local adapter points to that owner without copying data. The root is selected by `--wiki-root`, `AI_WORKING_CONTEXT_REGISTRY_PATH`, or the machine-local default.

## Identity

- `id` is a normalized credential-free remote identity: lowercase host plus repository path without `.git`.
- Match `canonical_remote` first, then `remote_aliases`.
- Multiple local folders and Git worktrees with the same normalized remote resolve to one entry.
- `local_aliases` is diagnostic fallback only; it must not override a conflicting Git remote.

## Classification

- `connected`: a project-specific canonical wiki namespace is available.
- `common-only`: explicitly managed but currently receives only explicitly registered common context.
- `archived`: retained for history and excluded from normal retrieval.
- `excluded`: tooling, external clone, fixture, or other deliberately non-project repository.

Every discovered canonical remote must have exactly one registry entry or an explicit alias match. A no-remote local Git directory needs a registry-local exclusion if it is intentionally retained.

## Retrieval safety

- Default allowed status: `canonical`.
- Reject overdue documents (`review_by` before today), invalid/missing frontmatter, paths outside the registered namespace, and symlink escapes.
- Always exclude `raw/`, `derived/`, `.runtime/`, `omc-inbox/`, and `wiki/80-observations/` from ordinary retrieval.
- Enforce registry `max_documents` and `max_total_bytes`.
- V1 retains its legacy index behavior: `index.md` consumes bytes but no document slot, and `documents` combines the index with `query_documents`. V2 indexes are navigation-only, never injected, and consume neither budget; both result arrays contain only selected notes.
- Optional `intent_routes` map stable query terms to explicit namespace-relative documents. Intent score augments text
  overlap; a pinned document with neither signal is not injected merely because it is pinned.
- Return paths and routing evidence, not document bodies.
- Invalid registry identity, contract or namespace containment fails closed. Invalid or stale individual notes are excluded while healthy allowed notes remain available. With no valid relevant result, continue repo-only.

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

Customer canonical scopes are `sys-wiki/aidp/<customer_scope>` directories. Personal-domain entries instead own one flat `sys-wiki/<customer_scope>` root beside `aidp` (for example `sys-wiki/jyt`) and never read the work common scope. Without a category contract, only direct Markdown files are scanned. Common scope is always **only direct Markdown files** in `sys-wiki/aidp`. Common-only entries actually retrieve common notes and have no write target. Root indexes may list projects for human navigation, but v2 routing never injects indexes or follows their links. `navigation` is a path descriptor, not evidence. `documents` contains only selected knowledge and linked manual notes.

Scope and document security domains must match (`work`, `personal`, or `public`); mixed/unclassified are excluded. Customer scope must be the current customer or explicitly registered common scope. A project tag alone grants nothing. Canonical v2 notes require stable ID, type, owner, source references, status, schema version, security/customer scope, and valid verification/review dates. Stale and contested notes are excluded. Indexes are navigation-only and need no invented verification date.

Manual bindings require matching ID, title, security/customer scope, status and review date in the note. `draft` and `provisional` remain visibly user-authored, unconfirmed context; `contested`/`deprecated` are excluded. Manual notes are always read-only and never become a canonical write destination. Linking does not rewrite the note or silently promote its status. When metadata is missing, report the missing fields and request the user's intended scope as part of the explicit connection work.

Default retrieval policy merges with per-project overrides. V2 scans only scoped Markdown files (maximum 2 MB per file), ranks sections across the entire document, and returns either `read_mode:document` or exact `sections` with inclusive `line_start`/`line_end`. Read **only those line ranges** for section results; loading the whole file would violate the byte budget. Returned byte counts are actual UTF-8 bytes. A single line larger than the section budget cannot be selected and must be split during curation. Maximum documents and combined selected bytes remain bounded. No extra cache is needed at the current corpus size.


## V2 categories inside authorized namespaces

The owning contract may define `canonical_sections`, an object mapping exact project namespaces to category arrays. It may also define `default_project_sections`, used only for a registered `sys-wiki/aidp/<customer_scope>` namespace without an explicit override. An explicit empty array disables defaults for that namespace. Defaults never apply to the common root or personal namespaces. These fields authorize no new read scope: registry identity, security and customer checks run first.

Each array has at most 12 unique entries: required `slug` and `title`, optional `description` (default empty) and `terms` (default empty array). Unknown entry fields are rejected. Slugs contain lowercase letters/digits separated by hyphens, at most 64 characters; `raw`, `candidate`, `my-wiki`, `sys-wiki`, `aidp` and `index` are reserved. Title is nonempty and at most 80 characters; description at most 500. Terms are at most 8 nonempty strings of at most 80 characters, unique after trimming and case folding. All text is single-line and excludes control characters. Category terms describe navigation and do not by themselves select every note in a category.

`canonical_sections` has at most 1000 exact keys of form `sys-wiki/aidp/<slug>` or `sys-wiki/<slug>` (excluding the common `sys-wiki/aidp` root and the same reserved final slugs). A mapping for a namespace the registry does not authorize grants no access. Namespace roots and declared category directories must not be symlinks. The reader scans direct Markdown files in the root and each declared category only, never grandchildren or undeclared siblings. Category indexes remain navigation-only. `recursive:false` prohibits arbitrary recursion while allowing these explicitly declared one-level children. Missing optional fields preserve legacy flat retrieval; missing category folders are not created by the reader.

## V2 search and one-hop evidence

Canonical notes may include `aliases` and `tags` as JSON inline string arrays or flat YAML block lists. Each optional list has at most 8 nonempty, single-line strings of at most 80 characters, unique after trimming and case folding. Spacing-equivalent Korean phrases contribute only one match per list. Malformed lists exclude the note. Use short alternate task names and meaningful domain terms, not copied source text or broad keyword inventories. Whole-phrase matching tolerates Korean spacing and common grammatical particles; it does not turn short fragments into arbitrary substring matches. Title/body overlap and configured intent routes remain direct signals. Results expose `selection_reasons`, `matched_aliases`, `matched_tags` and `matched_phrases`.

`related` contains at most 6 distinct stable canonical IDs of at most 80 characters (for example `KB-DELIVERY-POLICY`), never the note’s own ID, paths or wiki-link markup. Human Markdown links stay in the body. The reader first selects direct results within `max_documents` and `max_total_bytes`, then may add **one** related target using remaining capacity. Relations never displace direct results or reserve a slot. The target must already be validated canonical-current evidence inside the same authorized scope or from a customer seed to allowed common knowledge (never common to customer); manual bindings are neither seeds nor targets. Duplicate IDs in the scanned corpus, invalid/stale/contested notes, dangling IDs and already selected targets are excluded. No second hop runs, including on cyclic graphs.

The supplemental result has `selection_reasons:["related-one-hop"]` and `related_via:{id,relative_path,relation}` naming the selected direct seed. It uses the same exact line ranges and actual UTF-8 budget as direct results. Alias-only matches without a matching body section may read bounded initial body sections, never just frontmatter. This is bounded lexical routing with curated relations, not semantic search; uncaptured synonyms may still require metadata curation.
