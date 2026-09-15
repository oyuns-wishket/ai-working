# Shared skill ownership

Skills are task entrypoints, not a second global policy layer. Keep one owner for each workflow, and load its supporting references only when that mode is needed. Claude's native import wrapper and Codex's symlink both resolve `global/CLAUDE.md`; neither depends on OMC.

## Consolidated entrypoints

| Previous entrypoint | Current owner / preserved capability |
|---|---|
| claude-setup, sync-consortium | agent-environment: install, synchronize, diagnose and verify both platforms |
| brainstorming, writing-plans, executing-plans | dev-protocol: clarify actual unknowns, plan by scope and execute authorized work |
| using-git-worktrees, finishing-a-development-branch | dev-protocol: isolated work, project branch workflow, authorization and safe cleanup |
| test-driven-development, verification-before-completion, requesting-code-review | dev-protocol and its verification-review reference: meaningful regression tests, direct evidence and appropriately scoped review |
| subagent-driven-development, multi-agent-dev | multi-session-dev: lane contracts, in-process read-only subagents, isolated Claude/Codex write sessions per worktree, sequential integration and review |
| writing-skills | ssotify: create, improve, consolidate and validate shared skills |
| external systematic-debugging | public systematic-debugging: evidence-driven diagnosis, safe instrumentation and regression verification |
| wiki-curator | knowns: bounded duplicate/conflict review during an authorized closeout; project-wiki-context: read and health diagnostics |

Former entrypoints are removed from the curated home catalog, not retained as duplicate discoverable aliases. Old names in natural-language requests are resolved to their current owner; a removed slash command itself is not guaranteed to remain available. Original third-party skill directories are preserved for existing sessions and reference. This is a curated local workflow, not an in-place vendor upgrade.

Generic plans, tests and reviews do not each start a separate approval process. Follow the current user scope and `dev-protocol`; ask only when a material unresolved choice or new scope actually needs it. Meaningful new or risky work still gets appropriate planning and verification.

## Capabilities kept separate

- `gen-spec` includes an ERP SSOT/delta pipeline, while `generate-spec` handles general specifications. Similar output names do not establish interchangeable procedures.
- `agent-bot-setup` uses customer/project-owned runtime boundaries; `hermes-bot-setup` handles a personal assistant. Preserve their account ownership distinction.
- `remote-setup`, `remote-ssh-edit` and `mac-file-sync` solve different desktop, editing and file-transfer tasks.
- `feature-flow` owns project branch/preview mechanics; `dev-protocol` owns the work and approval lifecycle. `paseo-setup` configures a separate worktree tool only when requested.
- The project wiki workflow uses `project-wiki-context` for bounded reads and health diagnostics, and `knowns` for development closeout with duplicate/conflict review. Scheduled source ingestion belongs to the knowledge repository's pipeline and policy, not a third skill or an interactive closeout call per item. The separate `knowledge-wiki` integration keeps its adapter-specific scope.
- Team skills retain their original source and configuration. System skills bundled by a provider keep provider ownership.

Low recent explicit invocation is insufficient reason to remove these capabilities. Setup tasks may be infrequent, and reading a skill through file tools or executing its scripts directly is not counted as a native Skill invocation.

## Applying the curated catalog

Bootstrap installs the public skills and removes only stale links it recognizes as old ai-working-owned skills. It does not retire third-party sources just because they disappeared from a local asset registry.

For selected external workflow retirement on a machine:

1. Inventory both home catalogs and the local external-assets registry. Compare exact resolved source directories, including supporting files. Check whether a provider plugin independently exposes a duplicate skill.
2. Back up the registry and each selected symlink outside discovery directories. Verify the link still resolves to the reviewed source before moving it. Preserve unrelated sources, real directories and local customizations; report conflicts.
3. Remove only the reviewed source entries from the local registry. Apply public bootstrap from the canonical checkout, then run `sync_agent_assets.py` dry-run/apply/check against that local registry.
4. Verify both catalogs resolve each retained skill to the same whole source, retired entries are absent, the global policy resolution is unchanged and bootstrap reports no drift. A fresh session may be needed to discard instructions already invoked in an existing conversation.

Local plugin choices and registry paths do not travel in public Git. Another Mac needs its own reviewed retirement of external links; Git pull plus bootstrap handles only the public source portion. No customer/project directories are scanned or edited as part of this home operation.

## Evidence and current authoring guidance

Keep utilization aggregates and absolute local paths in private machine state. Compare explicit invocations separately from file reads and automatic hook activity. Skill counts and character counts describe the catalog, not token bills, runtime latency or money saved.

Current guidance supports concise descriptions with clear boundaries and conditional references. Both platforms load discovery metadata before selected skill bodies: [OpenAI skill guidance](https://learn.chatgpt.com/docs/build-skills), [Claude skill guidance](https://code.claude.com/docs/en/skills). Runtime catalogs can shorten or omit descriptions, so place the primary use case first.
