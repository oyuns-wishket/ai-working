# 2026-09-14 OMC utilization and native workflow dependency audit

## Gate evidence
- User authorized commit, push and deployment of verified environment changes.
- User subsequently requested an evidence-based OMC necessity/utilization check, removal if unnecessary, and shared development-environment improvements.
- Project-local Markdown, rules, skills and agents are explicitly excluded; user will maintain them during project work.
- Current work uses an isolated worktree. Existing memory/wiki/history and credentials must be preserved.

## Plan
- Verify the published shared-environment CI and fix concrete portability failures.
- Measure recent explicit OMC usage separately from automatically loaded hooks.
- Inspect active plugin, statusline and CLI dependencies; retain necessary behavior through shared native workflows before removing any integration.
- Review, test, apply and publish the justified changes; verify native readiness and CI.

## Initial verification finding
- The first public-safety run on the shared-environment commit failed the quoted SQL regression on Linux: Node provides stdin as a descriptor that cannot be reopened through /dev/stdin. Reading the existing standard input directly with cat preserves the payload on both platforms. The existing regression covers the behavior; no DB command is executed.

## Remaining evidence
- OMC utilization and dependency audits are in progress. No OMC runtime removal is authorized by an invented usage result.
