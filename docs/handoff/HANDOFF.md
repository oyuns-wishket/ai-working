# HANDOFF — ai-working

## Next actions
- UI workflow preflight is strengthened and linked to both agents; validators and 80 Node/90 Python tests pass. No pending UI implementation; published changes are verified by public-safety CI. See `docs/impl-notes/2026-10-27-ui-workflow-preflight.md`.

## Decisions & context
- UI workflow: global/dev-protocol now route menu, tab, information structure and navigation changes through design-workflow before implementation. Style reuse does not prove structure reuse; scoped UX decisions have their own evidence row.
- Wiki binding explicitly excludes this tooling repository; knowledge remains in the repository.

## Open items & blockers
- No UI workflow implementation blocker. Other machines require their normal pull/bootstrap; no remote-machine changes requested.

## Lessons
- Existing design tokens and a chosen tab count do not decide content grouping or layout. Check those before source edits; retrospective skill reading does not satisfy preflight.
