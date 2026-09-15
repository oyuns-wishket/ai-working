---
name: project-wiki-context
description: Resolve a Git project to a machine-local knowledge registry and retrieve only bounded, current canonical project context. Use before substantial work when a project has an explicitly connected knowledge namespace, or to diagnose registry coverage and freshness.
---

# Project wiki context

Use an optional knowledge registry without letting it override current code, migrations, tests, project instructions, or verified runtime evidence. Resolve project identity by credential-free Git remote so clones and worktrees share one mapping.

## Setup

The public resolver lives at `ai-working/skills/project-wiki-context/scripts/wiki_context.py`. Discover the `ai-working` checkout from the active skill symlink or ask for its root; do not assume a user home path.

Point `AI_WORKING_CONTEXT_REGISTRY_PATH` at a machine-local or project-owned registry root. Its default location is `~/.config/ai-working/context-registry`. The registry is not bundled with this public skill. Read [`references/registry-contract.md`](references/registry-contract.md) when creating or changing it.

## Resolve and route

```bash
python3 <ai-working-root>/skills/project-wiki-context/scripts/wiki_context.py resolve --project "$PWD"
python3 <ai-working-root>/skills/project-wiki-context/scripts/wiki_context.py route --project "$PWD" --query "<task>" --record --sample-kind development
```

Use only documents returned by `route`. For `read_mode:sections`, read only the returned inclusive line ranges; never expand them to the full file. Version 2 indexes are navigation-only and must not be injected or followed into other project folders. The resolver rejects stale, contested, malformed, oversized, escaped, or unregistered content and returns routing evidence rather than dumping the entire knowledge tree. Continue repository-only when resolution is unavailable or unhealthy and report that limitation.

V2 searches title/body plus bounded `aliases` and `tags`, including Korean spacing variants. A selected canonical result may bring at most one current related note into spare document/byte budget; `related_via` identifies the seed. Do not follow more links yourself. Manual notes cannot seed or receive this expansion. The owning contract may declare one level of business categories inside an already authorized namespace; undeclared folders remain unread.

## Observe actual use

For substantive development, retain the returned `retrieval_feedback.trace_id` with the current task and close it using [retrieval feedback](references/retrieval-feedback.md) after verification. Record `used` only for selected knowledge that actually influenced a checked decision; returned documents alone are not proof of use. Report missing, incorrect or outdated knowledge when observed. Unknown and absent feedback remain unknown. Use `evaluation` for test queries and `maintenance` for wiki management so neither inflates development results. A trace failure never blocks development. Omitting `--record` keeps the route command read-only.

## Diagnose

```bash
python3 <ai-working-root>/skills/project-wiki-context/scripts/wiki_context.py doctor --project "$PWD"
python3 <ai-working-root>/skills/project-wiki-context/scripts/wiki_context.py audit --workspace "<projects-root>"
```

`doctor` checks one project. `audit` compares discovered Git repositories with registry coverage without network access. Do not add customer identifiers or personal paths to this skill; mappings belong in the configured registry.

Report duplicate, stale or conflicting knowledge as read-only findings; diagnosis does not rewrite documents or refresh their verification dates. Development closeout uses `knowns` within its existing trigger and authorization. Scheduled raw-to-knowledge ingestion is owned by the knowledge repository's pipeline and policy, not this retrieval skill.

## Authority and safety

- Current repository and live project-owned infrastructure win when knowledge conflicts.
- Never read raw, derived, candidate or observation areas during ordinary work. `my-wiki` is read-only and only exact explicit bindings may be read; project tags alone do not authorize access.
- Never copy secrets, credentials, personal data, or customer-only payloads into output or public Git.
- Registry edits and wiki proposals are separate writes and require the authorization applicable to their owning repository.
