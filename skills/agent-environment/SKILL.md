---
name: agent-environment
description: Use when the user asks to set up, sync, diagnose, or update the shared Claude Code and Codex environment across Macs, global rules, hooks, skills, AGENTS.md/CLAUDE.md, or Claude account switching with cswap. Triggers on "에이전트 환경", "Claude Codex 동기화", "공통 규칙", "bootstrap", "cswap", "클로드 계정 전환", "다른 맥 세팅", or "글로벌 룰".
---

# Agent environment — Claude × Codex

Use the public `ai-working` checkout as the only version-controlled AI environment SSOT. Resolve its location from the installed skill link or current checkout and call it `$AI_WORKING_ROOT`; do not assume a particular username or parent directory. Provider credentials, TCC permissions, and other secrets remain machine-local configuration rather than a second policy or skill source.

## Choose the operation

1. **Check or sync another Mac:** read `references/claude-codex-sync.md`, run `bootstrap.sh --status` first, then `bootstrap.sh --pull` only when needed. Report each resolved link.
2. **Change a shared global rule or workflow:** edit only the canonical source under `ai-working/`. Never edit `~/.claude`, `~/.codex`, or an adapter copy as the source. Validate with `ai-working/bootstrap.sh --status`, then commit and push according to the current authorization.
3. **Use or repair Claude account switching:** read `references/cswap.md`. Never print, commit, export, or paste OAuth tokens, API keys, Keychain data, or `cswap export` output.
4. **Add a cross-agent skill:** author it at `ai-working/skills/<name>/` and run `ai-working/bootstrap.sh` to expose it to Claude and Codex. Keep secrets and customer-confidential values out of the skill; use documented environment variables or ignored local config for runtime values. Write `SKILL.md` agent-neutral and interpret platform-specific tool names through the global platform-translation rule.

## Invariants

- Claude global policy imports `global/CLAUDE.md`; Codex global guidance links to that exact file.
- Both agents read the same public source skills through links. Skills are authored under the `ai-working` root, never directly in an agent home.
- Hooks, Keychain/TCC permissions, account credentials, and provider-only commands remain machine-local. Their policy intent belongs in the source only when it applies to both agents.
- Before claiming the environment is synced, verify all `manifest.json` links and imports with `bootstrap.sh --status`.
