# Environment efficiency and workflow consistency

## Goal
Bound automatic handoff context, reuse existing authorization consistently, support configured workspace roots, and record local task usage with validation outcomes.

## Gate evidence
- User requested the four reviewed improvements and explicitly asked to complete these before wiki optimization.
- Questions: none for implementation. The user subsequently authorized commit, push and deployment of the verified result.
- Authorized: scoped SSOT implementation, isolated workers, tests, local configuration and installation. No customer document rewrite or wiki mutation in this stage.
- Repository context: repo-only; no registry entry. Domain references are irrelevant to this tooling task.

## Plan
1. Isolate handoff and task-metrics implementation workers; lead owns workspace configuration and approval guidance.
2. Preserve handoff history; expose bounded current sections and source location.
3. Keep usage numeric, session-scoped and machine-local; distinguish unknown usage from zero and avoid billing claims.
4. Verify behavioral regressions, all repository CI checks, independent review, then install and exercise local behavior.

## Acceptance
- Oversized handoffs cannot create unbounded hook output; next actions and blockers remain visible.
- Existing approvals remain valid for their exact scope; new destructive/production scope still needs authorization.
- Multiple configured roots work with boundary-safe path checks and legacy configuration compatibility.
- Metrics tie elapsed time, selected session usage, reported retries and checks to a task without storing prompt content in public Git.

## Decisions
- No visual changes, model defaults or cache routing changes.
- Reuse native workers without creating permanent agent files.
- Existing design worktree remains untouched.

## Deviation
None.

## Validation in progress
- Workspace path boundaries, symlink escapes, legacy override, owner-worktree exclusion, hook decisions and read-only doctor: 8 tests passed.
- Independent workflow scenarios: approved development deployment proceeds; new destructive schema delta asks only for that scope; label-only PR and existing-pattern modal avoid new-design gates.
- Real large handoff samples now produce at most 8,192 bytes with unchanged source hashes and all three current sections; legacy Korean headings and archived subtrees are covered.

## Independent review
- Initial findings: nested archives could replace current handoff sections; incomplete Codex counter snapshots could hide later complete usage; pre-task deduplication markers needed a memory limit.
- All three were reproduced with synthetic inputs, corrected, and independently rechecked successfully.
- Repository has no application build or package lint command. Validation uses the existing public-safety CI checks: syntax/JSON, skill validation, public tree/history audit, hook/bootstrap and Python regression suites.

## Local application plan
- Configure both existing local project roots using the machine-local workspace file; exclude the personal synchronization repository from application branch reminders.
- Apply through the primary SSOT checkout and bootstrap; preserve installed external hooks and original handoff files.
- Use a dedicated verification measurement task for the final verification/install interval only; do not mislabel it as the duration of the entire implementation.

## Verified result
- Node hook/bootstrap/behavior suite: 29 tests passed (resource and DB guard scenario suites included).
- Python CI suites: 86 tests passed, including 28 task-metrics tests.
- Shell, Node and Python syntax, JSON, skill validation, public contents/history audit and whitespace checks passed.
- Final independent review passed, including native cache-write/thinking counters and partial snapshot recovery.
- Primary SSOT application preserved another session's unrelated design changes. Bootstrap applied five hook/helper files; status is 71/71, second dry-run has zero changes.
- Installed reader on three large real handoffs emitted at most 8,192 bytes with source hashes unchanged. Both configured roots and the SSOT exclusion matched as intended.
- Verification-only task measurement completed locally with explicit session attribution and check outcomes. Application build/package lint are not defined in this tooling repo and remain not-run rather than reported as passed.
- Publication is authorized together with the subsequent hook/parity work. Verify public-safety CI and local bootstrap readiness after push. Wiki optimization remains the next work unit.
