---
name: hermes-bot-setup
description: Set up, rebuild, or migrate a Hermes-powered personal assistant on a Mac with Slack Socket Mode and optional Google integrations. Use for a personal assistant whose owner controls the accounts. Keeps all identities, schedules, tokens, and OAuth state machine-local.
---

# Hermes personal assistant setup

Confirm the Mac role, assistant name, Slack workspace, allowed users/channels, optional Gmail/Calendar capabilities, schedules, and timezone. Do not inherit another person's bot state, OAuth tokens, workspace IDs, or message templates.

## Local configuration

Use [`references/configuration.md`](references/configuration.md) as the field contract. Store the populated config and credentials under owner-only machine-local paths. Git contains placeholders only.

## Slack

Use a regular Slack bot with Socket Mode when no public webhook is desired. Start from [`assets/slack-manifest.json`](assets/slack-manifest.json), remove every event and scope not required by the selected capabilities, create/install the app through Slack, and place the resulting tokens only in the local secret store.

Verify app identity, team identity, and the allowlisted owner before starting the gateway. A message must never select another credential, tenant, or tool scope. Sending a test message requires the user's explicit destination and approval.

## Google services

Create a Desktop OAuth client owned by the user. Request only the selected Gmail/Calendar scopes. Browser consent is a user step. Keep the client secret and refresh token mode `600`; do not pass tokens in argv, logs, prompts, or Git.

For schedules, first run the context script manually with synthetic or read-only input. Record deduplication state atomically in a machine-local state directory. A reminder should wake the agent only when its context says action is needed, and a successful external action must be verified before marking it complete.

## Service and verification

Use the Hermes version's current CLI help to install its supported macOS service. Verify gateway health, restart behavior, Slack DM round trip, sender allowlist rejection, and each selected Google read/write operation. Read operations do not authorize sends, drafts, deletes, attendance posts, or calendar mutations.

Report installed capabilities and remaining browser/GUI steps without exposing account identifiers or raw service output.
