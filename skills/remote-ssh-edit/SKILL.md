---
name: remote-ssh-edit
description: Set up or repair VS Code Remote-SSH between Macs or other SSH hosts so projects can be edited where their files live. Use for SSH config, key authentication, remote project access, or Markdown preview. Discovers all host, user, and path values at runtime.
---

# Remote SSH editing

Determine whether the active machine is the client or server. Read existing `~/.ssh/config`, public keys, Remote-SSH extension state, and the remote system's SSH service without printing private keys.

## Required decisions

Obtain or discover:

- a user-chosen SSH alias;
- the host from an approved VPN/DNS service or the user's explicit value;
- the remote OS user and project root;
- the existing identity file, if any.

Keep these values in machine-local `~/.ssh/config`. Do not write them into `ai-working`.

## Server side

Enable Remote Login through the OS-supported path. Add only the client's public key to `~/.ssh/authorized_keys`; never transfer a private key. Preserve existing keys and enforce directory/file permissions. OS password and GUI approval remain user steps.

## Client side

Merge one idempotent host block into `~/.ssh/config` and keep unrelated hosts intact:

```sshconfig
Host <chosen-alias>
  HostName <discovered-host-or-address>
  User <remote-user>
  IdentityFile <existing-private-key-path>
  IdentitiesOnly yes
```

Use `StrictHostKeyChecking=accept-new` only for the first verified connection. A changed known host key requires out-of-band identity confirmation before removing the old entry.

Verify with `ssh -o BatchMode=yes -o ConnectTimeout=6 <alias> 'pwd'`, then open the discovered project root through VS Code Remote-SSH. Confirm that edits and Markdown preview operate on the remote filesystem. Do not claim setup on a second machine until tested there.
