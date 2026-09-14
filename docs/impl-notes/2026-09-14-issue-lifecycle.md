# 2026-09-14 Issue lifecycle alignment

## 목표 / 확정 사항
Replace unconditional issue creation with existing-issue lookup, explicit work linkage and acceptance-based closeout. Keep small immediate tasks lightweight. Preserve raw wiki collection and inspect wiki presentation/context architecture separately without mutations.

## Gate evidence
- User approved the proposed issue workflow: find/reuse existing issues, create only when tracking is useful, link implementation and reconcile completion evidence before closing.
- Shared environment implementation, local application, commit/push and lifecycle handling for this scoped tracking issue are authorized. No bulk cleanup of customer backlogs is included.
- Wiki information architecture remains under discussion. No raw collector, wiki content, project-local files or registry changes are authorized by this implementation plan.

## Issue tracking
- Existing related open issues searched before creation; no match found.
- Primary issue: https://github.com/oyuns-wishket/ai-working/issues/11.
- Done when: shared global/dev-protocol entry and exit rules are updated, callers point to the same owner, checks and exact published CI pass, and local Claude/Codex source parity is verified.
- Delivery: public shared configuration and local application; no app deployment target.

## 계획
1. Put the compact lifecycle principle in global policy.
2. Add one conditional dev-protocol issue reference, invoke it before substantive implementation and at closeout, and add a small tracking record to implementation notes.
3. Pass issue acceptance scope to workers and retain linkage across project PR/deployment workflows without premature auto-closing.
4. Verify realistic lifecycle scenarios, references and repository checks, publish with a non-closing issue reference, then close this issue only after measured completion.

## 판단 근거
Use an isolated worktree. This is instruction-only work; visual design gates do not apply. Existing project registry resolution for ai-working is repo-only. Do not add issue polling hooks or turn a backlog into session-start context.

## 검증
- 25 skill/reference checks, public content/full-history audit, shell syntax and whitespace checks passed.
- Existing tests passed: 34 Node, 90 repository Python and 52 auxiliary skill tests. No app build target exists for this workflow-only change.
- Independent document-based review passed eight scenarios: no-issue typo, related issue/in-progress PR, tracker failure, partial completion, post-merge production verification, multiple workers, wiki skip, and develop/default-branch closing semantics. This is not a runtime model-behavior test.
- Publication intentionally uses a non-closing reference to the primary issue. Remote closure is performed only after published CI and local source checks satisfy the issue's acceptance criteria.

## ⚠️ DEVIATION
없음
