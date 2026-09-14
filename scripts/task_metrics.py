#!/usr/bin/env python3
"""Explicit-session, machine-local task measurements (standard library, no network)."""

import argparse
import contextlib
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile


SLUG = re.compile(r"[a-z0-9][a-z0-9_-]{0,79}\Z")
MODEL = re.compile(r"[A-Za-z0-9._:/-]{1,120}\Z")
MAX_LINE_BYTES = 2 * 1024 * 1024
MAX_CALLS = 100_000
MAX_STATE_BYTES = 2 * 1024 * 1024
FIELDS = ("input_tokens", "fresh_input_tokens", "cache_read_tokens",
          "cache_write_tokens", "output_tokens", "reasoning_output_tokens")


def utc_now():
    return datetime.now(timezone.utc)


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fingerprint(value):
    return hashlib.sha256(value.encode()).hexdigest()


def count(value):
    return value if type(value) is int and value >= 0 else None


def model_name(value):
    return value if isinstance(value, str) and MODEL.fullmatch(value) else "unknown"


def object_value(value):
    return value if isinstance(value, dict) else {}


def native_rows(path, diagnostics):
    """Stream JSONL without loading a transcript or retaining its text."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                diagnostics["unreadable_sources"] += 1
                return
            while True:
                line = source.readline(MAX_LINE_BYTES + 1)
                if not line:
                    break
                if len(line) > MAX_LINE_BYTES:
                    while line and not line.endswith(b"\n"):
                        line = source.readline(MAX_LINE_BYTES + 1)
                    diagnostics["oversized_lines"] += 1
                    continue
                try:
                    row = json.loads(line)
                    if isinstance(row, dict):
                        yield row
                    else:
                        diagnostics["malformed_lines"] += 1
                except (ValueError, UnicodeError, RecursionError):
                    diagnostics["malformed_lines"] += 1
    except OSError:
        # Do not print paths, source text, or operating-system exception details.
        diagnostics["unreadable_sources"] += 1


def new_diagnostics():
    return dict.fromkeys(("malformed_lines", "oversized_lines", "unreadable_sources",
                          "missing_timestamps", "missing_call_ids", "missing_per_call_usage",
                          "duplicate_snapshots", "counter_resets", "record_limit_reached"), 0)


def merge_usage(old, new):
    for field in FIELDS:
        value = new.get(field)
        if value is not None:
            old[field] = max(old.get(field) or 0, value)


def claude_usage(usage):
    fresh = count(usage.get("input_tokens"))
    read = count(usage.get("cache_read_input_tokens"))
    write = count(usage.get("cache_creation_input_tokens"))
    return {"fresh_input_tokens": fresh, "cache_read_tokens": read,
            "cache_write_tokens": write, "output_tokens": count(usage.get("output_tokens")),
            "reasoning_output_tokens": count(object_value(usage.get("output_tokens_details"))
                                              .get("thinking_tokens"))}


def codex_usage(usage):
    total = count(usage.get("input_tokens"))
    read = count(usage.get("cached_input_tokens"))
    write = count(usage.get("cache_write_input_tokens"))
    if write is None:
        write = count(usage.get("cache_creation_input_tokens"))
    fresh = (total - read - write if all(value is not None for value in (total, read, write))
             and total >= read + write else None)
    return {"input_tokens": total, "fresh_input_tokens": fresh, "cache_read_tokens": read,
            "cache_write_tokens": write,
            "output_tokens": count(usage.get("output_tokens")),
            "reasoning_output_tokens": count(usage.get("reasoning_output_tokens"))}


def scan_usage(sources, started, ended):
    """Attribute only explicit sources and timestamped calls within the task window.

    Claude streaming updates are merged by request/message identity. Codex's last
    usage is per-call; total usage is used only as a duplicate/reset marker.
    """
    calls = {}
    diagnostics = new_diagnostics()
    source_ids = []
    for source in sources:
        provider, path = source["provider"], source["path"]
        source_ids.append(fingerprint(provider + ":" + path))
        seen_totals = set()
        total_calls = {}
        previous_total = None
        current_model = "unknown"
        for row in native_rows(path, diagnostics):
            payload = object_value(row.get("payload"))
            if provider == "codex" and row.get("type") == "turn_context":
                current_model = model_name(payload.get("model"))
            if provider == "claude":
                message = object_value(row.get("message"))
                usage = message.get("usage")
                if row.get("type") != "assistant" or not isinstance(usage, dict):
                    continue
                moment = timestamp(row.get("timestamp"))
                if moment is None:
                    diagnostics["missing_timestamps"] += 1
                    continue
                if not started <= moment <= ended:
                    continue
                message_id = message.get("id")
                if not isinstance(message_id, str) or not message_id:
                    diagnostics["missing_call_ids"] += 1
                    continue
                request_id = row.get("requestId") or ""
                key = ("claude", fingerprint(str(request_id) + ":" + message_id))
                parsed = claude_usage(usage)
                model = model_name(message.get("model"))
            else:
                if row.get("type") != "event_msg" or payload.get("type") != "token_count":
                    continue
                info = object_value(payload.get("info"))
                if not info:  # Rate-limit-only events contain no usage snapshot.
                    continue
                moment = timestamp(row.get("timestamp"))
                total = object_value(info.get("total_token_usage"))
                total_values = {k: count(total.get(k)) for k in
                                ("input_tokens", "cached_input_tokens", "output_tokens",
                                 "reasoning_output_tokens", "total_tokens")}
                total_key = tuple(total_values.values())
                has_total = any(value is not None for value in total_key)
                repeated = has_total and total_key in seen_totals
                if has_total:
                    observed_total = total_values["total_tokens"]
                    if (observed_total is not None and previous_total is not None
                            and observed_total < previous_total):
                        # A new counter epoch may follow compaction; do not infer deltas.
                        diagnostics["counter_resets"] += 1
                        seen_totals.clear()
                        total_calls.clear()
                        repeated = False
                    if observed_total is not None:
                        previous_total = observed_total
                    if len(seen_totals) >= MAX_CALLS and total_key not in seen_totals:
                        diagnostics["record_limit_reached"] += 1
                        break
                if moment is None:
                    diagnostics["missing_timestamps"] += 1
                    continue
                if not started <= moment <= ended:
                    if has_total:
                        seen_totals.add(total_key)
                    continue
                if repeated:
                    diagnostics["duplicate_snapshots"] += 1
                    previous_key = total_calls.get(total_key)
                    if previous_key is not None and isinstance(info.get("last_token_usage"), dict):
                        merge_usage(calls[previous_key]["usage"], codex_usage(info["last_token_usage"]))
                    continue
                usage = info.get("last_token_usage")
                if not isinstance(usage, dict) or not usage:
                    diagnostics["missing_per_call_usage"] += 1
                    continue
                if has_total:
                    seen_totals.add(total_key)
                parsed = codex_usage(usage)
                # Copied/forked native records retain timestamp and usage. Dedup
                # these across explicit sources without guessing by cwd or time.
                identity = json.dumps([iso(moment), total_values if has_total else parsed], sort_keys=True)
                key = ("codex", fingerprint(identity))
                model = current_model
            if key in calls:
                diagnostics["duplicate_snapshots"] += 1
                merge_usage(calls[key]["usage"], parsed)
                if calls[key]["model"] == "unknown":
                    calls[key]["model"] = model
            elif len(calls) >= MAX_CALLS:
                diagnostics["record_limit_reached"] += 1
                break
            else:
                calls[key] = {"provider": provider, "model": model, "usage": parsed}
            if provider == "codex" and has_total:
                total_calls[total_key] = key
    for call in calls.values():
        if call["provider"] == "claude":
            usage = call["usage"]
            components = [usage.get(k) for k in
                          ("fresh_input_tokens", "cache_read_tokens", "cache_write_tokens")]
            usage["input_tokens"] = sum(components) if all(v is not None for v in components) else None
        else:
            usage = call["usage"]
            total, read, write = (usage.get(k) for k in
                                  ("input_tokens", "cache_read_tokens", "cache_write_tokens"))
            usage["fresh_input_tokens"] = (
                total - read - write if all(value is not None for value in (total, read, write))
                and total >= read + write else None)
    incomplete = any(diagnostics[k] for k in diagnostics if k not in
                     ("duplicate_snapshots", "counter_resets"))
    groups = {}
    for call in calls.values():
        groups.setdefault((call["provider"], call["model"]), []).append(call["usage"])

    def aggregate(usages):
        result = {}
        for field in FIELDS:
            known = [item[field] for item in usages if item.get(field) is not None]
            result[field] = {
                "value": sum(known) if known else None,
                "coverage": ("unknown" if not known else
                             "partial" if incomplete or len(known) < len(usages) else "reported"),
                "reported_calls": len(known), "unreported_calls": len(usages) - len(known),
            }
        return result

    return {"status": "unknown" if not calls else "partial" if incomplete else "reported",
            "calls": len(calls), "explicit_sources": len(sources), "source_ids": source_ids,
            "tokens": aggregate([call["usage"] for call in calls.values()]),
            "by_model": [{"provider": provider, "model": model, "calls": len(usages),
                          "tokens": aggregate(usages)}
                         for (provider, model), usages in sorted(groups.items())],
            "diagnostics": diagnostics}


def source_argument(value):
    provider, separator, raw = value.partition(":")
    if separator != ":" or provider not in ("claude", "codex") or not raw:
        raise argparse.ArgumentTypeError("use claude:/path/to/session.jsonl or codex:/path/to/session.jsonl")
    return {"provider": provider, "path": str(Path(raw).expanduser().resolve())}


def check_argument(value):
    name, separator, outcome = value.partition("=")
    if separator != "=" or not SLUG.fullmatch(name) or outcome not in ("pass", "fail", "not-run"):
        raise argparse.ArgumentTypeError("use check-name=pass|fail|not-run")
    return name, outcome


def retries_argument(value):
    try:
        retries = int(value)
        if retries >= 0:
            return retries
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("retries must be a nonnegative integer")


def task_argument(value):
    if not SLUG.fullmatch(value):
        raise argparse.ArgumentTypeError("task must be a 1–80 character lowercase slug (letters, numbers, - or _)")
    return value


def state_root():
    base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))).expanduser()
    if not base.is_absolute():
        raise ValueError("XDG_STATE_HOME must be an absolute path")
    root = base / "ai-working" / "task-metrics"
    if root.is_symlink() or root.parent.is_symlink():
        raise ValueError("state directory must not be a symlink")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    return root


@contextlib.contextmanager
def state_lock(root):
    descriptor = os.open(root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("invalid state lock")
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("another task-metrics command is running; retry when it completes") from error
        yield
    finally:
        os.close(descriptor)


def read_task(path):
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError as error:
        raise ValueError("task does not exist; use start first") from error
    with os.fdopen(descriptor) as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("invalid task state")
        os.fchmod(source.fileno(), 0o600)
        raw = source.read(MAX_STATE_BYTES + 1)
    if len(raw) > MAX_STATE_BYTES:
        raise ValueError("task state exceeds size limit")
    try:
        task = json.loads(raw)
        if (not isinstance(task, dict) or task.get("version") != 1
                or task.get("status") not in ("running", "finished")
                or timestamp(task.get("started_at")) is None
                or not isinstance(task.get("sources"), list)
                or len(task["sources"]) > 100
                or not isinstance(task.get("checks"), dict)
                or "retries" not in task
                or any(not isinstance(source, dict)
                       or source.get("provider") not in ("claude", "codex")
                       or not isinstance(source.get("path"), str)
                       or not Path(source["path"]).is_absolute() for source in task["sources"])
                or (task["status"] == "finished" and
                    (timestamp(task.get("ended_at")) is None or not isinstance(task.get("usage"), dict)))):
            raise ValueError("invalid task state")
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("invalid task state") from error
    return task


def save_task(path, task):
    descriptor, temporary = tempfile.mkstemp(prefix=".task-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            os.fchmod(output.fileno(), 0o600)
            json.dump(task, output, sort_keys=True, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def attach_sources(task, sources):
    for source in sources:
        if source not in task["sources"]:
            if len(task["sources"]) >= 100:
                raise ValueError("a task supports at most 100 explicit session logs")
            task["sources"].append(source)


def report(task):
    # Paths are operational references stored privately, never printed in reports.
    result = {k: v for k, v in task.items() if k not in ("sources", "project_path")}
    ended = timestamp(task.get("ended_at")) or utc_now()
    started = timestamp(task["started_at"])
    result["elapsed_wall_seconds"] = round(max(0, (ended - started).total_seconds()), 3)
    result["retries_source"] = "manual" if task["retries"] is not None else "unknown"
    if task["status"] == "running":
        result["usage"] = scan_usage(task["sources"], started, ended)
    return result


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("start", "add-session", "finish", "report"):
        command = commands.add_parser(name)
        command.add_argument("task", type=task_argument)
        if name != "report":
            command.add_argument("--session-log", type=source_argument, action="append", default=[],
                                 help="explicit provider:path; repeat for worker sessions")
        if name == "start":
            command.add_argument("--project", type=Path, default=Path.cwd())
        if name == "finish":
            command.add_argument("--retries", type=retries_argument, default=None)
            command.add_argument("--check", type=check_argument, action="append", default=[])
    return root


def main(argv=None):
    arguments = parser().parse_args(argv)
    try:
        root = state_root()
        with state_lock(root):
            path = root / (arguments.task + ".json")
            if arguments.command == "start":
                if path.exists() or path.is_symlink():
                    raise ValueError("task already exists; use a new task slug")
                project = arguments.project.expanduser().resolve()
                if not project.is_dir():
                    raise ValueError("project directory does not exist")
                task = {"version": 1, "task": arguments.task, "status": "running",
                        "project_id": fingerprint(str(project)), "project_path": str(project),
                        "started_at": iso(utc_now()), "ended_at": None, "sources": [],
                        "retries": None, "checks": dict.fromkeys(("build", "lint", "test"), "not-run")}
            else:
                task = read_task(path)
                if arguments.command != "report" and task["status"] != "running":
                    raise ValueError("task is already finished; its measurement is immutable")
            if arguments.command != "report":
                if arguments.command == "add-session" and not arguments.session_log:
                    raise ValueError("add-session requires at least one --session-log")
                attach_sources(task, arguments.session_log)
                if arguments.command == "finish":
                    task["ended_at"] = iso(utc_now())
                    task["retries"] = arguments.retries
                    task["checks"].update(dict(arguments.check))
                    task["usage"] = scan_usage(task["sources"], timestamp(task["started_at"]),
                                               timestamp(task["ended_at"]))
                    task["status"] = "finished"
                save_task(path, task)
            print(json.dumps(report(task), indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError) as error:
        # OSError can contain private paths; emit only a generic error in that case.
        detail = str(error) if isinstance(error, ValueError) else "cannot access local metrics state"
        print("task-metrics: " + detail, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
