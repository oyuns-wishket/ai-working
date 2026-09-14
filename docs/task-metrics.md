# Machine-local task measurements

Use `scripts/task_metrics.py` to compare elapsed wall time, reported tokens, manual
retry counts, and verification results for a meaningful task. It uses Python's
standard library, performs no network requests, and changes no model settings.

## Agent lifecycle

Start before implementation. Choose a fresh, non-sensitive lowercase task slug;
`--project` defaults to the current directory. The script path below assumes the
shell is in the ai-working checkout.

```sh
python3 scripts/task_metrics.py start fix-example --project /path/to/project \
  --session-log codex:/path/to/main-session.jsonl
```

Pass the exact native Claude Code or Codex JSONL transcript path. The CLI never
discovers sessions by project directory, time range, or a wildcard. If the current
session path is unavailable, omit it: timing and checks remain useful and tokens
are explicitly unknown. Add a known main/worker log at any point before finish:

```sh
python3 scripts/task_metrics.py add-session fix-example \
  --session-log claude:/path/to/worker-session.jsonl
```

Wait for your own workers and run the project's checks, then finish in the same
work unit. Record the results you actually observed. `not-run` is the default for
build, lint, and test; other check names are allowed. Retry count means your
manually observed rework attempts, not a guessed count of tool calls. Omit it if
unknown; use zero only when observed.

```sh
python3 scripts/task_metrics.py finish fix-example --retries 1 \
  --check build=pass --check lint=pass --check test=not-run
python3 scripts/task_metrics.py report fix-example
```

`--session-log` is repeatable on start, add-session, and finish. Finish rereads all
attached logs and freezes the measurement; repeat start/finish and changes to a
finished task are rejected. `report` on a running task is a live snapshot. Do not
assign the same session/time window to independent tasks: the tool cannot infer
which overlapping task owns a request. Use each worker's own session log.

## Interpretation and privacy

- State lives only in `$XDG_STATE_HOME/ai-working/task-metrics/` (default
  `~/.local/state/ai-working/task-metrics/`). The directory is mode 0700 and files
  are mode 0600. A process lock prevents concurrent lost updates; contention fails
  with a retry message. No data is written to the project or synchronized to Git.
- Stored data consists of task identifiers, private project/session path
  references, UTC times, counters, model identifiers, and explicit check results.
  It never stores transcript text, prompts, tool output, or credentials. JSON
  reports omit source/project paths and use SHA-256 identifiers instead. Keep
  slugs generic, and do not publish reports without reviewing their metadata.
- Elapsed time includes waiting and idle time; it is **not active work time**.
  Only timestamped usage within start/finish bounds is counted. Starting midway
  through a session does not charge its entire cumulative history to the task.
- Claude snapshots merge by request/message identity using maximum reported
  counters. Total input is fresh input + cache read + cache creation. Codex uses
  `last_token_usage`; cumulative totals are only duplicate/reset markers. Native
  fork copies retaining their timestamp and usage deduplicate across source logs.
  Rewritten timestamps or unsupported exporters can prevent that deduplication.
- `tokens.*.value` is the sum of **reported** values, not always a complete total.
  `coverage` is `reported`, `partial`, or `unknown`. Missing values are JSON
  `null`, not zero. Codex `cache_write_input_tokens` and Claude
  `output_tokens_details.thinking_tokens` are read when present; either may be
  unreported. Fresh input excludes both cache reads and cache writes; it remains
  unknown in Codex when cache writes are unreported. Reasoning tokens, when present, are a subset of output; do not
  add them to output again. Missing cache creation keeps Claude total input
  unknown for that call.
- Missing/malformed/truncated/unreadable records mark coverage partial or unknown.
  JSONL is streamed with a 2 MiB line limit and 100,000-call memory bound; skipped
  records are exposed in `diagnostics`. Unrelated logs are never scanned. Usage
  emitted after finish is not included; wait for workers to flush before finish.
- Token counts are not subscription bills or cost savings. Compare similar tasks
  with the same verification standard; lower tokens alone do not establish a
  better outcome. No automatic routing or billed-cost estimate is attempted.
