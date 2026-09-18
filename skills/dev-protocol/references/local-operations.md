# Conditional local operations

Read only the section relevant to the current task. Global policy owns authorization and resource ownership; current project instructions and installed tools determine exact commands. Hook implementation belongs in code and [hook behavior](../../../docs/hook-behavior.md), not in copied global instructions.

## Starting and finishing local Docker/DB work

Before starting, inspect existing resources with `docker ps -a` and record which resources this task owns. A restarting container is not permission to remove another session's work: confirm ownership and impact first. Clean up this task's restarting loops when appropriate.

At the end of the work unit, stop this task's stack using its actual project identity, for example `docker compose down` in the owning compose project or `supabase stop --project-id <id>`. Preserve volumes. Hand off ownership explicitly if another session must continue using a resource.

Verify whether any containers are still running. If the check succeeds and none remain, stop Docker Desktop itself; stopping containers alone leaves the VM resident. Use the installed CLI's supported stop command (for example `docker desktop stop --detach --force`), or the Mac application's quit action. An unavailable or failed Docker probe does not establish an empty machine.

Active trusted hooks may help, but verify cleanup instead of assuming they handled Compose, wrappers, failed commands or ambiguous ownership. See the current hook code/docs when diagnosing missed tracking. Do not stop resources belonging to another task.

## Sharing an HTML result

Serve only the intended artifact directory, excluding credentials and unrelated files. Share the **Tailscale (VPN) address only** — discover it at runtime (`tailscale ip -4`, or the app bundle CLI on macOS). Do not present LAN IPs, `localhost`, or mDNS hostnames as the review URL: the user's device is on the tailnet, not the local LAN, so those never open (user correction 2026-09-18). If no Tailscale address is available, say so and ask how to deliver instead of falling back to LAN. Start a local HTTP server, for example `python3 -m http.server <port> --bind 0.0.0.0`, and record its process ownership so it can be stopped after review or at work-unit end.

URL-encode non-ASCII filenames and verify the actual artifact responds successfully before sharing its URL. Opening a local browser alone shows the server machine's screen, which may not be the user's device. Do not create a new public tunnel or public deployment merely to work around network access without that scope being authorized.

After an authorized deployment is verified, use its URL as the durable link and stop the task's temporary server. Markdown and plain text use file links or conversation content rather than an HTTP server.

## Explicitly requested new project layout

These conventions apply only when the user asks for a new monorepo/layout/work-log structure and the project has no overriding standard. Do not create missing folders just because this reference lists them.

- One client/project per repository. Executable apps in `apps/`; shared code in `packages/`. Multiple apps get separate app packages.
- Keep project context with the project: docs, materials, proposals, design mockups and schema/migrations belong in that repository. Do not split `docs/` into a private local-only repository.
- For the requested work-log layout, use `docs/work-log/_template/` containing `context.md`, `plan.md`, `checklist.md`; non-trivial work under this convention gets `docs/work-log/YYYY-MM-DD_<feature>/` with those three files.
- Consider subtree extraction only when an app/package actually needs an independent repository; do not introduce it as initial ceremony.

## Applying an approved migration

Use the project's documented deployment path. Check the target and dry-run diff against the existing approval; if they match, perform the approved non-destructive operation without another confirmation. Where this environment's command guard requires the explicit execution marker, use `CONFIRMED=1` only for that already-approved operation. It is an execution marker, not evidence of user authorization.

New destructive changes, a different target, or an unapproved production scope require their own decision before applying. Keep the migration source and measured validation with the project change.
