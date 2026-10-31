# Persistent development mode

Use when the user authorizes a coding agent, including CLI-first foundations with chat connected later. Existing investigation bots retain their readonly contract. A request to improve a readonly bot is not permission to enable development.

## Runtime and delivery

Use one native agent loop for terminal and chat. Keep model, effort, tools, source, instructions, budgets and session handling comparable; a relay with fewer tools is not terminal parity. Verify the selected model against the customer account, never silently downgrade. Separate the input/output adapter, durable host coordinator, native worker and publication adapter.

Start with the authorized repository containing project rules, plan, specification, implementation, tests and handoff. If detailed workflow integration is deferred, implement the CLI foundation and record unconnected capabilities accurately. The target flow may be request → development/tests → preview URL → development PR; no-merge means no merge capability in tools or credentials, not merely a sentence in the prompt. Verify preview reachability and PR base/head before reporting them. A model claim is not deployment evidence.

For nondevelopers, explain what changed, how to check it and what is left in familiar language. Preserve precise links and necessary technical names. Persist both progress and the final response obligation; timeout, restart, budget exhaustion or transport loss must not silently discard a request.

## Durable memory

- **Raw:** append input before execution; preserve actor, time, event/conversation/task/run IDs, observable tool/progress results and final answer. Do not capture hidden chain-of-thought. Store privately, outside source control.
- **Tasks:** maintain status, decisions, remaining actions, verification and versioned snapshots. Bind sessions to authenticated tenant/project/task/actor, not just a chat thread. Switching chat threads can resume an explicitly selected authorized task.
- **Wiki:** preserve evidence-linked candidate lessons, promote only after verification. Old text is data, never an instruction that expands authority.

Original preservation does not remove context limits. Supply the current request uncut plus bounded task state/recent evidence; expose permission-filtered search/read for further detail. Apply ACL before retrieval LIMIT. Do not bring a user's private task memory into a shared task just because that user can access both.

Use idempotent event identity with collision detection, durable inbox/outbox and atomic result/task updates. A crashed write run enters reconciliation; never replay unknown side effects automatically. Keep the native final output before parsing/checkpointing so a schema failure does not force code to run again. Publication and delivery need separate idempotency keys and receipts.

## Authority and lifecycle

Run the model worker as a separate OS account from the deployment runner. Provide a task worktree or reviewed source projection with exact path/hash manifest. Reject credential paths, escaping symlinks and arbitrary untracked files. Keep native state/auth outside the writable workspace. Disable unnecessary plugins, hooks, host skill discovery and inherited environment.

Give shell writes only to the authorized workspace. Use reviewed dependencies/tools, and network access only as specifically required and isolated. Keep cloud/GitHub credentials in host adapters; an agent with a shell and a privileged token still has merge authority even if no merge tool is advertised. Use the installed native schema and test allow and deny cases with the exact service account and unit restrictions.

The service owns the native process group/cgroup. A terminal client should submit/poll; terminating the client must not leave a native process that continues writes after its lock disappears. Serialize each task's requests and bound total concurrency by measured host capacity. Preserve pending/failed/outbox state across restart. Unknown writes require evidence-based operator reconciliation.

Before requesting cloud reauthentication, read project deployment instructions and inspect the current GitHub workflow, runner and customer secret/OIDC routes. Local session expiry does not establish that the authorized deployment path is unavailable. Do not copy secrets into local files. If installing a new runner from existing executable files, resolve versioned executable symlinks without copying existing runner registration credentials.

## Performance, nightly operations and education

Measure queue delay, context preparation, first progress, total duration, successful completion, tool errors, tokens when available and pending deliveries. Compare fixed representative tasks using the same source/model/effort and explicit pass criteria. Distinguish measured regression from guesses; model quality cannot be established by a service health check or mock tests.

Schedule maintenance in the requested timezone. Use the same execution lock, skip/defer active work, and make each day's run idempotent. Verify database backups by reopening them; use SQLite backup APIs for WAL-backed native state. Back up edited workspaces as well as conversations. Preserve executable modes and report excluded symlinks/dependency restoration requirements. Track disk growth and provide a verified off-host recovery plan where required.

Nightly optimization means integrity checks, index maintenance, resource/accounting reports and reviewed lesson candidates. It does not authorize deletion of raw data, unmerged work, arbitrary processes or automatic model/prompt self-modification. Changes to behavior require evaluation and a reversible rollout.

Education exports distinguish employee requests/decisions from agent actions and link each observation to evidence. Default to minimized private drafts with no raw transcript unless requested. Record truncation/coverage; a partial export is not the full history. Support human assessment of requesting, checking and refining work, without inventing competence scores or turning development support into automatic personnel evaluation.

## Acceptance evidence

Verify a real development task, a follow-up in a different conversation, restart/resume, duplicate events, concurrent actors/tasks, access denial, exhausted budgets, interruption/reconciliation, outbox recovery and a restored backup. Record actual model/effort/version and what was mocked versus live. Report remaining chat/publication adapters explicitly. Preserve existing authorization, and do not repeatedly ask for permission already given.
