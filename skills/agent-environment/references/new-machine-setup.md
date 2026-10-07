# New Mac setup from an existing Mac

## One-call contract

The user can say:

> agent-environment로 새 Mac mini를 기존 Mac mini처럼 세팅해줘.

Treat this as an instruction to complete the workflow below, including the tools and remote capabilities actually used on the baseline Mac. Reuse choices and authorization from the current conversation. The user does not need to list every dependency or invoke each subordinate skill. A bare skill name without setup intent follows the surrounding conversation; clarify the operation only if it is ambiguous.

For the same user's additional device, keep the existing ai-working repository as the canonical source. Do not create a fork or second personal policy. A genuinely different user's personalization belongs to `personal-ai-ssot` instead.

If skills are not yet registered, read this repository's `skills/agent-environment/SKILL.md` directly. Locate an existing checkout or use the repository identified by the user/current source. Inspect its Git status and remote before updating; safely fast-forward the default branch when appropriate. Discover the checkout and workspace locations from current configuration and user preferences. Ask once if there is no established location before cloning. Never copy another machine's absolute home paths blindly.

## Plan and execute

Create a short checklist covering discovery, installation, shared configuration, projects, remote access and verification. Keep discovered device identities, paths, application inventories and progress in machine-local configuration, outside public Git. Resume from verified progress rather than repeating completed setup.

1. **Discover the target and baseline.** Inspect OS, CPU, shell, user, installed tools/versions, current agent configuration, workspace paths and reachable authorized hosts. Identify which existing Mac is the baseline; ask only if it cannot be resolved. Inspect it read-only over an authorized connection, reporting non-secret settings only. Inventory actual AI apps/backends, external skills/plugins/MCPs, package managers, projects, remote products and relevant running services. Separate canonical policy from machine-local runtime settings and deprecated workflows. If the baseline is unreachable, continue independent target setup and mark parity unverified.

2. **Install the work tools.** Use Paseo as the default work app. Install/connect Claude Code and Codex when selected or used on the baseline. Prepare Git, Node.js, Python 3, jq, standard shell tools, Paseo CLI and GitHub CLI for the corresponding workflows. Install package managers, Supabase/Vercel CLI, Docker, Playwright and required browsers when the baseline's actual work or selected projects require them. Inspect compatible existing installations and supported official distribution paths; account for OS/CPU differences. Record reasons for version differences rather than silently introducing major upgrades. Do terminal work directly.

3. **Connect the canonical AI environment.** Read [shared environment](claude-codex-sync.md), current README, bootstrap and manifest before applying. Inspect target paths and workspace entries against this Mac's intended layout. Use supported machine-local configuration for device-specific values. If a canonical implementation change is necessary, retain portability and follow `ssotify` and the user's publication scope. Review dry-run, apply from the canonical checkout and verify status. Check Claude imports, Codex instructions, whole-directory skill links, hook manifests and native hook trust. Preserve unrelated settings and existing user content.

4. **Restore selected local integrations.** Read the shared-assets procedure for explicitly selected external skills/agents and reinstall plugins from their actual sources where supported. Verify provider discovery and each selected MCP with a real read-only call. Use the cswap reference for multiple Claude accounts and `hermes-bot-setup` or `agent-bot-setup` for a selected bot. Recreate device-local settings through supported configuration and fresh authentication. Never clone the whole agent home, vendor cache, Keychain, OAuth exports, private keys, conversation history or customer data as a shortcut. Existing bot instances/schedules must remain intact; matching the baseline does not authorize a duplicate live bot, external sends or production deployment. Clarify service placement only when that affects execution.

5. **Prepare selected projects.** Find the user's intended projects from established workspace configuration and baseline evidence; do not scan or copy unrelated customer repositories. Clone/sync authorized projects while preserving dirty and unmerged work. Read each project's current rules. Use `paseo-setup` for project workspace/services, the project's package manager and lockfile for dependencies, and its approved env sources. Use `design-workflow` for the UI libraries, design helper skills and asset-production tools actually needed by the project, honoring its design gates. Missing project or backend access is a scoped blocker, not a reason to invent credentials or claim readiness.

6. **Configure the remote workflow.** Resolve baseline/target host and viewer roles and reuse the chosen products. Read and execute `remote-setup` for private network, remote desktop, selected host power/restart, display, Korean/English input and clipboard behavior; `remote-ssh-edit` for SSH, VS Code and Remote-SSH; and `mac-file-sync` for Tailscale/Taildrop and SSH/rsync. Inspect both relevant ends and preserve existing sessions/services. Do not enable automatic login, weaken locking, force reboot or alter baseline services merely to match a snapshot. Follow the owner skill's explicit decision boundaries. Synchronize shared AI policy through authorized Git publication and the other Mac's pull/bootstrap, never through a parallel source copy.

7. **Prove runtime readiness.** Use the verification matrix below. Installation and symlink presence alone do not prove identical operation. Record command/action, device, observed result and any untested condition. Hand off only login, passwords, license activation and GUI/OS permissions that cannot be automated, with the exact required action. Continue independent work while waiting and resume the dependent verification afterward.

## Verification and completion

| Capability | Evidence |
|---|---|
| Paseo and agent backends | Start a harmless agent session through Paseo; verify each selected backend actually responds |
| Shared policy and skills | Bootstrap status; native Claude/Codex instruction and skill recognition in a new session |
| Hooks | Native registration/trust and relevant harmless or blocked-fixture behavior; do not test with a live destructive action |
| Projects | Dependency preparation, available build/lint/tests and actual development-server/service response in the selected projects |
| Remote access | Authorized network reachability, remote-desktop connection/resolution/input, SSH and real remote editing where selected |
| File/clipboard transfer | Selected transfer actually received, with file size/hash or clipboard behavior checked |
| Local integrations | Selected MCP read call and service health; bot identity/allowlist and existing-instance placement verified |
| Restart behavior | Inspect service registration/restart policy and safely test reconnection; defer a disruptive restart until authorized and report it as untested |
| Baseline comparison | Explicit differences with reasons and device-by-device verified/unverified status |

Finish with installed/configured capabilities, baseline differences, verification results, remaining user actions and scoped blockers. Report completion only for capabilities actually verified. Do not claim that an existing session reloaded based solely on changed files. Clean up only temporary resources owned by this setup and preserve persistent data.
