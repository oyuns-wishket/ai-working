---
name: mac-file-sync
description: Send files or safely synchronize a selected folder between Macs over Tailscale. Use for Taildrop transfers or rsync with a required dry-run. Discovers node and user names at runtime and has no built-in personal hosts or paths.
---

# Mac file sync

Use Tailscale status and the current filesystem to discover both ends. Never assume a node name, SSH user, home directory, or destination.

## Send files with Taildrop

1. Run `tailscale status` read-only and present matching online nodes when the target is unclear.
2. Send regular readable files only:

```bash
scripts/taildrop-send.sh --to <node-from-status> <file> [file ...]
```

The script prints file names, sizes, and SHA-256 hashes before sending. The user's concrete request to send named files to a named node authorizes that transfer. If the target is ambiguous, ask before sending.

On the receiving Mac:

```bash
scripts/taildrop-receive.sh [destination]
```

The default destination is `${AI_WORKING_RECEIVE_DIR:-$HOME/Downloads}`. Verify received size and hash against the sender.

## Synchronize a folder

Confirm the source and destination semantics, then run the mandatory dry-run:

```bash
scripts/safe-rsync.sh <source-dir/> <user@ssh-host:/absolute/destination/>
```

Review every listed create/update. The helper never uses `--delete`. Apply only after the displayed dry-run matches the requested scope:

```bash
scripts/safe-rsync.sh --apply <source-dir/> <user@ssh-host:/absolute/destination/>
```

Re-run dry-run and require zero changes. Do not broaden a file-send request into folder synchronization.
