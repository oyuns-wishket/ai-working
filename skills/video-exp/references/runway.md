# Runway media MCP

Official sources checked 2026-10-21:
- https://runway.com/mcp
- https://mcp.runwayml.com/
- https://docs.dev.runwayml.com/guides/mcp/

The Dev MCP documentation explicitly distinguishes its developer integration from the generation MCP. For this workflow use **https://mcp.runwayml.com/mcp**. Do not treat registration of Dev MCP as a functioning media-generation connection.

## Connect only when needed

Inspect the installed client's version and existing MCP configuration without dumping credentials. If the same server already exists, reuse it. With a supporting Codex CLI and no duplicate server:

```sh
codex mcp add runway-media --url https://mcp.runwayml.com/mcp
codex mcp login runway-media
```

Use the user's existing authorized account; only ask for user clicks when OAuth requires them. Never print passwords, tokens or cookies. Discover tools after authentication/reconnection. A newly registered server may require a fresh Codex session or MCP reconnect before the current client exposes its tools; verify rather than assuming success. Other clients use their native MCP/OAuth workflow.

Prefer exposed native media tools. A platform adapter is acceptable only when it uses the authenticated client without bypassing its permissions; inspect its supported protocol/version first. Do not replace missing MCP access with an API key or paid API call. If no plan/account/model/credit query exists, state that limitation instead of inferring eligibility.

## Generation lifecycle

Historical working tools included `whoami`, `init_upload`, `complete_upload`, `generate_image`, `generate_video`, `generate_speech`, `get_task`. Names, schemas, model offerings and prices are versioned: inspect actual exposed metadata before calling. Past successful settings were reference-based `nano-banana-2.1` 2K 16:9 and `gen-4-turbo` 10 seconds 16:9; these are not future availability/pricing claims.

1. Read account/model/credit information and calculate the bounded plan. Do not upgrade, buy credits or enable auto-top-up.
2. Upload the approved reference only when the current production scope authorizes it. Keep original local path/hash.
3. Save arguments and receipt in a private task directory outside shared output/public Git, mode600 (directory700). Before submitting a mutation, record a unique attempt marker. Existing marker/unknown response means reconcile task history; never blindly resubmit.
4. Keep `taskId` and poll an existing task with bounded waits. Polling/download failure is not a reason to start a new generated task.
5. Download to local assets without logging signed URLs. Maintain a project-safe record of task status, model, observed cost and accepted/rejected trim; private receipts retain provider details.
6. Inspect before using. No automatic regeneration. When a needed action fails, use an already valid clip or honest narrower demonstration; seek a new generation decision only if required by unresolved scope/cost.

A current task's generation approval is not a perpetual permission attached to this skill/profile. Conversely, do not repeatedly request approval for already authorized shots in the same bounded production plan.
