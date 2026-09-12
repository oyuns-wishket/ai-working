---
name: remote-setup
description: Set up or migrate a Mac remote-desktop environment over an approved private network, including host sleep behavior, display quality, input methods, and optional clipboard-image transfer. Use when configuring a headless Mac host or a Mac viewer. Discovers accounts, hosts, and versions instead of embedding them.
---

# Mac remote desktop setup

Interview for the viewer and host devices, remote-desktop product, private-network product, input languages, headless display needs, and whether image clipboard transfer is wanted. One Mac-only setup should not create a second-device configuration.

## Discovery

On each available Mac, inspect macOS version, CPU architecture, hostname, current user, installed app versions, SSH/remote-login state, power settings, displays, and active network nodes. Keep discovered account, hostname, address, fingerprint, and license values machine-local. Use [`../../config/remote-setup.example.env`](../../config/remote-setup.example.env) as a field list, not as a source of defaults.

## Configure

1. Install the user-selected private network and remote-desktop clients through their current supported distribution paths. Browser login, license activation, Screen Recording, Accessibility, and Input Monitoring are user actions.
2. On a headless host, configure only the power and restart settings the user selected. Explain the security effect before enabling automatic login or disabling a lock requirement.
3. Detect whether a physical or dummy display already provides the requested resolution. Add a virtual display tool only when needed and verify its current CLI syntax before automating it.
4. Test Korean/English input with the selected remote protocol. Apply the included Karabiner/macism helper only when the observed input model matches it.
5. For optional image clipboard transfer, install the included scripts under `~/.config/remote-clip/`, inject machine-local `REMOTE_SSH_TARGET`, and add the launchd job after a manual transfer succeeds.

## Verify

Measure network reachability, remote session connection, resolution, keyboard/input switching, reconnect after restart, and clipboard behavior selected by the user. Report each device as verified or unverified. Do not expose network addresses, account emails, SSH fingerprints, or passwords in committed files or logs.

For file-only Remote-SSH setup, use `remote-ssh-edit`. For ordinary file transfer, use `mac-file-sync`.
