# HANDOFF — ai-working

## Next actions
- Flowpass input rules hook is published and installed on both Macs. On the second Mac it cannot act yet: Flowpass is not connected there and Codex has not trusted the managed hooks. A rule text change needs only `global/flowpass-input-rules.md` and a pull. See `docs/impl-notes/2026-11-21-flowpass-input-rules.md`.
- Resource cleanup completion: managed temporary servers and explicitly disposable owned containers now have cleanup workers and receipts; installed locally and verified with a real temporary HTTP server. See `docs/impl-notes/2026-10-28-resource-cleanup-completion.md`.
- UI workflow preflight is strengthened and linked to both agents; validators and 80 Node/90 Python tests pass. No pending UI implementation; published changes are verified by public-safety CI. See `docs/impl-notes/2026-10-27-ui-workflow-preflight.md`.
- Paseo archive resource cleanup is locally installed and verified. SSOT publication authorized; other machines need pull/bootstrap plus explicit plugin installation/reload.

## Decisions & context
- Temporary servers use the session-bound managed launcher. Container writable layers are removed only with the disposable label; volumes and unowned legacy resources remain preserved. Failed or uncertain cleanup retains evidence and receipts.
- Flowpass input is gated by a deny-once PreToolUse hook per user request, not by injected context: context on that event arrives after the save. Rules text lives in `global/flowpass-input-rules.md`; lookups are allowlisted and everything else counts as input.
- UI workflow: global/dev-protocol now route menu, tab, information structure and navigation changes through design-workflow before implementation. Style reuse does not prove structure reuse; scoped UX decisions have their own evidence row.
- Use the official `agent.archived` plugin event, then wait for matching archived/closed state before invoking the existing resource guard with native session identity.
- Per-session OS file locks protect native/plugin overlap. Plugin source is canonical; runtime installation is machine-local and optional.
- Wiki binding explicitly excludes this tooling repository; knowledge remains in the repository.

## Open items & blockers
- Second Mac, Codex: all 11 managed hooks are untrusted, and no trust record there matches any of their definitions, so the guards have not been running in Codex on that Mac. `codex_hook_trust.py --apply` would turn on all 11 at once and waits for the owner's decision. Live checks with Claude Code and Codex on that Mac are pending too.
- `hook-dev-resource-guard` test fails on a cold first run on the second Mac (dev server cwd reported as `unknown`) and passes when rerun at once. Suspected cause: the 300 ms `lsof` probe limit; not verified.
- `public-safety` stops at the audit step on an existing agent-bot reference document, so CI has not reached the test steps since 2026-11-03.
- No UI workflow implementation blocker. Other machines require their normal pull/bootstrap; no remote-machine changes requested.
- No implementation blocker. Plugin runtime remains asynchronous; inspect persisted worker receipts for actual cleanup outcomes.

## Lessons
- Existing design tokens and a chosen tab count do not decide content grouping or layout. Check those before source edits; retrospective skill reading does not satisfy preflight.
- A Paseo archive response proves archival, not native SessionEnd execution. Verify lifecycle effects with disposable markers and a direct positive control.
