# Ingest modes

Select a mode only after reading the target wiki's governing rules. The target contract overrides these defaults.

## V2 contract mode — canonical system knowledge

Prefer this mode when the owner declares `.system/knowledge-contract.json`. Use its canonical schema/template/validator and the registry's `canonical_write_target`; never write `my-wiki`, even if it is explicitly linked for reading. Preserve stable topic ID, provenance, security domain, customer scope and actual verification dates. Search and update the existing topic; create only a new topic. The same owner validator applies to scheduled automatic ingestion and development closeout. The raw pipeline runs independently and does not invoke the interactive knowns approval workflow for each batch.

## Mode A — immutable source to compiled wiki

Use when the knowledge base has `raw/` or `raw/sources/` plus a curated `wiki/`.

1. Create one compact, immutable source snapshot in the prescribed origin folder.
2. Include project identity, task/issue, date, Git SHA, verified facts, user-approved meaning/goal/contribution, validation evidence, deviations, and source paths.
3. Never include secrets, personal data, full code, or unverified claims as facts.
4. Search for the existing canonical topic note before creating a page.
5. Merge approved knowledge, add source references, update links/status/freshness, then update index/log/manifest as required.
6. Run the prescribed compiler or integrity check.
7. Never edit, move, rename, or delete the new source snapshot after creation.

The `knowns` invocation counts as the user's request to begin this ingest workflow, but the source file is not created until the per-run exact write plan is approved.

## Mode B — mapped project note in an Obsidian vault

Use when the project rules map the project to a specific vault note.

1. Update only the mapped project note and explicitly related notes approved in the write plan.
2. Preserve the vault's frontmatter, section conventions, wikilinks, sensitivity, and review status.
3. Prefer concise current state, meaning, decisions, contribution, evidence, risks, and next actions over session transcripts.
4. Do not copy Slack originals, credentials, customer personal data, or broad source code.
5. If the env var identifies only the vault root but not the project note, ask the user to resolve the mapping.

## Mode C — direct governed wiki

Use when the wiki accepts direct edits without a raw layer.

1. Treat existing canonical notes as merge targets.
2. Add traceable source paths, task/issue, Git SHA, and verification date in the target schema.
3. Create a new note only when no existing canonical topic can absorb the durable delta.
4. Update index/backlinks/log and run the target validation.

## Mode D — proposed or remote knowledge system

Use only when project rules explicitly connect a remote knowledge workspace or a propose-only governance.

1. Use the designated skill/API/MCP rather than fabricating local files.
2. Preserve proposed/change-request status and optimistic concurrency rules.
3. Show the exact proposal before the external write.
4. Report the returned document/change-request identifiers.

Do not invoke `knowns` again from the remote wiki management workflow.

## Git publication after local ingest

For Modes A–C, publish only when the selected wiki is a Git repository separate from the project code repository by Git common-directory identity and the exact plan includes the repository root, every file, commit message, current branch, remote name, credential-redacted fetch/push URL, and whether a new remote branch may be created from an exact remote-advertised base SHA.

Run the target validation first, then pass both `--repo <wiki-git-root>` and `--project-repo <project-git-root>` to `scripts/publish_git.py --dry-run`. Run the same command without `--dry-run` and with the emitted `--preflight-token`; this binds the actual publish to the validated file content and Git state. Never replace the helper with broad `git add .`, force push, automatic pull/rebase, amend, or reset. Mode D uses its designated API/MCP result instead of local Git publication.

## Status and conflict handling

- Verified code/runtime fact: use the target's canonical or verified status only with actual evidence.
- User meaning/goal/contribution: attribute it as a user-approved project intent.
- Inference: mark provisional unless the user explicitly confirms it.
- Conflict: preserve both sources and use contested/contradiction workflow.
- Supersession: update links and archives only when the target rules allow it and the exact move/rename/archive was approved.
