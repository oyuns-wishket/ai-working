---
name: systematic-debugging
description: Diagnose unexplained failures, flaky tests, regressions, and integration errors using reproducible evidence before changing code. Use when the cause is uncertain or a previous fix failed.
---

# Systematic debugging

Resolve the cause with the smallest useful experiment. For an obvious error with a demonstrated cause, verify the direct correction without adding a diagnostic ceremony. Implementation and deployment authorization remain governed by `dev-protocol`.

## Establish the failure

Read the exact error and relevant stack frames, expected versus actual behavior, environment/version and recent diff. Reproduce with a minimal input when safe. If production reproduction could mutate data, use existing redacted observations or a safe fixture. Record uncertainty when reproduction is unavailable.

Compare a working and failing case. Trace the bad value or state backward through its callers to the first incorrect boundary. In a multi-component flow, inspect inputs, outputs and configuration presence at the relevant boundaries; narrow the failing component before changing unrelated layers.

Diagnostics must not dump environment variables, tokens, headers, payloads or account identifiers. When testing configuration propagation, emit only an allowlisted variable's boolean presence, type or redacted shape. Never interpolate the variable's actual value into a presence check.

## Test one explanation

State a hypothesis and the observation that would disprove it. Change one relevant factor, run the smallest test, and compare the result. Preserve failed-experiment evidence instead of piling speculative fixes together. If repeated attempts contradict the hypothesis, reassess the boundary or architecture before another patch.

For intermittent behavior, capture ordering and state transitions with bounded instrumentation. Wait on an observable readiness condition with a deadline; arbitrary delays hide the cause. Remove temporary instrumentation after diagnosis unless it is an intentional maintainable improvement.

## Fix and verify

Correct the earliest responsible source while preserving necessary downstream validation. Add a meaningful regression test when possible; confirm it exposes the original failure and passes with the fix. Run affected integration checks and the repository's required final checks. See [verification and review](../dev-protocol/references/verification-review.md) when selecting evidence.

Report the demonstrated cause, the correction, what passed and what remains uncertain. Diagnostic confidence does not authorize a new production mutation or a broader rewrite.
