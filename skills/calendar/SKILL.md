---
name: calendar
description: Post a user-approved attendance or status update to a configured chat channel. Use for requests such as remote work, off-site work, leaving work, weekend work, or a custom status message. Requires machine-local channel configuration and never stores workspace IDs or tokens in Git.
---

# Calendar status posting

Post one status update only when the user has explicitly asked for that post. Do not infer attendance from a calendar event or schedule.

## Configuration discovery

Read the first existing file from:

1. `$AI_WORKING_CONFIG_DIR/calendar.json`
2. `${XDG_CONFIG_HOME:-$HOME/.config}/ai-working/calendar.json`

Use [`../../config/calendar.example.json`](../../config/calendar.example.json) as the schema. The real file is machine-local, mode `600`, and excluded from Git. It contains the destination adapter and tool, channel identifier, zero or more mention identifiers, and the user's own status-to-message mapping. Never print token values or identifiers.

If the config is missing or invalid, report the missing keys and stop before sending. Obtain credentials from the configured adapter's normal machine-local credential source; never copy credentials from another account or repository.

## Posting

1. Parse the requested status or `custom: <message>` text.
2. Resolve the exact outgoing text from `messages`; for a custom status, use the user's text without adding sensitive context. Append every configured `mention_ids` entry in the adapter's native mention format and listed order.
3. Show the destination name and final text when either is ambiguous. The user's direct request to post a concrete status is sufficient authorization for one send.
4. Use the configured adapter. Verify its response contains a success result and message identifier.
5. Report the posted status and destination label. Do not expose raw IDs, tokens, or API responses.

Do not retry an uncertain send automatically. First query the destination for the expected message or report that delivery is unverified.
