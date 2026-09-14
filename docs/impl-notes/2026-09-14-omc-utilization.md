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

## Decision evidence
- A bounded recent-use audit deduplicated tool-call IDs and separated explicit skill/worker calls from automatic hook attachments. OMC workflow use was sparse; most activity came from automatically invoked hook programs. Exact personal usage counts and coverage stay machine-local rather than in public source.
- Existing shared workflows and native workers cover the observed general review/implementation roles. Specialized LSP capability is an explicit optional loss; no equivalence or monetary/time saving is claimed.
- Native Claude subagent and statusline contracts were verified against current official documentation and installed payloads. No model calls were needed.
- Other actually used debugging/planning skills are preserved as individually shared sources with their companion workflows, without a forced startup hook.

## Implementation
- Native worker contracts replace hardcoded OMC role names in shared guidance. Project-local workers and rules remain unchanged by explicit user choice.
- Lightweight statusline reads only native model/project/context fields. No network, subprocess, cache or credential reads.
- Local retired-plugin profile preserves unrelated settings and makes bootstrap repeatable. Native uninstall preserves persistent data and leaves existing sessions under their original ownership.
- Independent review and regression verification passed: Node 34 tests, Python repository 90 tests, skill validation 26, public audit and syntax checks. Prior required auxiliary skill suites also passed unchanged.
- Native OMC plugin uninstall used persistent-data preservation; the unused global CLI package was removed with lifecycle scripts disabled. Existing-session cache entry bytes were unchanged, and no running process was terminated.
- Local installation verified: 74 bootstrap checks, repeat dry-run with no changes, 44 shared skill sources / 88 matching links, and zero managed or external native hook trust warnings.
- Native statusline smoke output confirmed model/project/context information. The plugin is absent from native discovery and its CLI command entrypoints are absent.
- Existing project-local instructions, agents, rules, skills, memory and wiki content were not modified. New sessions are needed to reload the catalog and omit old session-bound MCP processes.
- Publish the reviewed shared changes and verify the exact revision's public-safety CI. There is no separate application deployment pipeline in this configuration repository.
