# Shared agent assets

`python3 scripts/sync_agent_assets.py` synchronizes one explicitly selected home or project. It does not discover
customer repositories, scan memory or caches, install plugins, change credentials, or publish files. Python 3.9 or
newer is sufficient; no third-party dependencies are required.

Global personal policy and public skills remain owned by `bootstrap.sh` and the ai-working canonical sources. This
helper handles explicit external assets and project adapters. Hook lifecycle translation is a separate concern.
A successful filesystem check establishes asset installation, not proof that an already-running agent has reloaded it.

## Commands

```sh
python3 scripts/sync_agent_assets.py --home "$HOME" --config "$ASSET_CONFIG" --json
python3 scripts/sync_agent_assets.py --home "$HOME" --config "$ASSET_CONFIG" --apply --json
python3 scripts/sync_agent_assets.py --home "$HOME" --config "$ASSET_CONFIG" --check --json
python3 scripts/sync_agent_assets.py --project "$PROJECT_ROOT" --check --json
```

Dry-run is the default. `--apply` performs reviewed, supported changes; it can apply safe entries while reporting
unresolved conflicts. `--check` is read-only and returns nonzero for proposed changes, conflicts, or unsupported assets.
Every mode emits JSON. Exit code 1 means unresolved assets/drift; 2 means invalid input or an execution error.
The report uses paths relative to the selected scope and never prints source file contents or credentials.

Keep the optional config machine-local, outside public Git:

```json
{
  "schema_version": 1,
  "skill_sources": [
    {"name": "example-skill", "path": "/absolute/local/source/example-skill"}
  ],
  "agent_sources": [
    {"name": "example-reviewer", "path": "/absolute/local/source/example-reviewer.md"}
  ],
  "model_map": {"source-model-tier": "explicit-target-model"}
}
```

`skill_sources` and `agent_sources` name existing, explicitly selected sources, including plugin-provided assets.
The synchronizer does not copy those source repositories into ai-working. Native model names are not interchangeable:
non-`inherit` Claude models require an explicit `model_map` entry before generating a Codex adapter. A target value
of `"inherit"` omits the native model field and uses the platform default; it is never emitted as a model identifier.

## What is synchronized

- **Skills:** the existing `.claude/skills` and `.agents/skills` directories are examined one level deep. A missing
  counterpart becomes a symlink to the same entire source directory, including scripts and references. Different
  physical sources are conflicts even when `SKILL.md` matches, because support files may differ. Project links refer to the existing in-project entry using a relative path, preserving any source symlink
  indirection. Explicit external project sources require a project-local indirection; machine-specific source paths
  are not written into project links. Existing destinations
  are preserved. Explicit configured sources select the intended canonical directory.
- **Project instructions:** original root `AGENTS.md` and `CLAUDE.md` bodies remain in place. A managed, plain-text
  reference block tells each agent to read the other applicable instruction body once. No native `@` imports are added,
  preventing new import cycles. A missing counterpart is created only if a root instruction document already exists.
  Root instruction symlinks are preserved and reported for review.
- **Project rules:** `.claude/rules/*.md` and its subdirectories are listed by reference. Unscoped rules apply to the
  project; `paths` lists retain their file-match conditions. Rule bodies are never concatenated into root instructions.
  Unsupported frontmatter, external rule links, or more than 100 rules stop instruction adaptation and are reported.
  These references express shared behavior; they do not turn Codex into Claude's native rule loader.
- **Workers:** supported Claude Markdown agent files become Codex TOML adapters and are registered under
  `[agents.<role>]` in `.codex/config.toml`. Explicit external agent sources also produce a managed Claude copy, keeping
  the external source authoritative. Existing user registrations and any pre-existing unmanaged `agents` configuration require a parser-assisted merge
  and are preserved. A conflicting external Claude counterpart blocks dependent Codex conversion. `Write`/`Edit` restrictions become
  Codex `sandbox_mode = "read-only"`; this may be stricter than disabling one individual edit tool. Unknown tools,
  hooks, permission fields, and other unmappable frontmatter are reported as unsupported. `level` metadata is retained
  in the description. Codex-only agents require an explicit portable source; reverse conversion is not guessed.

Only a conservative YAML subset is accepted: scalar fields, simple lists, and literal/folded description blocks.
Native Codex configuration containing multiline TOML strings requires parser-assisted registration and is left for
review. The helper never weakens a restriction to make an asset appear synchronized.

## Backups and repeatability

Modified regular files are backed up before replacement. Home state lives under `.config/ai-working/`. Git project
state lives under the resolved Git common directory, in `ai-working-assets/<scope-hash>/`, outside tracked working
files. Explicit non-Git projects fall back to `.agent/`. Each contains `asset-sync-state.json` and private
`asset-sync-backups/<run>/` when needed. Non-Git metadata must remain local and must not be published.
Existing symlinks are retained; missing skill counterparts alone receive new symlinks.

Generated file hashes distinguish safe source updates from local customizations. A generated file or managed block
changed outside the synchronizer is reported as a conflict rather than overwritten. Resolve the intended source and
inspect the preserved files before rerunning. When a previously supported worker source disappears or gains unsupported restrictions, unchanged owned
registrations are removed so an older, less restricted adapter does not remain active. Worker files are retained.
Modified configs or worker files block this cleanup with an explicit active-stale warning and a nonzero result.
Do not delete state to bypass a conflict. Destination parent symlinks
cannot redirect writes outside the selected root.

This is a scoped adapter workflow, not blanket copying of every Markdown file. Handbooks, customer facts, execution
history, personal memory, tool credentials, and vendor internals keep their existing ownership and access boundaries.
