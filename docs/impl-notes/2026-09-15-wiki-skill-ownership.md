# Wiki skill ownership

## Gate evidence

- The user explicitly requested removal of the legacy `wiki-curator` skill and use of `knowns` and `project-wiki-context` for the current wiki workflow.
- Scope: remove the owned skill and installed links; retain bounded duplicate/conflict handling in the existing closeout owner; clarify read/write responsibilities.
- Existing authorization covers shared-environment commit, push and local synchronization. No customer repository, wiki data or scheduled ingestion runtime is changed by this maintenance task.
- The personal synchronization repository permits a direct main change. Four unrelated design-workflow edits are preserved by exact path and hash; they are not staged or committed.

## Issue tracking

- Skipped: bounded catalog maintenance completed in one work unit. Open issues and PRs were queried successfully and none matched; no retrospective issue is needed.
- Broader knowledge-layout and ingestion work remains tracked in its own repository.

## Plan

1. Remove the old entrypoint and update the catalog and ownership map.
2. Preserve topic matching, evidence-based supersession, unresolved-conflict handling and stale-date semantics inside the existing knowns flow.
3. Clarify that project-wiki-context diagnoses and reads; the owning repository runs scheduled ingestion.
4. Run skill/public audits and existing hook/bootstrap tests; dry-run bootstrap, apply only the reviewed owned-link removal, then verify parity.

## Decisions

- No alias skill or replacement curator entrypoint is added.
- The existing knowns production closeout trigger and its user-choice boundary are unchanged. Scheduled raw ingestion has a separately authorized repository-owned policy and does not invoke interactive closeout on each item.
- Existing provider caches, unrelated integration skills and project-local instructions remain under their current owners.

## Verification

- Skill validation: 24 public skills passed.
- Full-history public audit passed after staging the owned deletion. The first unstaged audit could not read the deleted tracked file; no audit rule was bypassed.
- Existing hook/bootstrap tests: 34 passed. Existing knowns tests: 21 passed. No new tests were added for this instruction/catalog-only change.
- Bootstrap dry-run: exactly two stale owned links, no unrelated changes. Applied the same removal and verified both catalogs no longer contain the entrypoint.
- Retained knowns/project-wiki-context directories resolve to identical sources for both platforms. Global rule resolution remains unchanged.
- Four unrelated design-workflow file hashes remain unchanged.
- Publication and final bootstrap status are verified at task completion.
