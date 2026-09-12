# cswap — Claude Code two-account operation

## Scope and safety

`cswap` is the locally installed `claude-swap` utility. It switches stored Claude Code OAuth credentials while preserving the single shared `~/.claude` configuration directory. It is third-party tooling, not an Anthropic feature.

Never commit or paste OAuth tokens, API keys, Keychain material, `~/.claude.json`, or `cswap export` output. An export is plaintext JSON and is only appropriate for an encrypted, user-controlled backup.

## Everyday use

```bash
cswap status                 # active account and current quota
cswap list                   # both slots and health/quota
cswap switch 1               # select slot 1
cswap switch 2               # select slot 2
cswap switch --strategy best # select the account with the most headroom
cswap tui                    # interactive chooser
cswap run 2 -- --resume      # one terminal invocation under slot 2
```

For an interactive Claude Code session: finish or close the current CLI/IDE Claude tab, run `cswap switch <slot>`, then reopen Claude. The local conversation can be resumed, but the newly selected account may rebuild its prompt cache on the first request.

## Automatic rotation

The local LaunchAgent `com.user.cswap-auto` runs `cswap auto` at login and stays alive. Current intended defaults are a 60-second poll and a 90% threshold, with `best` selection. Inspect without changing anything:

```bash
cswap config
launchctl print gui/$(id -u)/com.user.cswap-auto
```

Do not claim auto-rotation worked solely because the agent is loaded; verify `cswap list` shows both accounts healthy and use `cswap status` after a transition.

## Register or repair an account

To add a second account, use `/login` to authenticate interactively as that account, then register the active credentials in its chosen slot:

```text
claude → /login → finish browser login → exit Claude
cswap add --slot <1-or-2>
cswap list
```

### Exact recovery flow: slot 1 says `relogin_required` while slot 2 is active

This is a **token refresh**, not a new-account registration. On the Mac where `cswap list` shows the problem:

1. Pause automatic switching first. Otherwise `cswap auto` can see slot 1 as unhealthy and switch back to slot 2 between browser login and backup capture:

   ```bash
   DOMAIN="gui/$(id -u)"
   launchctl disable "$DOMAIN/com.user.cswap-auto"
   launchctl bootout "$DOMAIN/com.user.cswap-auto"
   ```

2. **Do not run `/logout`**: it signs out completely and can revoke the refresh token that `cswap` needs to retain for the current slot. In Claude Code, run `/login` directly and complete the browser login as **slot 1's account**. `/login` is the account-change action; it does not require `/logout` first.
3. Save the fresh live login back into the existing slot. Existing Claude sessions do not need forced termination: `cswap` writes the new backup and marks their session profile stale for the next launch.

   ```bash
   cswap add --slot 1
   cswap list
   ```

4. Re-enable automatic switching and verify one tick:

   ```bash
   launchctl enable "$DOMAIN/com.user.cswap-auto"
   launchctl bootstrap "$DOMAIN" ~/Library/LaunchAgents/com.user.cswap-auto.plist
   cswap auto --once
   ```

5. Confirm both slots report readable usage and fresh OAuth. They are now eligible for the existing 90% automatic rotation again. Use `cswap switch 2` later only when you explicitly want to work on slot 2.

Do **not** run `/logout` while registering or refreshing a `cswap` account, create a third slot, remove either slot, export credentials, or repeatedly run `cswap switch 1` before refreshing. `cswap add --slot 1` is the step that replaces the stale stored token with the fresh account-1 login.

### Why a previously registered slot can become dead

A stored slot can become invalid when the provider revokes its refresh token after logout. A second failure mode is an auto-switch race: the background agent can return the live config to another healthy slot before `cswap add --slot 1` captures the new token. Pause auto, use direct `/login`, save the intended slot, then re-enable auto. Inspect the installed `cswap` version and current slot health at runtime; do not encode a machine snapshot in this SSOT.
