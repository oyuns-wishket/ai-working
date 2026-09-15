#!/usr/bin/env python3
"""Spawn, monitor, collect and cancel lane sessions for multi-session-dev.

One lane = one headless CLI session (`claude -p` or `codex exec`) running in
its own worktree (write lanes) or the Lead checkout (read lanes). The runner
never merges; see integrate.py. State lives under
$XDG_STATE_HOME/multi-session-dev/tasks/<repo-id>/<task>/.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from configure import default_config_path, load_config
from lane_plan import (
    DEFAULT_MAX_PARALLEL,
    DEFAULT_RETRY_LIMIT,
    lane_by_id,
    load_plan,
    validate_plan,
)
from worktree_manager import (
    create_worktree,
    dirty_paths,
    git_root,
    repo_id,
    run_git,
)

SKILL_ROOT = Path(__file__).resolve().parents[1]
RESULT_SCHEMA_PATH = SKILL_ROOT / "assets" / "lane-result.schema.json"
PROMPT_TEMPLATE_PATH = SKILL_ROOT / "assets" / "lane-prompt.md"
LANE_ENV = "MULTI_SESSION_DEV_LANE"
POLL_SECONDS = 2.0
CANCEL_GRACE_SECONDS = 10.0
TERMINAL = {"complete", "blocked", "failed", "cancelled", "skipped"}
STRIP_ENV = (
    "CLAUDECODE",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_MESSAGING_SOCKET",
    "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_PID",
    "CLAUDE_EFFORT",
)
READ_LANE_DISALLOWED = ["Write", "Edit", "MultiEdit", "NotebookEdit", "Bash(git push*)", "Bash(git commit*)"]
WRITE_LANE_DISALLOWED = ["Bash(git push*)"]


# --------------------------------------------------------------------------- state


def default_state_root() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return root / "multi-session-dev"


def task_dir(state_root: Path, repo: Path, task: str) -> Path:
    return state_root / "tasks" / repo_id(repo) / task


def task_state_path(state_root: Path, repo: Path, task: str) -> Path:
    return task_dir(state_root, repo, task) / "task.json"


def load_task_state(state_root: Path, repo: Path, task: str) -> dict[str, Any]:
    path = task_state_path(state_root, repo, task)
    if not path.exists():
        return {"schema_version": 1, "repo": str(repo), "task": task, "lanes": {}}
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def save_task_state(state_root: Path, repo: Path, task: str, state: dict[str, Any]) -> None:
    path = task_state_path(state_root, repo, task)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.chmod(temp, 0o600)
    os.replace(temp, path)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # A reaped-but-not-collected zombie still answers kill(0); check its state.
    try:
        out = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
        ).stdout.strip()
    except OSError:
        return True
    if not out:
        return False
    return not out.startswith("Z")


# --------------------------------------------------------------------------- config


def runtime_config(args: argparse.Namespace) -> dict[str, Any]:
    return load_config(Path(args.config).expanduser())


def binary(name: str, config: dict[str, Any]) -> str:
    override = (config.get("binaries") or {}).get(name)
    if override:
        return override
    found = shutil.which(name)
    if not found:
        raise SystemExit(f"{name} CLI not found on PATH; set binaries.{name} in the config")
    return found


def role_default(config: dict[str, Any], role: str, key: str) -> Any:
    defaults = config.get("role_defaults") or {}
    return (defaults.get(role) or {}).get(key) or (defaults.get("*") or {}).get(key)


# --------------------------------------------------------------------------- prompt


def read_prompt_text(plan: dict[str, Any], lane: dict[str, Any], repo: Path) -> str:
    if lane.get("prompt_file"):
        path = Path(lane["prompt_file"]).expanduser()
        if not path.is_absolute():
            path = repo / path
        return path.read_text(encoding="utf-8")
    return str(lane.get("prompt", ""))


def render_prompt(
    plan: dict[str, Any],
    lane: dict[str, Any],
    *,
    repo: Path,
    cwd: Path,
    branch: str | None,
    extra: str | None = None,
) -> str:
    template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    owned = lane.get("owned_paths") or []
    verify = lane.get("verify_commands") or []
    rules = plan.get("rules_to_read") or []
    if lane.get("write"):
        commit_instruction = (
            f"commit your work on branch `{branch}` with clear messages before returning; "
            "never push. The Lead merges lane branches."
        )
    else:
        commit_instruction = "this lane is read-only; do not commit."
    values = {
        "lane_id": lane["id"],
        "task": plan["task"],
        "repo": str(repo),
        "cwd": str(cwd),
        "branch": branch or "(Lead checkout, no lane branch)",
        "mode": lane.get("mode"),
        "write": "yes" if lane.get("write") else "no",
        "role": lane.get("role"),
        "issue": plan.get("issue") or "none",
        "owned_paths": ", ".join(f"`{p}`" for p in owned) if owned else "(none: read-only lane)",
        "resources": plan.get("resources") or "none beyond what already exists in the repo",
        "commit_instruction": commit_instruction,
        "rules_to_read": "\n".join(f"- `{r}`" for r in rules) if rules else "- `CLAUDE.md` / `AGENTS.md` if present",
        "acceptance": lane.get("acceptance", ""),
        "verify_commands": "\n".join(f"- `{c}`" for c in verify) if verify else "- (none specified; report what you did run)",
        "lane_prompt": read_prompt_text(plan, lane, repo),
    }
    text = template
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", str(value))
    if extra:
        text += f"\n\n## Lead follow-up for this attempt\n\n{extra}\n"
    return text


# --------------------------------------------------------------------------- commands


def claude_command(
    lane: dict[str, Any],
    config: dict[str, Any],
    *,
    task: str,
    session_id: str,
    resume: str | None,
) -> list[str]:
    # Claude's validator rejects the "$schema" meta key; pass a compact schema without it.
    schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    schema.pop("$schema", None)
    schema_text = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    cmd = [
        binary("claude", config),
        "-p",
        "--output-format",
        "json",
        "--json-schema",
        schema_text,
        "--permission-mode",
        "bypassPermissions",
        "--permission-prompts",
        "none",
        "--name",
        f"msd-{task}-{lane['id']}",
    ]
    if resume:
        cmd += ["--resume", resume]
    else:
        cmd += ["--session-id", session_id]
    model = lane.get("model") or role_default(config, lane.get("role", ""), "claude_model")
    if model:
        cmd += ["--model", str(model)]
    effort = lane.get("effort") or role_default(config, lane.get("role", ""), "claude_effort")
    if effort:
        cmd += ["--effort", str(effort)]
    budget = lane.get("max_budget_usd") or config.get("max_budget_usd")
    if budget:
        cmd += ["--max-budget-usd", str(budget)]
    disallowed = list(WRITE_LANE_DISALLOWED if lane.get("write") else READ_LANE_DISALLOWED)
    disallowed += list(lane.get("disallowed_tools") or [])
    cmd += ["--disallowedTools", ",".join(disallowed)]
    return cmd


def codex_command(
    lane: dict[str, Any],
    config: dict[str, Any],
    *,
    cwd: Path,
    last_message: Path,
    resume: str | None,
) -> list[str]:
    cmd = [binary("codex", config), "exec"]
    if resume:
        cmd += ["resume", resume]
    cmd += [
        "-C",
        str(cwd),
        "-s",
        "workspace-write" if lane.get("write") else "read-only",
        "--json",
        "-o",
        str(last_message),
        "--output-schema",
        str(RESULT_SCHEMA_PATH),
    ]
    model = lane.get("model") or role_default(config, lane.get("role", ""), "codex_model")
    if model:
        cmd += ["-m", str(model)]
    effort = lane.get("effort") or role_default(config, lane.get("role", ""), "codex_effort") or "high"
    cmd += ["-c", f'model_reasoning_effort="{effort}"']
    cmd.append("-")
    return cmd


def lane_env(task: str, lane_id: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in STRIP_ENV}
    env[LANE_ENV] = f"{task}/{lane_id}"
    env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "0"
    return env


# --------------------------------------------------------------------------- spawn


def ensure_not_nested() -> None:
    if os.environ.get(LANE_ENV):
        raise SystemExit(
            f"nested spawn refused: this process is already lane {os.environ[LANE_ENV]}"
        )


def running_count(state: dict[str, Any]) -> int:
    count = 0
    for lane in state.get("lanes", {}).values():
        if lane.get("status") == "running" and pid_alive(lane.get("pid")):
            count += 1
    return count


def spawn_lane(
    plan: dict[str, Any],
    lane: dict[str, Any],
    *,
    repo: Path,
    config: dict[str, Any],
    state_root: Path,
    state: dict[str, Any],
    worktree_root: Path | None,
    follow_up: str | None = None,
    resume: bool = False,
    hold: bool = False,
) -> tuple[dict[str, Any], subprocess.Popen[bytes] | None]:
    task = plan["task"]
    lane_id = lane["id"]
    record = state["lanes"].get(lane_id) or {"attempts": 0}
    if record.get("status") == "running" and pid_alive(record.get("pid")):
        raise SystemExit(f"lane {lane_id} is already running (pid {record['pid']})")
    retry_limit = plan.get("retry_limit", DEFAULT_RETRY_LIMIT)
    if record.get("attempts", 0) >= retry_limit + 1 and not hold:
        raise SystemExit(
            f"lane {lane_id} reached retry limit ({retry_limit}); escalate to the user"
        )

    lane_dir = task_dir(state_root, repo, task) / lane_id
    attempt = record.get("attempts", 0) + 1
    attempt_dir = lane_dir / f"attempt-{attempt}"
    attempt_dir.mkdir(parents=True, exist_ok=True)

    branch = record.get("branch")
    worktree_path = record.get("worktree_path")
    if lane.get("write"):
        if worktree_path and Path(worktree_path).is_dir():
            cwd = Path(worktree_path)
        else:
            if worktree_root is None:
                raise SystemExit("worktree_root is not configured; run configure.py set --worktree-root")
            created = create_worktree(
                repo,
                task,
                lane_id,
                base_ref=plan.get("base_ref", "HEAD"),
                worktree_root=worktree_root,
                state_root=state_root,
                allow_generated_worker_metadata=True,
            )
            cwd = Path(created["worktree_path"])
            branch = created["branch"]
            worktree_path = str(cwd)
    else:
        cwd = repo

    resume_id = None
    if resume:
        resume_id = record.get("session_id") if lane["platform"] == "claude" else record.get("thread_id")
        if not resume_id:
            raise SystemExit(f"lane {lane_id} has no previous session to resume")

    prompt = render_prompt(plan, lane, repo=repo, cwd=cwd, branch=branch, extra=follow_up)
    prompt_path = attempt_dir / "prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    session_id = str(uuid.uuid4())
    last_message = attempt_dir / "last-message.json"
    if lane["platform"] == "claude":
        cmd = claude_command(lane, config, task=task, session_id=session_id, resume=resume_id)
    else:
        cmd = codex_command(lane, config, cwd=cwd, last_message=last_message, resume=resume_id)

    stdout_path = attempt_dir / "stdout.jsonl"
    stderr_path = attempt_dir / "stderr.log"
    with prompt_path.open("rb") as stdin, stdout_path.open("wb") as stdout, stderr_path.open(
        "wb"
    ) as stderr:
        process = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            env=lane_env(task, lane_id),
            start_new_session=True,
        )

    record.update(
        {
            "status": "running",
            "role": lane.get("role"),
            "mode": lane.get("mode"),
            "platform": lane["platform"],
            "write": bool(lane.get("write")),
            "advisory": bool(lane.get("advisory")),
            "depends_on": list(lane.get("depends_on") or []),
            "cwd": str(cwd),
            "worktree_path": worktree_path,
            "branch": branch,
            "pid": process.pid,
            "pgid": process.pid,
            "attempts": attempt,
            "attempt_dir": str(attempt_dir),
            "started_at": now_iso(),
            "ended_at": None,
            "exit_code": None,
            "session_id": session_id if lane["platform"] == "claude" and not resume_id else record.get("session_id"),
            "timeout_seconds": lane.get("timeout_seconds"),
            "command": cmd[:1] + [arg if len(arg) < 200 else arg[:200] + "…" for arg in cmd[1:]],
        }
    )
    state["lanes"][lane_id] = record
    state["target_branch"] = plan.get("target_branch")
    state["lane_order"] = [l["id"] for l in plan["lanes"]]
    state["plan_path"] = state.get("plan_path")
    save_task_state(state_root, repo, task, state)
    return record, (process if hold else None)


# --------------------------------------------------------------------------- collect


def claude_project_slug(cwd: Path) -> str:
    return re.sub(r"[^A-Za-z0-9-]", "-", str(cwd))


def find_session_log(record: dict[str, Any]) -> str | None:
    if record.get("platform") == "claude":
        session_id = record.get("session_id")
        if not session_id:
            return None
        direct = Path.home() / ".claude" / "projects" / claude_project_slug(Path(record["cwd"])) / f"{session_id}.jsonl"
        if direct.is_file():
            return str(direct)
        matches = glob.glob(str(Path.home() / ".claude" / "projects" / "*" / f"{session_id}.jsonl"))
        return matches[0] if matches else None
    thread_id = record.get("thread_id")
    if not thread_id:
        return None
    matches = glob.glob(str(Path.home() / ".codex" / "sessions" / "*" / "*" / "*" / f"rollout-*-{thread_id}.jsonl"))
    return matches[0] if matches else None


def parse_claude_output(stdout_path: Path) -> dict[str, Any]:
    final: dict[str, Any] | None = None
    for line in stdout_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if data.get("type") == "result":
            final = data
    if final is None:
        return {"parsed": False}
    result = final.get("structured_output")
    if result is None and isinstance(final.get("result"), str):
        try:
            result = json.loads(final["result"])
        except json.JSONDecodeError:
            result = None
    return {
        "parsed": True,
        "result": result,
        "session_id": final.get("session_id"),
        "is_error": bool(final.get("is_error")),
        "subtype": final.get("subtype"),
        "cost_usd": final.get("total_cost_usd"),
        "num_turns": final.get("num_turns"),
        "permission_denials": final.get("permission_denials") or [],
        "usage": final.get("usage"),
    }


def parse_codex_output(stdout_path: Path, last_message: Path) -> dict[str, Any]:
    thread_id = None
    errors: list[str] = []
    usage = None
    for line in stdout_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = data.get("type")
        if kind == "thread.started":
            thread_id = data.get("thread_id")
        elif kind == "error":
            errors.append(str(data.get("message")))
        elif kind == "turn.failed":
            errors.append(json.dumps(data.get("error")))
        elif kind == "turn.completed":
            usage = data.get("usage")
    result = None
    if last_message.is_file():
        text = last_message.read_text(encoding="utf-8").strip()
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            result = None
    return {
        "parsed": result is not None or thread_id is not None,
        "result": result,
        "thread_id": thread_id,
        "is_error": bool(errors),
        "errors": errors,
        "usage": usage,
    }


REQUIRED_RESULT_KEYS = ("status", "scope", "files", "evidence", "risks", "handoff", "verdict", "blocked_reason")


def result_valid(result: Any) -> list[str]:
    if not isinstance(result, dict):
        return ["result is not an object"]
    problems = [f"missing {key}" for key in REQUIRED_RESULT_KEYS if key not in result]
    if result.get("status") not in {"complete", "blocked", "failed"}:
        problems.append("status must be complete|blocked|failed")
    if result.get("verdict") not in {"PASS", "FAIL", "N/A"}:
        problems.append("verdict must be PASS|FAIL|N/A")
    return problems


def collect_lane(record: dict[str, Any], exit_code: int | None) -> dict[str, Any]:
    attempt_dir = Path(record["attempt_dir"])
    stdout_path = attempt_dir / "stdout.jsonl"
    if record["platform"] == "claude":
        parsed = parse_claude_output(stdout_path)
        if parsed.get("session_id"):
            record["session_id"] = parsed["session_id"]
    else:
        parsed = parse_codex_output(stdout_path, attempt_dir / "last-message.json")
        if parsed.get("thread_id"):
            record["thread_id"] = parsed["thread_id"]
    record["exit_code"] = exit_code
    record["ended_at"] = now_iso()
    record["session_log"] = find_session_log(record)
    record["cost_usd"] = parsed.get("cost_usd")
    record["usage"] = parsed.get("usage")
    record["permission_denials"] = parsed.get("permission_denials") or []
    record["runner_errors"] = parsed.get("errors") or []
    result = parsed.get("result")
    problems = result_valid(result)
    record["result"] = result if not problems else None
    record["result_problems"] = problems

    if record.get("worktree_path") and Path(record["worktree_path"]).is_dir():
        wt = Path(record["worktree_path"])
        record["head_sha"] = run_git(wt, ["rev-parse", "HEAD"], check=False).stdout.strip() or None
        record["dirty_paths"] = dirty_paths(wt)

    if exit_code not in (0, None) or parsed.get("is_error") or problems:
        record["status"] = "failed"
    else:
        record["status"] = result["status"]
        if record.get("write") and record["status"] == "complete" and record.get("dirty_paths"):
            record["status"] = "failed"
            record["result_problems"] = ["write lane returned complete with uncommitted changes"]
    return record


# --------------------------------------------------------------------------- cancel


def kill_lane(record: dict[str, Any]) -> bool:
    pgid = record.get("pgid")
    if not pgid or not pid_alive(record.get("pid")):
        return False
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return False
    deadline = time.time() + CANCEL_GRACE_SECONDS
    while time.time() < deadline and pid_alive(record.get("pid")):
        time.sleep(0.5)
    if pid_alive(record.get("pid")):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    record["status"] = "cancelled"
    record["ended_at"] = now_iso()
    return True


# --------------------------------------------------------------------------- CLI helpers


def resolve_repo(args: argparse.Namespace, plan: dict[str, Any] | None = None) -> Path:
    if getattr(args, "repo", None):
        return git_root(Path(args.repo).expanduser())
    if plan and plan.get("repo"):
        return git_root(Path(plan["repo"]).expanduser())
    return git_root(Path.cwd())


def resolve_worktree_root(args: argparse.Namespace, config: dict[str, Any]) -> Path | None:
    if getattr(args, "worktree_root", None):
        return Path(args.worktree_root).expanduser().resolve(strict=False)
    value = config.get("worktree_root")
    return Path(value).expanduser().resolve(strict=False) if value else None


def load_validated_plan(path: str) -> dict[str, Any]:
    plan = load_plan(Path(path).expanduser())
    errors, _ = validate_plan(plan)
    if errors:
        raise SystemExit("invalid lane plan:\n- " + "\n- ".join(errors))
    return plan


def public_record(lane_id: str, record: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "status", "role", "mode", "platform", "write", "advisory", "attempts", "branch",
        "worktree_path", "head_sha", "dirty_paths", "exit_code", "session_id", "thread_id",
        "session_log", "cost_usd", "result", "result_problems", "permission_denials",
        "runner_errors", "started_at", "ended_at", "attempt_dir",
    )
    return {"lane": lane_id, **{k: record.get(k) for k in keys}}


def elapsed(record: dict[str, Any]) -> str:
    start = record.get("started_at")
    if not start:
        return "-"
    begin = time.mktime(time.strptime(start, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    end_value = record.get("ended_at")
    end = time.mktime(time.strptime(end_value, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone if end_value else time.time()
    seconds = int(max(0, end - begin))
    return f"{seconds // 60}m{seconds % 60:02d}s"


def print_status_table(state: dict[str, Any]) -> None:
    rows = [("lane", "status", "mode", "platform", "att", "verdict", "elapsed", "branch", "head")]
    for lane_id in state.get("lane_order") or sorted(state.get("lanes", {})):
        record = state["lanes"].get(lane_id)
        if not record:
            rows.append((lane_id, "planned", "-", "-", "0", "-", "-", "-", "-"))
            continue
        status = record.get("status", "?")
        if status == "running" and not pid_alive(record.get("pid")):
            status = "running?"  # process gone, not yet collected
        verdict = (record.get("result") or {}).get("verdict", "-") if record.get("result") else "-"
        rows.append(
            (
                lane_id,
                status,
                record.get("mode", "-"),
                record.get("platform", "-"),
                str(record.get("attempts", 0)),
                verdict,
                elapsed(record),
                record.get("branch") or "-",
                (record.get("head_sha") or "-")[:10],
            )
        )
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for row in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


# --------------------------------------------------------------------------- commands


def command_spawn(args: argparse.Namespace) -> int:
    ensure_not_nested()
    plan = load_validated_plan(args.plan)
    repo = resolve_repo(args, plan)
    config = runtime_config(args)
    state_root = Path(args.state_root).expanduser()
    state = load_task_state(state_root, repo, plan["task"])
    state["plan_path"] = str(Path(args.plan).expanduser().resolve())
    max_parallel = plan.get("max_parallel") or config.get("max_parallel") or DEFAULT_MAX_PARALLEL
    if running_count(state) >= max_parallel:
        raise SystemExit(f"max_parallel={max_parallel} reached; wait for a lane to finish")
    lane = lane_by_id(plan, args.lane)
    if lane.get("mode") != "session":
        raise SystemExit(f"lane {args.lane} is a subagent lane; run it in-process, not as a session")
    for dep in lane.get("depends_on") or []:
        if state["lanes"].get(dep, {}).get("status") != "complete":
            raise SystemExit(f"dependency '{dep}' of lane {args.lane} is not complete")
    record, _ = spawn_lane(
        plan,
        lane,
        repo=repo,
        config=config,
        state_root=state_root,
        state=state,
        worktree_root=resolve_worktree_root(args, config),
        follow_up=args.follow_up,
        resume=args.resume,
    )
    print(json.dumps(public_record(args.lane, record) | {"pid": record["pid"]}, ensure_ascii=False, indent=2))
    return 0


def wait_for_records(
    state_root: Path,
    repo: Path,
    task: str,
    lane_ids: list[str],
    *,
    timeout: float | None,
    processes: dict[str, subprocess.Popen[bytes]] | None = None,
) -> dict[str, Any]:
    started = time.time()
    state = load_task_state(state_root, repo, task)
    pending = set(lane_ids)
    while pending:
        state = load_task_state(state_root, repo, task)
        for lane_id in sorted(pending):
            record = state["lanes"].get(lane_id)
            if not record:
                pending.discard(lane_id)
                continue
            if record.get("status") != "running":
                pending.discard(lane_id)
                continue
            proc = (processes or {}).get(lane_id)
            if proc is not None:
                code = proc.poll()
                if code is None:
                    lane_timeout = record.get("timeout_seconds")
                    if lane_timeout and time.time() - started > lane_timeout:
                        kill_lane(record)
                        record["result_problems"] = [f"timeout after {lane_timeout}s"]
                        save_task_state(state_root, repo, task, state)
                        pending.discard(lane_id)
                    continue
                collect_lane(record, code)
            else:
                if pid_alive(record.get("pid")):
                    continue
                collect_lane(record, record.get("exit_code"))
            save_task_state(state_root, repo, task, state)
            pending.discard(lane_id)
        if pending:
            if timeout and time.time() - started > timeout:
                break
            time.sleep(POLL_SECONDS)
    return state


def command_wait(args: argparse.Namespace) -> int:
    repo = resolve_repo(args)
    state_root = Path(args.state_root).expanduser()
    state = load_task_state(state_root, repo, args.task)
    lane_ids = args.lane or [lid for lid, rec in state["lanes"].items() if rec.get("status") == "running"]
    state = wait_for_records(state_root, repo, args.task, lane_ids, timeout=args.timeout)
    records = [public_record(lid, state["lanes"][lid]) for lid in lane_ids if lid in state["lanes"]]
    print(json.dumps({"task": args.task, "lanes": records}, ensure_ascii=False, indent=2))
    return 0 if all(r["status"] == "complete" for r in records) else 1


def command_run(args: argparse.Namespace) -> int:
    ensure_not_nested()
    plan = load_validated_plan(args.plan)
    _, waves = validate_plan(plan)
    repo = resolve_repo(args, plan)
    config = runtime_config(args)
    state_root = Path(args.state_root).expanduser()
    task = plan["task"]
    state = load_task_state(state_root, repo, task)
    state["plan_path"] = str(Path(args.plan).expanduser().resolve())
    max_parallel = plan.get("max_parallel") or config.get("max_parallel") or DEFAULT_MAX_PARALLEL
    worktree_root = resolve_worktree_root(args, config)

    if args.wave is not None:
        if args.wave >= len(waves):
            raise SystemExit(f"wave {args.wave} does not exist; plan has {len(waves)} waves")
        selected = list(waves[args.wave])
    elif args.lane:
        selected = list(args.lane)
    else:
        selected = [lane["id"] for lane in plan["lanes"]]
    selected = [lid for lid in selected if lane_by_id(plan, lid).get("mode") == "session"]
    if not selected:
        raise SystemExit("no session lanes selected")

    processes: dict[str, subprocess.Popen[bytes]] = {}
    pending = list(selected)

    def shutdown(signum: int, _frame: Any) -> None:
        current = load_task_state(state_root, repo, task)
        for lane_id in list(processes):
            record = current["lanes"].get(lane_id)
            if record:
                kill_lane(record)
        save_task_state(state_root, repo, task, current)
        sys.stderr.write(f"\nrun interrupted by signal {signum}; lanes cancelled, worktrees preserved\n")
        raise SystemExit(130)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while pending or processes:
        state = load_task_state(state_root, repo, task)
        progressed = False
        for lane_id in list(pending):
            if len(processes) + running_count({"lanes": {k: v for k, v in state["lanes"].items() if k not in processes}}) >= max_parallel:
                break
            lane = lane_by_id(plan, lane_id)
            deps = lane.get("depends_on") or []
            dep_status = {dep: state["lanes"].get(dep, {}).get("status") for dep in deps}
            if any(s in {"failed", "blocked", "cancelled", "skipped"} for s in dep_status.values()):
                blocked_by = [d for d, s in dep_status.items() if s in {"failed", "blocked", "cancelled", "skipped"}]
                state["lanes"][lane_id] = {
                    **(state["lanes"].get(lane_id) or {"attempts": 0}),
                    "status": "skipped",
                    "result_problems": [f"dependency not complete: {', '.join(blocked_by)}"],
                    "platform": lane["platform"], "mode": lane["mode"], "role": lane["role"],
                }
                save_task_state(state_root, repo, task, state)
                pending.remove(lane_id)
                progressed = True
                continue
            if not all(s == "complete" for s in dep_status.values()):
                continue  # wait for dependency
            record, proc = spawn_lane(
                plan, lane, repo=repo, config=config, state_root=state_root, state=state,
                worktree_root=worktree_root, hold=True,
            )
            if proc is not None:
                processes[lane_id] = proc
            pending.remove(lane_id)
            progressed = True
        if processes:
            state = wait_for_records(
                state_root, repo, task, list(processes), timeout=POLL_SECONDS, processes=processes
            )
            for lane_id in list(processes):
                if state["lanes"][lane_id].get("status") != "running":
                    processes.pop(lane_id)
                    progressed = True
        elif pending and not progressed:
            # nothing running and nothing spawnable: dependencies outside this selection are incomplete
            missing = {
                lid: [d for d in (lane_by_id(plan, lid).get("depends_on") or [])
                      if state["lanes"].get(d, {}).get("status") != "complete"]
                for lid in pending
            }
            raise SystemExit(f"cannot progress; incomplete dependencies outside selection: {missing}")
        if not progressed and processes:
            time.sleep(POLL_SECONDS)

    state = load_task_state(state_root, repo, task)
    records = [public_record(lid, state["lanes"][lid]) for lid in selected if lid in state["lanes"]]
    ok = all(
        r["status"] == "complete" and (r["advisory"] or (r["result"] or {}).get("verdict") != "FAIL")
        for r in records
    )
    if args.json:
        print(json.dumps({"task": task, "ok": ok, "lanes": records}, ensure_ascii=False, indent=2))
    else:
        print_status_table(state)
    return 0 if ok else 1


def command_status(args: argparse.Namespace) -> int:
    repo = resolve_repo(args)
    state_root = Path(args.state_root).expanduser()
    if args.task:
        state = load_task_state(state_root, repo, args.task)
        if args.json:
            print(json.dumps({"task": args.task, "lanes": [public_record(l, r) for l, r in state["lanes"].items()], "integration": state.get("integration")}, ensure_ascii=False, indent=2))
        else:
            print_status_table(state)
        return 0
    tasks_root = state_root / "tasks" / repo_id(repo)
    found = []
    if tasks_root.is_dir():
        for task_json in sorted(tasks_root.glob("*/task.json")):
            with task_json.open(encoding="utf-8") as stream:
                data = json.load(stream)
            lanes = data.get("lanes", {})
            found.append(
                {
                    "task": data.get("task"),
                    "lanes": len(lanes),
                    "running": sum(1 for r in lanes.values() if r.get("status") == "running" and pid_alive(r.get("pid"))),
                    "worktrees_present": [r["worktree_path"] for r in lanes.values() if r.get("worktree_path") and Path(r["worktree_path"]).is_dir()],
                }
            )
    print(json.dumps({"repo": str(repo), "tasks": found}, ensure_ascii=False, indent=2))
    return 0


def command_cancel(args: argparse.Namespace) -> int:
    repo = resolve_repo(args)
    state_root = Path(args.state_root).expanduser()
    state = load_task_state(state_root, repo, args.task)
    targets = args.lane or list(state["lanes"])
    cancelled = []
    for lane_id in targets:
        record = state["lanes"].get(lane_id)
        if record and kill_lane(record):
            cancelled.append(lane_id)
    save_task_state(state_root, repo, args.task, state)
    print(json.dumps({"task": args.task, "cancelled": cancelled, "worktrees_preserved": True}, ensure_ascii=False))
    return 0


def command_collect(args: argparse.Namespace) -> int:
    repo = resolve_repo(args)
    state_root = Path(args.state_root).expanduser()
    state = load_task_state(state_root, repo, args.task)
    record = state["lanes"].get(args.lane)
    if not record:
        raise SystemExit(f"unknown lane {args.lane}")
    if record.get("status") == "running" and pid_alive(record.get("pid")):
        raise SystemExit(f"lane {args.lane} is still running")
    collect_lane(record, record.get("exit_code"))
    save_task_state(state_root, repo, args.task, state)
    print(json.dumps(public_record(args.lane, record), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run multi-session-dev lane sessions.")
    parser.add_argument("--config", default=str(default_config_path()))
    parser.add_argument("--state-root", default=str(default_state_root()))
    parser.add_argument("--repo")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Spawn selected lanes respecting slots and dependencies, wait, collect")
    run.add_argument("--plan", required=True)
    run.add_argument("--wave", type=int)
    run.add_argument("--lane", action="append")
    run.add_argument("--worktree-root")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=command_run)

    spawn = sub.add_parser("spawn", help="Start one lane in the background")
    spawn.add_argument("--plan", required=True)
    spawn.add_argument("--lane", required=True)
    spawn.add_argument("--worktree-root")
    spawn.add_argument("--follow-up", help="Extra Lead instructions for a retry attempt")
    spawn.add_argument("--resume", action="store_true", help="Resume the lane's previous session")
    spawn.set_defaults(func=command_spawn)

    wait = sub.add_parser("wait")
    wait.add_argument("--task", required=True)
    wait.add_argument("--lane", action="append")
    wait.add_argument("--timeout", type=float)
    wait.set_defaults(func=command_wait)

    status = sub.add_parser("status")
    status.add_argument("--task")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_status)

    cancel = sub.add_parser("cancel")
    cancel.add_argument("--task", required=True)
    cancel.add_argument("--lane", action="append")
    cancel.set_defaults(func=command_cancel)

    collect = sub.add_parser("collect")
    collect.add_argument("--task", required=True)
    collect.add_argument("--lane", required=True)
    collect.set_defaults(func=command_collect)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
