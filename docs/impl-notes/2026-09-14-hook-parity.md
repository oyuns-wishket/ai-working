# 2026-09-14 Hook simplification and Claude/Codex parity

## Gate evidence
- User approved the audited direction: keep DB protections, fix resource ownership, bounded handoff, preserve UI integrations; remove automatic push and redundant per-edit work.
- User explicitly requested synchronization of Claude and Codex hooks, skills, rules, agents and instruction Markdown.
- Authorized: local setup, implementation and validation; the user subsequently explicitly requested commit, push and deployment of the verified result.
- Credentials, session history and private memories remain local; provider mechanics are adapters, not duplicated shared policy.

## Plan
- Fix resource ownership and unnecessary probes in an isolated worker.
- Audit instruction/skill/agent parity and native hook contracts read-only.
- Implement portable hook adapters, lean manifests, repeatable instruction synchronization and parity diagnostics.
- Verify with isolated fixtures, independent review, repository checks, then back up/apply to the live local environment.

## Decisions and deviations
- Repo-only: registry has no mapping for this repository.
- No UI work: design workflow skipped.
- Primary checkout contains this session's 20 previously verified edits. Created new isolated worktrees directly from clean HEAD and copied the owned files to lead; primary dirty files are preserved. This safely replaces the skill helper's blanket dirty-check restriction.
- Native worker sessions reused; no permanent worker definitions created.

## Validation
- Node hook/bootstrap suite: 32 top-level tests passed, including 29 mocked resource scenarios and quoted/newline SQL regressions.
- Python repository suite: 89 tests passed. Additional required skill suites: 52 tests passed (11 runtime guard, 5 context inspection, 16 Git publication, 5 multi-agent, 15 wiki context).
- Shell/Node/Python syntax, JSON parsing, diff whitespace, 26 skill validations and full-history public audit passed.
- Independent review reproduced and fixed SQL newline handling, malformed JSON preservation, runtime concurrent-write snapshots, native role registration collisions, dependent adapter conflicts and stale unrestricted role registrations.
- Applied canonical files locally; shared personal/external skills: 33 identical source targets, 66 asset checks with no drift/conflicts.
- Both platforms render 9 owned hook registrations from one definition. Native Codex trusted 9 reviewed owned definitions and restored 4 previously trusted unchanged UI definitions; subsequent review-required counts are zero, warnings zero.
- Installed bootstrap status: 73 normal. Repeated dry-run: 0 changes / 0 problems.
- No application build/lint commands exist; syntax, policy behavioral tests and native protocol fixtures are the relevant checks. No model calls or real Docker/DB mutations were used for tests.

## Local application and remaining scope
- Private backups preserve previous source/settings. Removed automatic HANDOFF Git writes and default per-edit reminders/lint.
- Migrated 14 existing personal interaction principles into the shared canonical policy; removed the duplicate local section only after exact body comparison.
- Local plugin profile disables duplicate team skill plugins and Superpowers startup; OMC explicit functionality and UI integrations remain. OMC keyword/skill auto-routing is skipped. Provider plugin internals are not represented as shared user-authored agents.
- Project inventory is read-only: 138 primary repositories, 38 conflicting skill source entries and 110 unsupported instruction/agent entries. The user explicitly deferred project-local Markdown/rules/agents changes to their own future project work; bulk project application is excluded.
- Project adapters and conflict-aware synchronizer are implemented/tested; existing project instructions and tool restrictions remain preserved.
- Publication is authorized. This configuration repository has a public-safety CI workflow and bootstrap installation, with no application/server deployment pipeline. Publish the reviewed shared changes on main (personal SSOT exception), verify CI and installed readiness; project-specific application is explicitly deferred to the user. Remove only clean task worktrees whose content is preserved in the published commit.
- Wiki optimization remains the next requested work after this environment scope is closed; no wiki content modified.

## Runtime limits
- Codex Bash PostToolUse returns plain output without an exit code. Exact Docker run/create IDs can prove ownership; ambiguous start/Supabase/Compose results require direct agent cleanup. Native write_stdin input does not have a separate PreToolUse event.
- Existing running sessions may retain previously loaded instructions; use a new session to load the synchronized skill catalog and rules.
