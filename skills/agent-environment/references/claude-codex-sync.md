# Claude × Codex shared environment

## Canonical layout

| Concern | Canonical source | Claude resolution | Codex resolution |
|---|---|---|---|
| Personal global policy | `global/CLAUDE.md` | marker-managed import in `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` symlink |
| Reusable workflow | `skills/<name>/SKILL.md` | `~/.claude/skills/<name>` per-skill symlink | `~/.agents/skills/<name>` per-skill symlink to the same source |
| Workspace/repo guidance | repository `AGENTS.md` / `CLAUDE.md` | native `CLAUDE.md` loading | native `AGENTS.md`; Codex fallback recognizes `CLAUDE.md` where configured |
| Hooks, permissions, credentials | local machine configuration | Claude-specific | Codex-specific |

`global/CLAUDE.md` is the policy SSOT. Write it in tool-neutral language. Do not fork it into a Codex-only document. A same-machine edit is visible to both agents immediately through the links.

## Cross-Mac routine

On the machine where the source changed:

1. Inspect the repo diff and test it.
2. Commit and push the changed public `ai-working` repo according to the current authorization.

On the other Mac:

```bash
"$AI_WORKING_ROOT/bootstrap.sh" --status
"$AI_WORKING_ROOT/bootstrap.sh" --pull
"$AI_WORKING_ROOT/bootstrap.sh" --status
```

Resolve `AI_WORKING_ROOT` from the installed skill symlink or the current checkout before running these commands. Never infer it from another person's username.

`--pull` fast-forwards first, then applies the manifest idempotently. It backs up a replaced local real file under `~/.claude/backups/consortium-*`; it must not be used as a substitute for inspecting a dirty Git worktree.

## What bootstrap restores

- Claude's marker-managed global-rule import.
- Codex `~/.codex/AGENTS.md` → `global/CLAUDE.md`.
- Every source skill individually linked into `~/.claude/skills/` and `~/.agents/skills/`. `link_skill` never touches a destination that resolves to the same physical path as the source.
- Workspace guidance declared in `manifest.json`.
- Claude governance hooks.

## Machine-local integrations

MCP registrations, account tokens, trust levels, TCC permissions, and provider-specific settings stay on each machine. Keep only their reusable setup procedure in `ai-working`; store live values in the provider's credential store or an ignored local config. Verify an integration with a real read-only tool call after installing it.

## Change rules

- Edit source skills and source rules in this repo. Both agents resolve the same file; platform-specific tool names are interpreted per the global platform-translation rule, not forked into adapters.
- A new skill under `skills/` becomes discoverable by both agents on every Mac after `bootstrap.sh` — no per-skill registration.
- Never put tokens, `~/.claude.json`, Keychain contents, `cswap` account exports, or machine-only launchd/TCC state in this repo.
- A hook may enforce a rule on one platform; the rule itself remains global policy. Do not claim a hook is shared merely because the intent is shared.
