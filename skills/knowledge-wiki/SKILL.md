---
name: knowledge-wiki
description: Read and propose edits to a versioned knowledge workspace through a configured MCP or API adapter. Use for knowledge tree, search, document reads, proposed updates, conflict recovery, recent changes, and workspace health checks.
---

# Knowledge wiki

Use only an adapter already available in the active toolset or configured in a machine-local file. Do not assume a vendor, workspace, endpoint, or credential source.

## Read

1. List workspaces when the target is unclear.
2. Use tree or search to narrow the request before reading full documents.
3. Prefer current canonical documents. Surface contested, stale, or superseded status.
4. Keep retrieval bounded to the task; do not dump an entire workspace, raw ingestion area, or activity history.

## Proposed edits

Pull the target document and capture its version identifier. Produce a focused patch that preserves frontmatter and unrelated content. Push as a proposal when the adapter supports review states; do not silently publish over a governed document.

On a version conflict, pull the new version, merge the intended delta, show the changed result, and retry once with the new base version. Stop after another conflict. Use an idempotency key when the adapter supports one.

## Safety

- Never place secrets, personal data, customer-only payloads, or broad source dumps in the wiki.
- Do not print API keys or raw authorization headers.
- Key creation or rotation requires the user's explicit request and verification that the workspace owner authorizes it.
- Report workspace, document title, proposal/version result, and any conflict without exposing private identifiers unnecessarily.

Adapter-specific schemas remain in the adapter or project that owns them. This public skill defines the workflow without copying any external implementation.
