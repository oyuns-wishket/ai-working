# Hook behavior and local workspace configuration

`bootstrap.sh --status` checks installed files and wiring. `node --test tests/*.test.mjs` exercises hook behavior
under temporary homes without running migrations or modifying live projects. `node scripts/check_environment.mjs
--project <project-path> --json` reports local workspace matching and handoff size without writing files.

## Workspace scope

The advisory branch and implementation-note hooks read `$XDG_CONFIG_HOME/ai-working/workspaces.json`
(default `~/.config/ai-working/workspaces.json`):

```json
{
  "schema_version": 1,
  "workspace_roots": ["~/projects", "~/personal-projects"],
  "excluded_roots": ["~/personal-projects/ai-working"]
}
```

Paths stay machine-local. Roots accept absolute paths and `~/`; exclusions apply to a directory and its descendants.
Matching respects directory boundaries and resolves symlinks. Git worktrees outside a root inherit the owning
repository's workspace; an excluded repository stays excluded in its worktrees. The personal SSOT can be excluded
when its direct-main synchronization convention differs from application branches.

`AI_WORKING_PROJECTS_ROOT` preserves the old single-root override and takes precedence over the file.
`AI_WORKING_WORKSPACES_CONFIG` selects a different file. Without either setting the legacy `~/aidp` default remains.
An explicit empty `workspace_roots` array disables these advisory checks. Invalid configuration produces a diagnostic
instead of falling back to a broader root. This setting does not register wiki mappings or install workspace rules.

## Current context

The session-start hook selects a bounded excerpt of current handoff sections and points to the source for further
reading. Historical content remains on disk. A missing helper never triggers a full-document fallback; rerun bootstrap
to restore the installed helper. Keep current actions, decisions, and blockers in their existing canonical sections;
read completed history only for tasks that need it.

Claude consumes the session-start hook. Codex follows the same bounded-reading policy in `dev-protocol`; this change
does not assume that Codex runs Claude's SessionStart event. The installed helper is also callable directly.

## Approval behavior

`dev-protocol` owns scope and approval interpretation. Hooks can check explicit execution markers and project safety
policies, but cannot infer approval from a conversation. After checking the actual prior authorization and dry-run,
the agent passes the existing confirmation marker. It asks only about a new destructive change, unapproved production
scope, or another action outside the user's request. A marker alone is not evidence of user authorization.

## Regression coverage

- Oversized/multilingual handoffs, omitted sections, preserved source content, and missing helpers.
- Multiple roots, similarly named siblings, exclusions, symlink escapes, and detached-location worktrees.
- Migration dry-runs and already-confirmed commands accepted; unconfirmed writes rejected.
- Bootstrap preservation of unrelated hooks and repeated installation with zero changes.

Natural-language decisions also need scenario review: a request to deploy an already specified development change,
a new destructive production change, and a small change within an existing UI should lead to different decisions.
Passing shell tests does not prove that a model will interpret every instruction correctly.

## Lean defaults and actual parity

`global/governance-hooks.json` is the single policy definition for both runtimes. Bootstrap renders native Codex matchers/context budgets. Startup combines bounded metadata and handoff in one registration. GitHub issue and disk scans are opt-in (`AI_WORKING_STARTUP_ISSUES=1`, `AI_WORKING_STARTUP_DISK=1`). Per-edit lint/reminders and HANDOFF sync registrations are removed; the retired HANDOFF program is a harmless no-op even if an old registration remains elsewhere. Agents still update HANDOFF and run meaningful final verification under the same shared rules.

The resource guard exits before OS/Docker probes for unrelated tool calls. Ownership requires attributable successful output plus immutable container IDs; snapshots, new names, failed/pending commands and legacy claims never authorize cleanup. Both runtimes track a plain Docker run/create returning an exact full container ID. Structured successful responses can also confirm explicit Docker start and scoped Supabase starts. Native Codex Bash hooks currently return plain output without an exit code, so ambiguous start/Supabase results require manual Rule 16 cleanup. Compose, wrappers, compound commands and changed stack identities also remain manual. Docker Desktop quits only after successful empty-running-container detection. No live Docker was used for regression tests.

Native Codex maps exec_command to Bash and runs hooks for nested code-mode calls; write_stdin input has no separate PreToolUse. SessionEnd is main-thread-only and capped at three seconds, so cleanup is detached. The shell pattern guard is best effort, not an execution sandbox; quoted SQL and newline command boundaries have regression coverage.

Changing a Codex hook definition can invalidate native trust. Run `python3 scripts/codex_hook_trust.py --ensure-instructions` to inspect, then `--apply --ensure-instructions` after reviewing the authorized installed changes. It uses native currentHash/version checks and re-reads readiness. It preserves disabled hooks and refuses to trust unknown definitions. A matching bootstrap status and a zero managed trust-review count are separate checks; neither proves every possible shell command is covered.

## Local plugin and preference profile

`~/.config/ai-working/runtime-profile.json` optionally controls `lean_omc` and an explicit `disabled_claude_plugins` list. Bootstrap preserves unrelated settings, skips OMC keyword/skill auto-routing, and removes its old unconditional wrapper block with backups. It removes a local Interaction Principles section only when the same body is already canonical. OMC's own wiki/memory hooks do not all honor these skip tokens; they are separate from the configured project knowledge registry and require their own scoped review. Superpowers startup has no individual skip flag; disabling its plugin is an explicit local profile choice, never a cache edit.

External app status hooks are preserved. Native UI definitions whose registration index changes may require trust restoration; match the exact reviewed command and previously trusted native hash rather than accepting every installed hook.
