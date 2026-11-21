# HANDOFF — ai-working

## Next actions
- design-workflow now treats a deck spec supplied by a standard deck skill as the deck master (`small-feature`, no comps for layouts the builder stamps out; hand-written slides still get the new-expression check). Live for both agents on the first Mac and published; validators and tests pass locally; independent review findings folded in. Other machines need their normal pull/bootstrap. See `docs/impl-notes/2026-11-21-design-workflow-standard-deck-skill.md`.
- Flowpass input rules hook runs on the first Mac, the only machine where Flowpass is used, in both Claude Code and Codex. A rule text change needs only `global/flowpass-input-rules.md`. See `docs/impl-notes/2026-11-21-flowpass-input-rules.md`.
- Resource cleanup completion: managed temporary servers and explicitly disposable owned containers now have cleanup workers and receipts; installed locally and verified with a real temporary HTTP server. See `docs/impl-notes/2026-10-28-resource-cleanup-completion.md`.
- UI workflow preflight is strengthened and linked to both agents; validators and 80 Node/90 Python tests pass. No pending UI implementation; published changes are verified by public-safety CI. See `docs/impl-notes/2026-10-27-ui-workflow-preflight.md`.
- Paseo archive resource cleanup is locally installed and verified. SSOT publication authorized; other machines need pull/bootstrap plus explicit plugin installation/reload.

## Decisions & context
- Standard deck skills call design-workflow, never the reverse. The deck skill owns values (colors, type, frame, components, motion); design-workflow owns mode, decision records, full-page verification and delivery. A brand guide alone is still not a deck spec.
- Temporary servers use the session-bound managed launcher. Container writable layers are removed only with the disposable label; volumes and unowned legacy resources remain preserved. Failed or uncertain cleanup retains evidence and receipts.
- Flowpass input is gated by a deny-once PreToolUse hook per user request, not by injected context: context on that event arrives after the save. Rules text lives in `global/flowpass-input-rules.md`; lookups are allowlisted and everything else counts as input.
- Flowpass is used on the first Mac only (owner's decision, 2026-11-21). The second Mac keeps the installed hook, which never fires without a Flowpass MCP server; Flowpass is not connected there.
- UI workflow: global/dev-protocol now route menu, tab, information structure and navigation changes through design-workflow before implementation. Style reuse does not prove structure reuse; scoped UX decisions have their own evidence row.
- Use the official `agent.archived` plugin event, then wait for matching archived/closed state before invoking the existing resource guard with native session identity.
- Per-session OS file locks protect native/plugin overlap. Plugin source is canonical; runtime installation is machine-local and optional.
- Wiki binding explicitly excludes this tooling repository; knowledge remains in the repository.

## Open items & blockers
- The design-workflow copy shipped in the company marketplace plugin is maintained separately and has diverged from this source in both directions. Only the standard-deck judgment is being carried over there, through that repository's own merge request; nothing else is synchronized.
- Second Mac, Codex: none of the 11 managed hooks has ever been trusted there, so the guards do not run in Codex on that Mac. Run `codex_hook_trust.py --apply` there before using Codex on it.
- When the work app re-registers its hooks, Codex's position-based trust keys shift and the shifted managed hooks stop running in Codex until `./bootstrap.sh` restores the order. `bootstrap --status` reports it as a hook manifest that needs an update.
- `hook-dev-resource-guard` test fails on a cold first run on the second Mac (dev server cwd reported as `unknown`) and passes when rerun at once. Suspected cause: the 300 ms `lsof` probe limit; not verified.
- `public-safety` stops at the audit step on an existing agent-bot reference document, so CI has not reached the test steps since 2026-11-03.
- No UI workflow implementation blocker. Other machines require their normal pull/bootstrap; no remote-machine changes requested.
- No implementation blocker. Plugin runtime remains asynchronous; inspect persisted worker receipts for actual cleanup outcomes.

## Lessons
- Existing design tokens and a chosen tab count do not decide content grouping or layout. Check those before source edits; retrospective skill reading does not satisfy preflight.
- A Paseo archive response proves archival, not native SessionEnd execution. Verify lifecycle effects with disposable markers and a direct positive control.
