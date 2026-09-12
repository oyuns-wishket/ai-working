# ai-working architecture

`ai-working` is the only Git source of truth for reusable Claude and Codex behavior.

## Source boundaries

| Kind | Canonical location |
|---|---|
| Global agent policy | `global/CLAUDE.md` |
| Reusable workflow | `skills/<name>/SKILL.md` and its supporting files |
| Claude/Codex hooks | `hooks/` plus `global/*hooks.json` |
| Workspace-wide defaults | `workspaces/<workspace>/` |
| Project-specific rules and facts | The project repository that owns them |
| Credentials, account IDs, hostnames and local paths | Machine-local configuration, never Git |
| Session history and personal memory | Agent-local storage, never Git |

The bootstrap links both agents directly to files under this repository. It does not load another policy or skill
repository and does not give a second repository precedence.

## Authoring contract

When a reusable rule or workflow changes, edit this repository first. Do not author canonical files under
`~/.claude`, `~/.codex`, `~/.agents`, a retired mirror, or an ignored local directory. Run the public audit, skill
validation, relevant tests, and bootstrap status before publishing.

Customer facts stay in the customer-owned project repository. A reusable skill may explain how to discover those
facts or consume a project-local configuration, but it must not copy customer topology, credentials, contacts, or
runtime identifiers into this public repository.

Machine-specific values use `~/.config/ai-working/`. Public skills may define an example schema under `config/`, but
the real file is not a source of shared policy and is never committed.

## Release safety

`scripts/public_audit.py` rejects credentials, personal paths and hosts, private network addresses, customer-specific
identifiers, session/cache directories, binaries, oversize blobs, and symlinks. CI scans the current tree and every
reachable public Git blob. Private repository history must never be merged, rebased, or cherry-picked into this
history; reusable content is rewritten as a reviewed public snapshot.

Private denylist values live in the machine-local `~/.config/ai-working/public-audit-denylist.txt` and the encrypted
CI secret `AI_WORKING_AUDIT_DENYLIST_B64`. The public scanner contains generic detectors and the loading contract, but
does not publish the protected names it searches for.
