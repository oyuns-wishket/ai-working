# Rule discovery and precedence

## Goal

Resolve only the wiki connection and governing rules that the active project actually designates. Discovery is read-only until the user approves an exact write plan.

## Connection evidence

Accept a wiki candidate only when a project-scoped instruction explicitly connects it. Valid evidence includes:

- a concrete path in project `AGENTS.md`, `CLAUDE.md`, or a designated rule;
- an environment variable named by that instruction, with a currently resolved path;
- a project-local config or mapping file explicitly named by that instruction;
- a project note path inside a vault explicitly named by that instruction.
- a project-owned or machine-local registry matching the project's credential-free canonical Git remote to one `connected` namespace.

The registry is project-scoped connection evidence because the exact remote identity is the key. A local folder-name-only match is not sufficient when the repository has a remote. Registry evidence authorizes discovery only; it never authorizes a wiki write or publish.

Do not treat these as a connection by themselves:

- a generic `WIKI_PATH` or `OBSIDIAN_VAULT_PATH` that no project rule mentions;
- a nearby folder named `wiki`;
- a global fallback such as `~/wiki`;
- a wiki found by broad home-directory search;
- a stale path mentioned only in chat without project evidence.
- a registry entry classified `common-only`, `archived`, or `excluded`.

If a worktree path differs from its source checkout, keep the worktree as code evidence but normalize the project identity using Git remote, common directory, and project rules. Do not create duplicate wiki pages for each worktree.

## Governing rule sources

For the selected target, build the rule set from:

1. user instructions in the current conversation;
2. the most local scoped project and wiki rules;
3. `AGENTS.md` and `CLAUDE.md` from the applicable root to the target;
4. `.claude/rules/**`, `.agents/rules/**`, `.codex/rules/**`, or another rule directory explicitly named by a governing file;
5. root `README*`, `SCHEMA*`, `GOVERNANCE*`, `CONTRIBUTING*`;
6. ingest, compile, maintenance, runbook, source-authority, contradiction, index, and validation documents explicitly designated as rules;
7. files and scripts that the governing documents explicitly require.

Follow explicit rule references until no new governing file is found. Resolve relative paths from the file that names them. A referenced file outside the target root may be read only when the governing document explicitly names it.

Ordinary content links, backlinks, related-note lists, and `[[wikilinks]]` are knowledge navigation, not rules. Do not recursively load them as instructions.

## Precedence

Apply instructions in this order:

1. current user instruction;
2. more local target-scoped rule;
3. target root rule;
4. project rule that defines the connection;
5. `knowns` defaults.

Higher priority cannot silently authorize a write that a lower-level target governance marks as forbidden or approval-only. Surface the conflict and ask the user for a decision that is valid under the target governance.

## Bounded reading

- Read indexes and candidate-related notes before raw sources.
- Search by task concepts, file paths, issue number, domain terms, and current Git SHA.
- Do not scan an entire vault or `raw/` tree without a governing rule that requires it.
- Record every rule file used in the final write plan so the user can verify the interpretation.

## V2 canonical write discovery

When the owning wiki provides `.system/knowledge-contract.json`, resolve the registry `canonical_write_target` separately from all read scopes. Read the owner schema/template and validator instead of copying a canonical template into this skill. A common-only read or an exact my-wiki binding is not a closeout target. V2 writes stay within the registered sys-wiki target, including after symlink resolution; never fall back to Mode B for a user-owned note. V2 discovery reads explicit governing files and does not recursively scan canonical, candidate or manual content for rules.

### First durable note for a common-only project

A remote-matched managed work project may produce a `registry-connection-proposal` with a suggested project namespace whose business categories come from the owning contract. This is not a write grant. Run the owner `connect_project_wiki.py` in dry-run mode; include its exact registry/index paths, proposed topic path and the helper-returned connection review hash (`registry_sha256`; do not recompute it from only the registry file) in the same knowns approval batch. After that existing approval, apply with `--expected-registry-sha256`, rediscover the now-connected canonical target, ingest and validate/publish the complete approved set. Do not create directories for all registry entries in advance. The connector does not modify the customer code repo or grant new raw-source permissions. Existing customer namespace collisions require explicit ownership resolution.
