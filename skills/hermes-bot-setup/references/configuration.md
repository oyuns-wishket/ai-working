# Machine-local configuration

Discover the actual Hermes schema from the installed version. The local profile should represent:

- assistant display name and timezone;
- Slack team, bot, app, allowed user, and allowed channel identifiers;
- local paths for app token, bot token, OAuth client, refresh token, and state;
- enabled Gmail and Calendar scopes;
- user-selected schedules and message templates;
- gateway service label and log path.

Identifiers and schedules are personal configuration. Credentials are secrets. Neither belongs in `ai-working`; keep them in the platform keychain or owner-only files outside Git. Validate file permissions and authenticated account identity without printing values.
