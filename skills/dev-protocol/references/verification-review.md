# Verification and review

Read this when choosing tests or reviewing an implementation. Approval, implementation notes, deployment and cleanup remain owned by `dev-protocol`; this reference adds no approval gate.

## Choose evidence for the change

- Follow the repository's required checks and package manager. A relevant existing test may be enough; do not create a test that merely repeats wording or internal implementation.
- For new behavior or a reproducible bug, write a focused behavioral regression test when it provides useful protection. Run it before the fix and confirm it fails for the intended reason, then implement the smallest correction and run it again. If behavior is already correct, investigate the assumption rather than forcing a failure.
- Reversible prose/configuration changes can use schema, syntax, link, dry-run and runtime inspection instead of a new test. Preserve user work; never delete an implementation just because a test was written later.
- Use realistic inputs and check observable output, state, permissions and errors. Avoid mocks that replace the behavior under test. Isolate credentials, databases and external side effects.
- For flaky asynchronous behavior, observe the actual readiness condition with a bounded timeout; do not make arbitrary sleep increases the fix.

## Review scope and correctness

Compare the raw diff with the actual request and project rules: missing requirements, unintended changes, failure paths, permission/data boundaries, consumer compatibility and test coverage. Inspect referenced code when needed; judge findings by evidence and impact.

For substantial or risky work, use an independent native reviewer when available and authorized. Give the reviewer the raw artifacts, acceptance criteria and an explicit no-edit scope. Existing project reviewer roles take precedence; no plugin agent name is required. For a small bounded change, a direct diff review is enough.

Fix material findings, rerun the checks affected by the fix, and report unresolved limitations. Do not commission repeated reviews or expand test scope after passing checks without a new change, failure or concrete concern.

## Completion evidence

Run the required build/lint/test commands on the final integrated tree and inspect exit status and results. A worker summary, planned command or previous commit's passing checks is not evidence for the new result. Distinguish passed, failed, unavailable and not applicable.

Report what changed, why, the measured verification and remaining limitations. Continue the existing authorized commit/PR/deployment path. If deployment is authorized, verify the actual environment and follow `dev-protocol` closeout in the same turn.
