# Resource cleanup completion

## 목표 / 확정 사항
- Session-bound temporary servers and disposable container layers are cleaned on native end and archive; persist cleanup outcomes.

## Gate evidence
- User asked to improve disk remnants and temporary servers after the resource audit.
- Authorized: shared cleanup implementation, tests, documentation, local installation. Subsequent user request authorized SSOT commit/push, including the dependent archive integration.
- Preserve volumes, arbitrary existing container data, unrelated processes and uncommitted changes.
- Logic-only tooling change; no UI or visual prototype required.
- Existing staged archive implementation is a dependency. Continue in canonical checkout, preserving its index; dirty state prevents safely moving that unpublished implementation. Personal SSOT local maintenance exception.

## Issue tracking
- Bounded open issue/PR searches for resource cleanup returned none. Immediate local maintenance tracked here; no new public issue.
- Wiki: tooling repository explicitly excluded, repo-only.

## 계획
1. Add explicit session-bound process launcher and identity-checked cleanup with receipts.
2. Extend Docker cleanup with opt-in disposable removal, outcome records and retryable failures.
3. Test isolation, failure, process-only lifecycle and existing behavior; bootstrap and verify installation.

## 판단 근거
- Command-name or directory matching cannot establish process ownership.
- Removing arbitrary containers could destroy writable-layer data. Only an explicit disposable label permits removal, never volumes/images/global prune.
- Unknown legacy resources remain reported rather than guessed.

## ⚠️ DEVIATION
- Container deletion is opt-in via a disposable label because old writable layers may contain data. Unregistered legacy servers are not adopted.
- Existing asynchronous tests now wait for completion receipts; command dispatch is no longer the last observable operation.
- Read-only safety review identified uncertain process probes, orphan groups and Supabase identity races; all now fail closed with retained evidence.

## Verification
- Full sequential Node suite: 81 passed. Full Python suite: 96 passed.
- Actual helper/installed SessionEnd smoke: HTTP response verified, process group stopped, listening port closed, temporary log removed. No test server left running.
- Worker fixtures verify disposable removal, volume/bystander preservation, failed cleanup retention, label changes and replaced Supabase identity refusal. No real Docker data was removed in tests.
- Shared installation: 78 current entries; managed native hook trust: 10 enabled/trusted, zero managed review required. Existing unrelated trust entries unchanged.
- Skill validation: 25 passed. Public safety audit includes new files using an isolated temporary index, plus history. Original staged work preserved.
- Initial regression runs exposed test timing assumptions: after command dispatch, the worker now performs verification before consuming ownership. Tests wait for receipt/marker completion instead of racing the next scenario. One parallel run also reproduced the previously documented 300 ms lsof probe timeout; sequential execution used for required suite.
- User subsequently authorized publishing to the SSOT. Customer deployment remains outside scope.

## Limits / next work
- Existing unowned resources are not retroactively adopted, and unlabeled container data is preserved. A separate reviewed inventory is required before deleting old data.
- Commands that daemonize into another process session are outside the managed process group. A killed supervisor with remaining group members produces an orphaned result instead of unsafe blind termination.
- Docker Desktop CLI success is recorded as stop-requested, not verified VM exit.
