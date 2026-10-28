# Paseo archive resource cleanup

## 목표 / 확정 사항
- Archiving a Paseo agent or workspace must invoke the existing resource guard after the agent runtime closes, even when its native SessionEnd hook is skipped.
- Reuse confirmed resource ownership; never infer ownership from a process name, directory, or archive event.

## Gate evidence
- User requested improving the hook so Paseo archive performs cleanup, after a disposable Codex archive left a cleanup marker untouched and a direct hook control removed it.
- Authorized scope: canonical hook/plugin code, tests, documentation, and local installation/verification. No unrelated sessions, resources, provider binaries, or remote publication.
- No further product decision is needed. Use the official lifecycle plugin API and hot reload, without restarting the daemon.
- Worktree exception: clean personal SSOT checkout; direct-main local maintenance is allowed by the shared policy. Keep changes local pending publication authorization.

## Issue tracking
- Related open Paseo issues and resource PRs: none in the bounded searches.
- Skipped new issue: immediate local tooling maintenance; this note tracks acceptance and remaining work.
- Wiki resolution: explicitly excluded tooling repository; repo-only.

## 사각지대 / 검증
- `agent.archived` fires before runtime shutdown: poll the official snapshot until archived AND closed; refuse changed identities or restored sessions.
- Native SessionEnd and plugin may overlap: make marker consumption mutually exclusive, and retain existing ownership checks.
- Plugin is asynchronous: report dispatch/failure through plugin logs; do not label the archive response itself cleanup completion.
- No new auto-cleanup of dev servers or unowned resources. Real resource shutdown is tested with executable stubs, not live containers.
- No model/backend restart or package patch. Plugin registration requires local Paseo plugin support.

## 계획
1. Add a small official lifecycle plugin using native session identity and the installed resource guard.
2. Protect duplicate cleanup and add regression tests for close ordering, identity changes, unrelated resources, and failure paths.
3. Install locally, repeat the disposable archive marker test, run hook/bootstrap/public checks, and update handoff.

## 판단 근거
- Project teardown covers only owned worktrees; it misses local workspaces and individual agent archive.
- A wrapper or installed package patch couples cleanup to process internals and can disappear on upgrade.
- Official events cover both archive entrypoints and both existing hook backends.

## ⚠️ DEVIATION
- Initial PID-file lock was rejected during safety review: two callers could reclaim a dead owner's lock concurrently. Use OS `flock`, inherited through `exec`, instead.
- The installed plugin builder requires implementation modules under `server/`; moved the module there after the first local build reported the constraint. Hot reload then succeeded without daemon restart.
- Archive can remove a worktree before detached Supabase cleanup. Preserve explicit verified project identity and fall back to a temporary working directory; regression-tested without real containers.

## 검증 / 다음에 참고
- `node --test --test-concurrency=1 tests/*.test.mjs`: 80 tests passed (includes bootstrap and hook suites).
- After the removed-worktree regression, the three affected test files passed 18 tests; resource guard includes 32 executable-stub scenarios.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 90 tests passed.
- Initial parallel resource test hit its existing 300 ms lsof probe timeout (`cwd=unknown`); isolated rerun and full sequential suite passed. No unrelated probe behavior was changed.
- Local plugin build/status: running. Shared hook dry-run/apply succeeded. Native managed Codex hook trust stayed valid; no trust definitions changed.
- Disposable Codex agent archive: marker removed by plugin, unrelated marker retained. Disposable Claude workspace archive: marker already removed by native SessionEnd; plugin safely reported absent.
- Repeated the originally failing Codex workspace archive after restoring the disposable session: plugin removed the marker, unrelated marker remained. Disposable workspaces and working directories were then cleaned up.
- Existing sessions and daemon were not restarted; no live Docker/Supabase resources were started or stopped. Real shutdown behavior was tested with command stubs and immutable-ID ownership fixtures.
- Plugin logs distinguish dispatch, no state, skipped identity, and failure. Detached command success still needs actual resource observation; archive completion alone is not evidence.
- Public audit including new staged files and full history: passed. Skill validation: 25 passed. Installed bootstrap status: 76 current entries. Plugin status: running. Remote publication is outside this request.
