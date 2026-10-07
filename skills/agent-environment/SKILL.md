---
name: agent-environment
description: Set up a new Mac or Mac mini like an existing Mac with Paseo, Claude/Codex, work tools, shared rules/skills/hooks, remote access and runtime verification. Also sync or diagnose an existing environment and cswap accounts. Includes former claude-setup and sync-consortium requests.
---

# Agent environment

The public `ai-working` checkout owns shared policy and workflows. Resolve `AI_WORKING_ROOT` from the current checkout or installed skill symlink. Credentials, account choices, permissions and plugin selections stay machine-local.

## Choose the operation

- **New Mac / match an existing Mac:** requests such as “agent-environment로 새 Mac mini를 기존 Mac mini처럼 세팅해줘” activate the complete [new-machine setup](references/new-machine-setup.md). This single entrypoint owns discovery, tool installation, shared environment, project preparation, remote setup and runtime verification; invoke the relevant owner skills yourself without requiring the user to name them or paste a longer prompt. A status/sync-only request does not activate machine migration.
- **Install AI work tools:** default to Paseo (https://paseo.sh) as the work app and follow its current official installation instructions. Install/connect Claude Code or Codex as needed agent backends. Honor an explicit user choice of another tool. Use `paseo-setup` for project-specific worktree configuration, and bootstrap below for shared rules/skills.
- **Install, sync or repair:** read [shared environment](references/claude-codex-sync.md). Inspect the checkout status and `bootstrap.sh --status`, then dry-run the needed update. Use `--pull` only when source updates are needed and the checkout can fast-forward safely. Apply from the canonical checkout, not a temporary task worktree. Inspect the real diff before replacing local customizations.
- **Change global policy or a skill:** edit `global/CLAUDE.md` or `skills/<name>/` in this repository, validate, then run bootstrap. Use `ssotify` for substantial skill authoring/consolidation. Never make an agent-home copy the new source.
- **Claude account switching:** read [cswap](references/cswap.md). Never print or export account tokens, Keychain contents or `cswap export` output.
- **Hook or context efficiency:** read [hook behavior](../../docs/hook-behavior.md); run `node scripts/check_environment.mjs --project <path> --json`. For measured task comparisons use [task metrics](../../docs/task-metrics.md). Installation parity does not prove runtime behavior; cache-hit rate is not money saved.
- **External assets or retired workflows:** read [shared assets](../../docs/agent-assets.md) and [skill ownership](../../docs/skill-consolidation.md). Review selected sources and conflicts before applying the local registry. Project adapters are a separate scope; never fan out across projects without a request.

## Complete the selected setup

Environment setup includes installing, connecting and verifying the tools required for the user's selected work. Do not stop at a prerequisite list or bootstrap links. Inspect existing installations, reuse compatible versions and prior authorization, and perform terminal steps directly. Read the matching skill before executing its procedure:

| Selected work | Installation and configuration owner |
|---|---|
| Base AI environment | Paseo, selected Claude Code/Codex backends, Git, Node.js, Python 3, jq and standard shell tools; bootstrap shared rules/skills/hooks |
| Project workspaces | [`paseo-setup`](../paseo-setup/SKILL.md): Paseo CLI when used and project-specific setup/services |
| Development, PRs and deployment | [`dev-protocol`](../dev-protocol/SKILL.md), [`feature-flow`](../feature-flow/SKILL.md), [`customer-infra-ops`](../customer-infra-ops/SKILL.md): package manager, GitHub CLI, Supabase/Vercel CLI and Docker as required by the actual project |
| UI and browser verification | [`design-workflow`](../design-workflow/SKILL.md), [`dev-review-deck`](../dev-review-deck/SKILL.md): Playwright and required browser; scoped Anime.js/Motion/Bklit/Three.js dependencies, optional Taste/Impeccable and asset-production tools according to the selected design path |
| Multiple Macs and remote desktop | [`remote-setup`](../remote-setup/SKILL.md): selected private network and remote-desktop apps, host power/display/input and optional clipboard transfer |
| Remote project editing | [`remote-ssh-edit`](../remote-ssh-edit/SKILL.md): SSH, VS Code and Remote-SSH extension |
| Mac file transfer/sync | [`mac-file-sync`](../mac-file-sync/SKILL.md): Tailscale, Taildrop and SSH/rsync |
| Multiple Claude accounts | [cswap](references/cswap.md): `claude-swap` utility and selected local account setup |
| Personal or organization bot | [`hermes-bot-setup`](../hermes-bot-setup/SKILL.md) or [`agent-bot-setup`](../agent-bot-setup/SKILL.md): selected bot runtime and integrations |

App libraries belong in the actual project and follow its package manager, lockfile, compatibility and design gates. Unselected services and unused libraries are not installation targets. A single-Mac setup must work without remote tools.

For multiple Macs, discover the current and remote device roles, reachable hosts and existing configuration. Apply selected procedures on both relevant ends, and synchronize the canonical AI environment through authorized Git commit/push and remote pull/bootstrap. Verify each device and the real connection independently; an unreachable device remains explicitly unverified. Reuse prior choices; clarify only unresolved device/product decisions or expanded scope. Hand off only login, license activation and GUI/OS permissions that cannot be automated, with exact instructions. Keep host identities and credentials machine-local.

## Verify shared rules and skills

- Claude `~/.claude/CLAUDE.md` has a marker-managed native import of `global/CLAUDE.md`; unrelated wrapper content is preserved.
- Codex `~/.codex/AGENTS.md` links to that same file. Removing OMC does not require removing Claude's native import wrapper.
- Both home skill directories resolve each shared skill to the same whole source directory, including references/scripts.
- Run `bootstrap.sh --status`. For changed hooks, verify native trust and lifecycle behavior as described in the shared-environment reference. Never claim an existing session has reloaded based only on filesystem checks.

## Optional orchestration removal

Compare recent explicit workflow use with automatic hook activity. Keep aggregates private and preserve required capabilities before removal. Use native uninstall with persistent-data preservation; replace a plugin-dependent statusline first. Do not kill existing sessions or delete project memory/wiki folders.

The local runtime profile supports `omc_mode: "removed"` and `native_statusline: true`. These configure adapters without making OMC a dependency. Inspect native discovery afterward and report any existing-session processes that remain.
