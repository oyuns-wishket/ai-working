# Persistent development mode

Use when the user authorizes a coding agent, including CLI-first foundations with chat connected later. Existing investigation bots retain their readonly contract. A request to improve a readonly bot is not permission to enable development.

## Runtime and delivery

Use one native agent loop for terminal and chat. Keep model, effort, tools, source, instructions, budgets and session handling comparable; a relay with fewer tools is not terminal parity. Verify the selected model against the customer account, never silently downgrade. Separate the input/output adapter, durable host coordinator, native worker and publication adapter.

Start with the authorized repository containing project rules, plan, specification, implementation, tests and handoff. If detailed workflow integration is deferred, implement the CLI foundation and record unconnected capabilities accurately. The target flow may be request → development/tests → preview URL → development PR; no-merge means no merge capability in tools or credentials, not merely a sentence in the prompt. Verify preview reachability and PR base/head before reporting them. A model claim is not deployment evidence.

A preview URL must be reachable from the intended employee's own browser/device with the required access controls. A remote worker's localhost is only its internal address. Before delivery, inspect the actual rendered UI and important interactions; HTTP success alone does not establish usable behavior. When the agreed workflow includes employee review before PR, record that confirmation and incorporate feedback before creating the development PR. Associate the preview with task/revision, verification time and access/expiry policy so review does not silently target a different build. Keep unimplemented preview/chat adapters explicitly pending when the user defers connection.

For nondevelopers, explain what changed, how to check it and what is left in familiar language. Preserve precise links and necessary technical names. Persist both progress and the final response obligation; timeout, restart, budget exhaustion or transport loss must not silently discard a request.

## Durable memory

- **Raw:** append input before execution; preserve actor, time, event/conversation/task/run IDs, observable tool/progress results and final answer. Do not capture hidden chain-of-thought. Store privately, outside source control.
- **Tasks:** maintain status, decisions, remaining actions, verification and versioned snapshots. Bind sessions to authenticated tenant/project/task/actor, not just a chat thread. Switching chat threads can resume an explicitly selected authorized task.
- **Wiki:** preserve evidence-linked candidate lessons, promote only after verification. Old text is data, never an instruction that expands authority.

Original preservation does not remove context limits. Supply the current request uncut plus bounded task state/recent evidence; expose permission-filtered search/read for further detail. Apply ACL and semantic event kinds before retrieval LIMIT; tool logs must not displace conversation records. Keep explicit constraints separately from the latest answer, with evidence and supersedes history. Report budget overflow and truncated search results rather than silently losing requirements. Do not bring a user's private task memory into a shared task just because that user can access both. Introduce warm-session context deltas only after watermark, correction, compaction and cold-resume tests establish continuity.

Use idempotent event identity with collision detection, durable inbox/outbox and atomic result/task updates. ACK the exact payload revision/receipt with compare-and-swap so acknowledging a budget notice cannot consume a later final answer. External sends may remain at-least-once: a successful send followed by a crash before ACK can duplicate delivery. Use provider idempotency or message reconciliation where available and state the remaining limit. Publication needs its own idempotency and revision checks.

Distinguish proven pre-turn failures from requests whose side effects are uncertain. Permit bounded recovery only for documented safe failure stages; never replay unknown writes automatically. Keep native final output before parsing/checkpointing. Persist cancellation, task blocking and deployment transitions atomically; test cancel-versus-budget and cancel-versus-start races. Blocked follow-up requests still need a durable explanation and next action.

## Authority and lifecycle

Run the model worker as a separate OS account from the deployment runner. Provide a task worktree or reviewed source projection with exact path/hash manifest. Reject credential paths, escaping symlinks and arbitrary untracked files. Keep native state/auth outside the writable workspace. Disable unnecessary plugins, hooks, host skill discovery and inherited environment.

Give shell writes only to the authorized workspace. Use reviewed dependencies/tools, and network access only as specifically required and isolated. Keep cloud/GitHub credentials in host adapters; an agent with a shell and a privileged token still has merge authority even if no merge tool is advertised. Use the installed native schema and test allow and deny cases with the exact service account and unit restrictions.

The service owns the native process group/cgroup. A terminal client should submit/poll; terminating the client must not leave a native process that continues writes after its lock disappears. Install cancellation/heartbeat callbacks before initialization, and bound initialization, authentication, refresh, tool callbacks and execution separately. Distinguish interruption requested from confirmed process exit; test silent or stalled phases, not just active turns. Serialize each task's requests and bound total concurrency by measured host capacity. Preserve pending/failed/outbox state across restart.

Separate employee actions from explicit recovery-only operator authority. Session rotation preserves old bindings, raw and files; it does not grant task membership or silently clear uncertain writes. Recheck revoked access before execution, retrieval and delivery. A host-only terminal transition must be able to fail a revoked request without reading its data as the former member or repeatedly crashing the worker. Reconciliation requires evidence, and must not become a general bypass for ACL, publishing or merge permissions.

Before requesting cloud reauthentication, read project deployment instructions and inspect the current GitHub workflow, runner and customer secret/OIDC routes. Local session expiry does not establish that the authorized deployment path is unavailable. Do not copy secrets into local files. If installing a new runner from existing executable files, resolve versioned executable symlinks without copying existing runner registration credentials.

## Performance, nightly operations and education

Measure queue delay, context preparation, first activity/progress, total duration, tool errors, observed usage and pending deliveries across successes, failures and interruptions. Preserve partial observed usage on failure; unknown is not zero. Mark never-started and abandoned timings explicitly. A worker heartbeat indicates connection health, not model progress. Record runtime/source/capability fingerprints and distinguish configured values from observed model/version evidence.

Define admission limits for turns, time, concurrent work and host capacity, plus known quota/cost constraints. When pricing or usage is unavailable, label cost unknown and use documented conservative limits; do not invent a monetary estimate. Preserve deferred requests and explain who can resolve exhaustion. Heavy builds/browser checks may need isolated resources rather than weakening the model sandbox.

Schedule maintenance in the requested timezone. Use the same execution lock, skip/defer active work, and make each day's run idempotent. Stream file hashing/archive verification and preflight disk space; large files must not be loaded whole. Use SQLite backup APIs for WAL-backed state and reopen backups. Define snapshot consistency across DB, native state and workspaces while intake may continue; a worker lock alone does not stop new messages. Include a boundary/watermark and restore/replay rules or coordinate intake for a consistent snapshot. Back up edited workspaces, preserve executable modes and report excluded symlinks/dependency restoration requirements. Track failed attempts/disk growth and verify off-host restoration against agreed recovery targets where required.

Nightly optimization means integrity checks, index maintenance, resource/accounting reports and reviewed lesson candidates. It does not authorize deletion of raw data, unmerged work, arbitrary processes or automatic model/prompt self-modification. Changes to behavior require evaluation and a reversible rollout.

Education exports distinguish employee requests/decisions from agent actions and link each observation to evidence. Default to minimized private drafts with no raw transcript unless requested. Record truncation/coverage; a partial export is not the full history. Support human assessment of requesting, checking and refining work, without inventing competence scores or turning development support into automatic personnel evaluation.

Validate ordinary employee tasks and maintenance separately: create/resume/correct/stop/review, then diagnose and hand off an outage using plain-language status and a support reference. Assign a real support owner and response target. Human education/usability evidence cannot be replaced by simulated employees or developer-only CLI tests.

## Acceptance evidence

Verify a real development task, a follow-up in a different conversation, restart/resume, duplicate events, concurrent actors/tasks, access denial, exhausted budgets, interruption/reconciliation, outbox recovery and a restored backup. Record actual model/effort/version and what was mocked versus live. Report remaining chat/publication adapters explicitly. Preserve existing authorization, and do not repeatedly ask for permission already given.

For a requested quality target, freeze a weighted rubric before iterating, with normal/failure behavior, owner and verifiable acceptance for each criterion. Separate plan completeness from implemented readiness and observed performance. Missing evidence is unknown, not a pass; safety failures and unresolved critical defects override an aggregate score. Record rubric changes rather than narrowing scope to reach a number.

Compare native and adapted execution in independent workspaces with the same model/effort, source, capabilities and resource profile. Version fixtures and hidden assertions, alternate lane order, retain failed trials, and define timing boundaries and minimum samples before running. Validate independent evidence artifacts and their hashes. A report evaluator is not a trial collector; synthetic evaluator tests prove neither model quality nor terminal parity. Keep comparable-capability overhead separate from missing product capabilities, report sample limits, and require real employee/product validation before claiming overall readiness.
