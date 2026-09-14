---
name: agent-environment
description: Set up, sync, or diagnose the shared Claude/Codex environment, global rules, hooks, skills, and cswap accounts across Macs. Includes former claude-setup and sync-consortium requests.
---

# Agent environment

The public `ai-working` checkout owns shared policy and workflows. Resolve `AI_WORKING_ROOT` from the current checkout or installed skill symlink. Credentials, account choices, permissions and plugin selections stay machine-local.

## Choose the operation

- **Install, sync or repair:** read [shared environment](references/claude-codex-sync.md). Inspect the checkout status and `bootstrap.sh --status`, then dry-run the needed update. Use `--pull` only when source updates are needed and the checkout can fast-forward safely. Apply from the canonical checkout, not a temporary task worktree. Inspect the real diff before replacing local customizations.
- **Change global policy or a skill:** edit `global/CLAUDE.md` or `skills/<name>/` in this repository, validate, then run bootstrap. Use `ssotify` for substantial skill authoring/consolidation. Never make an agent-home copy the new source.
- **Claude account switching:** read [cswap](references/cswap.md). Never print or export account tokens, Keychain contents or `cswap export` output.
- **Hook or context efficiency:** read [hook behavior](../../docs/hook-behavior.md); run `node scripts/check_environment.mjs --project <path> --json`. For measured task comparisons use [task metrics](../../docs/task-metrics.md). Installation parity does not prove runtime behavior; cache-hit rate is not money saved.
- **External assets or retired workflows:** read [shared assets](../../docs/agent-assets.md) and [skill ownership](../../docs/skill-consolidation.md). Review selected sources and conflicts before applying the local registry. Project adapters are a separate scope; never fan out across projects without a request.

## Verify the actual resolution

- Claude `~/.claude/CLAUDE.md` has a marker-managed native import of `global/CLAUDE.md`; unrelated wrapper content is preserved.
- Codex `~/.codex/AGENTS.md` links to that same file. Removing OMC does not require removing Claude's native import wrapper.
- Both home skill directories resolve each shared skill to the same whole source directory, including references/scripts.
- Run `bootstrap.sh --status`. For changed hooks, verify native trust and lifecycle behavior as described in the shared-environment reference. Never claim an existing session has reloaded based only on filesystem checks.

## Optional orchestration removal

Compare recent explicit workflow use with automatic hook activity. Keep aggregates private and preserve required capabilities before removal. Use native uninstall with persistent-data preservation; replace a plugin-dependent statusline first. Do not kill existing sessions or delete project memory/wiki folders.

The local runtime profile supports `omc_mode: "removed"` and `native_statusline: true`. These configure adapters without making OMC a dependency. Inspect native discovery afterward and report any existing-session processes that remain.
