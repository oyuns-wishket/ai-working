# HANDOFF — ai-working

## Next actions
- Resource cleanup completion: managed temporary servers and explicitly disposable owned containers now have cleanup workers and receipts; installed locally and verified with a real temporary HTTP server. See `docs/impl-notes/2026-10-28-resource-cleanup-completion.md`.
- UI workflow preflight is strengthened and linked to both agents; validators and 80 Node/90 Python tests pass. No pending UI implementation; published changes are verified by public-safety CI. See `docs/impl-notes/2026-10-27-ui-workflow-preflight.md`.
- Paseo archive resource cleanup is locally installed and verified. SSOT publication authorized; other machines need pull/bootstrap plus explicit plugin installation/reload.

## Decisions & context
- Temporary servers use the session-bound managed launcher. Container writable layers are removed only with the disposable label; volumes and unowned legacy resources remain preserved. Failed or uncertain cleanup retains evidence and receipts.
- UI workflow: global/dev-protocol now route menu, tab, information structure and navigation changes through design-workflow before implementation. Style reuse does not prove structure reuse; scoped UX decisions have their own evidence row.
- Use the official `agent.archived` plugin event, then wait for matching archived/closed state before invoking the existing resource guard with native session identity.
- Per-session OS file locks protect native/plugin overlap. Plugin source is canonical; runtime installation is machine-local and optional.
- Wiki binding explicitly excludes this tooling repository; knowledge remains in the repository.

## Open items & blockers
- No UI workflow implementation blocker. Other machines require their normal pull/bootstrap; no remote-machine changes requested.
- No implementation blocker. Plugin runtime remains asynchronous; inspect persisted worker receipts for actual cleanup outcomes.

## Lessons
- Existing design tokens and a chosen tab count do not decide content grouping or layout. Check those before source edits; retrospective skill reading does not satisfy preflight.
- A Paseo archive response proves archival, not native SessionEnd execution. Verify lifecycle effects with disposable markers and a direct positive control.
