# Paseo archive resource cleanup

This optional server plugin connects Paseo's official `agent.archived` event to
the installed ai-working resource guard. Workspace archive emits the same event
for its agents. It supports the Claude and Codex hooks; it does not execute other
SessionEnd commands or take ownership of resources.

The handler reads the native session ID through the official client API, waits
up to 20 seconds for the same archived agent to become `closed`, then invokes
`~/.claude/hooks/dev-resource-guard.mjs`. A restored or replaced session is
skipped. The existing guard retains immutable container IDs and shared Supabase
ownership checks. A per-session OS lock prevents overlapping native/plugin
cleanup and is automatically released if a process is killed. Lock files remain
in the local cache intentionally; deleting an active lock file is unsafe.
If Paseo has already removed a worktree, Supabase cleanup uses a temporary working
directory with the same verified explicit project ID; it never uses `--all` or
`--no-backup`.

## Install on a selected machine

Requires Paseo >= 0.10.3, Node, Python 3 (macOS/Linux), and the installed shared
hooks. There are no npm dependencies or provider binary modifications.

1. Run the repository bootstrap dry-run, inspect changes, then apply and verify.
2. Inspect `paseo plugin ls --json` and the machine-local Paseo configuration.
   Enabling the plugin runtime can enable other configured plugins, so review
   those first and preserve unrelated settings. Installation is part of an
   authorized local environment change; bootstrap does not enable plugins on
   every machine automatically.
3. From the canonical checkout, run:

   ```sh
   paseo plugin install "$PWD/plugins/paseo-resource-cleanup"
   ```

4. If global plugins are disabled, enable `pluginsEnabled` in that machine's
   Paseo configuration after reviewing the activation scope, and run `paseo reload`.
   Then use `paseo plugin reload ai-working-resource-cleanup` and check that
   `paseo plugin ls ai-working-resource-cleanup --json` says `running`.
   No daemon restart is necessary for the plugin runtime reload.
5. On source updates, apply the shared hooks through bootstrap and reload this
   plugin. A directory installation points at this canonical source.

## Verify and diagnose

- `node --test tests/paseo-resource-cleanup.test.mjs tests/resource-cleanup-lock.test.mjs`
- `node --test tests/hook-dev-resource-guard.test.mjs`
- `paseo plugin logs ai-working-resource-cleanup --json`

For live verification, create a disposable agent and place a marker with
`ownershipVersion: 0` under the resource guard's `sessions/<native-session-id>.json`
cache path. Archive only that disposable agent/workspace and wait for its marker
to disappear. Such a marker cannot authorize container shutdown. Check an
unrelated marker remains and check the plugin log. Never fabricate a version 2
ownership marker for live resources.

`dispatched` means the guard finished planning and launched any needed detached
cleanup; it does not prove Docker/Supabase stop succeeded. `absent` means there
was no resource marker, including when native SessionEnd already consumed it.
Failures and timeouts appear in plugin logs. Archive is asynchronous and does not
wait for this plugin. Disabled/unloaded plugins or events missed while the daemon
is down are not replayed. Servers launched with the installed `managed-server.py --session <native-id> start -- <command>`
are cleaned too, including process-only sessions. See `cleanup-results/` and
`process-results/` under the local resource guard cache for verified outcomes.
Unregistered resources remain manual cleanup; failed Docker cleanup retains
ownership for retry. Explicitly disposable owned containers can be removed
without deleting volumes.

To undo this integration, `paseo plugin remove ai-working-resource-cleanup`.
Leave other plugins and the native hooks intact; restore a previously disabled
global plugin runtime only when no other plugin now depends on it.
