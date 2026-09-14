import contextlib
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("task_metrics", ROOT / "scripts" / "task_metrics.py")
METRICS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(METRICS)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
END = START + timedelta(minutes=10)


def moment(seconds=1):
    return METRICS.iso(START + timedelta(seconds=seconds))


def claude(seconds=1, message_id="message-a", request="request-a", **usage):
    return {"type": "assistant", "timestamp": moment(seconds), "requestId": request,
            "message": {"id": message_id, "model": "model-a", "usage": usage,
                        "content": [{"type": "text", "text": "PRIVATE TRANSCRIPT CONTENT"}]}}


def codex(seconds=1, last=None, total=None):
    return {"type": "event_msg", "timestamp": moment(seconds),
            "payload": {"type": "token_count", "info": {
                "last_token_usage": last, "total_token_usage": total}}}


class TaskMetricsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="task-metrics-test-")
        self.root = Path(self.temporary.name)
        self.environment = patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root / "state")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def source(self, provider, rows, filename="session.jsonl"):
        path = self.root / filename
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        return {"provider": provider, "path": str(path)}

    def scan(self, sources):
        return METRICS.scan_usage(sources, START, END)

    def run_cli(self, *arguments, expected=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = METRICS.main(list(arguments))
        self.assertEqual(code, expected, stderr.getvalue())
        return json.loads(stdout.getvalue()) if code == 0 else stderr.getvalue()

    def test_claude_streams_merge_final_maxima_and_count_all_input_classes(self):
        source = self.source("claude", [
            claude(input_tokens=10, cache_read_input_tokens=90,
                   cache_creation_input_tokens=20, output_tokens=1),
            claude(seconds=2, output_tokens=7),
            claude(seconds=3, input_tokens=10, cache_read_input_tokens=90,
                   cache_creation_input_tokens=20, output_tokens=7),
        ])
        result = self.scan([source])
        self.assertEqual(result["calls"], 1)
        self.assertEqual(result["tokens"]["input_tokens"]["value"], 120)
        self.assertEqual(result["tokens"]["output_tokens"]["value"], 7)
        self.assertEqual(result["diagnostics"]["duplicate_snapshots"], 2)

    def test_claude_request_identity_distinguishes_messages(self):
        source = self.source("claude", [claude(output_tokens=2),
                                          claude(request="request-b", output_tokens=3)])
        self.assertEqual(self.scan([source])["tokens"]["output_tokens"]["value"], 5)

    def test_missing_claude_cache_write_is_unknown_not_zero(self):
        result = self.scan([self.source("claude", [
            claude(input_tokens=10, cache_read_input_tokens=90, output_tokens=0)])])
        self.assertIsNone(result["tokens"]["cache_write_tokens"]["value"])
        self.assertIsNone(result["tokens"]["input_tokens"]["value"])
        self.assertEqual(result["tokens"]["output_tokens"]["value"], 0)
        self.assertEqual(result["tokens"]["output_tokens"]["coverage"], "reported")

    def test_partially_reported_fields_are_marked(self):
        result = self.scan([self.source("claude", [
            claude(input_tokens=10, cache_read_input_tokens=0, cache_creation_input_tokens=0),
            claude(message_id="other", input_tokens=10)])])
        field = result["tokens"]["input_tokens"]
        self.assertEqual(field, {"value": 10, "coverage": "partial",
                                 "reported_calls": 1, "unreported_calls": 1})

    def test_task_window_excludes_both_before_and_after(self):
        result = self.scan([self.source("claude", [
            claude(seconds=-1, message_id="before", output_tokens=100),
            claude(seconds=1, message_id="during", output_tokens=7),
            claude(seconds=601, message_id="after", output_tokens=100),
        ])])
        self.assertEqual(result["calls"], 1)
        self.assertEqual(result["tokens"]["output_tokens"]["value"], 7)

    def test_codex_uses_last_usage_and_skips_repeated_cumulative_snapshots(self):
        last = {"input_tokens": 100, "cached_input_tokens": 90, "output_tokens": 4,
                "reasoning_output_tokens": 2, "total_tokens": 104}
        total = {"input_tokens": 1000, "cached_input_tokens": 900, "output_tokens": 40,
                 "reasoning_output_tokens": 20, "total_tokens": 1040}
        result = self.scan([self.source("codex", [
            {"type": "turn_context", "payload": {"model": "model-b"}},
            codex(last=last, total=total), codex(seconds=2, last=last, total=total),
        ])])
        self.assertEqual(result["calls"], 1)
        self.assertEqual(result["tokens"]["input_tokens"]["value"], 100)
        self.assertIsNone(result["tokens"]["fresh_input_tokens"]["value"])
        self.assertEqual(result["tokens"]["output_tokens"]["value"], 4)
        self.assertIsNone(result["tokens"]["cache_write_tokens"]["value"])
        self.assertEqual(result["by_model"][0]["model"], "model-b")

    def test_native_codex_cache_write_and_claude_thinking_counters(self):
        result = self.scan([
            self.source("codex", [codex(last={"input_tokens": 100, "cached_input_tokens": 80,
                                               "cache_write_input_tokens": 10, "output_tokens": 20,
                                               "reasoning_output_tokens": 5},
                                         total={"total_tokens": 120})], "codex.jsonl"),
            self.source("claude", [claude(input_tokens=4, cache_read_input_tokens=50,
                                           cache_creation_input_tokens=6, output_tokens=9,
                                           output_tokens_details={"thinking_tokens": 3})], "claude.jsonl"),
        ])
        self.assertEqual(result["tokens"]["input_tokens"]["value"], 160)
        self.assertEqual(result["tokens"]["fresh_input_tokens"]["value"], 14)
        self.assertEqual(result["tokens"]["cache_write_tokens"]["value"], 16)
        self.assertEqual(result["tokens"]["reasoning_output_tokens"]["value"], 8)

    def test_codex_repeated_total_can_complete_partial_last_fields(self):
        result = self.scan([self.source("codex", [
            codex(last={"input_tokens": 30}, total={"total_tokens": 34}),
            codex(seconds=2, last={"input_tokens": 30, "cached_input_tokens": 20,
                                   "cache_write_input_tokens": 2, "output_tokens": 4},
                  total={"total_tokens": 34}),
        ])])
        self.assertEqual(result["calls"], 1)
        self.assertEqual(result["tokens"]["output_tokens"]["value"], 4)
        self.assertEqual(result["tokens"]["fresh_input_tokens"]["value"], 8)

    def test_codex_fresh_input_recomputed_after_cache_snapshot_recovers(self):
        result = self.scan([self.source("codex", [
            codex(last={"input_tokens": 30, "cached_input_tokens": 0,
                        "cache_write_input_tokens": 0}, total={"total_tokens": 34}),
            codex(seconds=2, last={"input_tokens": 30, "cached_input_tokens": 20,
                                   "cache_write_input_tokens": 2, "output_tokens": 4},
                  total={"total_tokens": 34}),
        ])])
        self.assertEqual(result["tokens"]["fresh_input_tokens"]["value"], 8)

    def test_codex_pre_task_snapshot_prevents_counting_stale_last_usage(self):
        last, total = {"input_tokens": 30}, {"total_tokens": 90}
        result = self.scan([self.source("codex", [
            codex(seconds=-1, last=last, total=total),
            codex(seconds=1, last=last, total=total),
            codex(seconds=2, last={"input_tokens": 4}, total={"total_tokens": 94}),
        ])])
        self.assertEqual(result["calls"], 1)
        self.assertEqual(result["tokens"]["input_tokens"]["value"], 4)

    def test_codex_copied_fork_records_deduplicate_across_sources(self):
        inherited = codex(last={"input_tokens": 30}, total={"total_tokens": 90})
        parent = self.source("codex", [inherited], "parent.jsonl")
        child = self.source("codex", [
            {"type": "session_meta", "payload": {"id": "child", "forked_from_id": "parent"}},
            inherited, codex(seconds=2, last={"input_tokens": 4}, total={"total_tokens": 94}),
        ], "child.jsonl")
        result = self.scan([parent, child])
        self.assertEqual(result["calls"], 2)
        self.assertEqual(result["tokens"]["input_tokens"]["value"], 34)

    def test_codex_totals_without_last_are_not_counted_as_calls(self):
        result = self.scan([self.source("codex", [codex(total={"total_tokens": 50000})])])
        self.assertEqual(result["calls"], 0)
        self.assertEqual(result["status"], "unknown")
        self.assertIsNone(result["tokens"]["input_tokens"]["value"])
        self.assertEqual(result["diagnostics"]["missing_per_call_usage"], 1)

    def test_codex_delayed_last_usage_is_not_dropped_by_total_only_snapshot(self):
        result = self.scan([self.source("codex", [
            codex(total={"total_tokens": 90}),
            codex(seconds=2, last={"input_tokens": 30}, total={"total_tokens": 90}),
        ])])
        self.assertEqual(result["calls"], 1)
        self.assertEqual(result["tokens"]["input_tokens"]["value"], 30)

    def test_codex_counter_reset_does_not_subtract_or_reuse_cumulative_totals(self):
        result = self.scan([self.source("codex", [
            codex(last={"input_tokens": 3}, total={"total_tokens": 100}),
            codex(seconds=2, last={"input_tokens": 4}, total={"total_tokens": 4}),
        ])])
        self.assertEqual(result["tokens"]["input_tokens"]["value"], 7)
        self.assertEqual(result["diagnostics"]["counter_resets"], 1)

    def test_missing_invalid_counts_remain_unknown(self):
        result = self.scan([self.source("claude", [
            claude(input_tokens=-1, output_tokens=True, cache_read_input_tokens="10")])])
        for field in METRICS.FIELDS:
            self.assertIsNone(result["tokens"][field]["value"])

    def test_malformed_truncated_oversized_and_unreadable_logs_are_partial(self):
        source = self.source("claude", [claude(output_tokens=4)])
        with open(source["path"], "ab") as output:
            output.write(b"not json\n")
            output.write(b"x" * (METRICS.MAX_LINE_BYTES + 5) + b"\n")
            output.write(b'{"truncated":')
        result = self.scan([source, {"provider": "codex", "path": str(self.root / "missing")}])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["diagnostics"]["malformed_lines"], 2)
        self.assertEqual(result["diagnostics"]["oversized_lines"], 1)
        self.assertEqual(result["diagnostics"]["unreadable_sources"], 1)
        self.assertEqual(result["tokens"]["output_tokens"]["coverage"], "partial")

    def test_unidentifiable_or_untimed_usage_is_not_guessed(self):
        missing_time, missing_id = claude(output_tokens=10), claude(output_tokens=10)
        del missing_time["timestamp"]
        del missing_id["message"]["id"]
        result = self.scan([self.source("claude", [missing_time, missing_id])])
        self.assertEqual(result["calls"], 0)
        self.assertEqual(result["diagnostics"]["missing_timestamps"], 1)
        self.assertEqual(result["diagnostics"]["missing_call_ids"], 1)

    def test_no_sources_is_unknown_with_no_zero_fabrication(self):
        result = self.scan([])
        self.assertEqual(result["status"], "unknown")
        self.assertIsNone(result["tokens"]["input_tokens"]["value"])

    def test_cli_cycle_rereads_explicit_logs_and_redacts_private_text(self):
        primary = self.source("claude", [], "primary.jsonl")
        worker = self.source("codex", [], "worker.jsonl")
        self.source("claude", [claude(output_tokens=9999)], "unrelated.jsonl")
        start = self.run_cli("start", "fix-example", "--project", str(self.root),
                             "--session-log", "claude:" + primary["path"])
        self.run_cli("add-session", "fix-example", "--session-log", "codex:" + worker["path"])
        self.run_cli("add-session", "fix-example", "--session-log", "codex:" + worker["path"])
        native_time = METRICS.iso(METRICS.utc_now())
        row_a = claude(input_tokens=10, cache_read_input_tokens=90,
                       cache_creation_input_tokens=0, output_tokens=4)
        row_a["timestamp"] = native_time
        row_b = codex(last={"input_tokens": 20, "cached_input_tokens": 10, "output_tokens": 2},
                      total={"total_tokens": 10000})
        row_b["timestamp"] = native_time
        Path(primary["path"]).write_text(json.dumps(row_a) + "\n")
        Path(worker["path"]).write_text(json.dumps(row_b) + "\n")
        finish = self.run_cli("finish", "fix-example", "--retries", "1",
                              "--check", "build=pass", "--check", "lint=pass", "--check", "test=fail")
        self.assertEqual(finish["usage"]["tokens"]["input_tokens"]["value"], 120)
        self.assertEqual(finish["usage"]["tokens"]["output_tokens"]["value"], 6)
        self.assertEqual(finish["usage"]["explicit_sources"], 2)
        self.assertEqual(finish["retries"], 1)
        self.assertEqual(finish["retries_source"], "manual")
        self.assertEqual(finish["checks"], {"build": "pass", "lint": "pass", "test": "fail"})
        self.assertGreaterEqual(finish["elapsed_wall_seconds"], 0)
        self.assertEqual(start["project_id"], finish["project_id"])
        self.assertEqual(finish, self.run_cli("report", "fix-example"))
        serialized = json.dumps(finish)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("PRIVATE TRANSCRIPT CONTENT", serialized)
        state = METRICS.state_root() / "fix-example.json"
        self.assertNotIn("PRIVATE TRANSCRIPT CONTENT", state.read_text())
        self.assertEqual(stat.S_IMODE(state.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(state.parent.stat().st_mode), 0o700)

    def test_cli_omitted_results_are_unknown_and_not_run(self):
        self.run_cli("start", "example")
        result = self.run_cli("finish", "example")
        self.assertIsNone(result["retries"])
        self.assertEqual(result["retries_source"], "unknown")
        self.assertEqual(set(result["checks"].values()), {"not-run"})
        self.assertEqual(result["usage"]["status"], "unknown")

    def test_duplicate_start_finish_and_late_attachment_are_rejected(self):
        self.run_cli("start", "example")
        self.assertIn("already exists", self.run_cli("start", "example", expected=2))
        self.run_cli("finish", "example")
        self.assertIn("already finished", self.run_cli("finish", "example", expected=2))
        self.assertIn("already finished", self.run_cli("add-session", "example",
                      "--session-log", "codex:missing.jsonl", expected=2))

    def test_lock_contention_fails_safely_without_lost_writes(self):
        root = METRICS.state_root()
        with METRICS.state_lock(root):
            result = subprocess.run([sys_executable(), str(ROOT / "scripts" / "task_metrics.py"),
                                     "start", "contended"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("another task-metrics command", result.stderr)
        self.assertFalse((root / "contended.json").exists())

    def test_task_traversal_and_invalid_args_rejected_before_state_creation(self):
        for arguments in (("start", "../escape"), ("start", "/absolute"),
                          ("finish", "example", "--retries", "-1"),
                          ("finish", "example", "--check", "build=maybe"),
                          ("start", "example", "--session-log", "other:/tmp/example")):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    METRICS.main(list(arguments))
                self.assertEqual(caught.exception.code, 2)
        self.assertFalse((self.root / "state").exists())

    def test_state_symlink_and_task_symlink_are_rejected(self):
        root = METRICS.state_root()
        outside = self.root / "outside.json"
        outside.write_text("do not change")
        (root / "example.json").symlink_to(outside)
        self.run_cli("report", "example", expected=2)
        self.run_cli("start", "example", expected=2)
        self.assertEqual(outside.read_text(), "do not change")

    def test_record_limit_marks_partial_measurement(self):
        with patch.object(METRICS, "MAX_CALLS", 1):
            result = self.scan([self.source("claude", [
                claude(output_tokens=4), claude(message_id="second", output_tokens=9)])])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["diagnostics"]["record_limit_reached"], 1)

    def test_pre_task_codex_snapshot_memory_is_also_bounded(self):
        with patch.object(METRICS, "MAX_CALLS", 1):
            result = self.scan([self.source("codex", [
                codex(seconds=-3, last={"input_tokens": 1}, total={"total_tokens": 1}),
                codex(seconds=-2, last={"input_tokens": 1}, total={"total_tokens": 2}),
            ])])
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["diagnostics"]["record_limit_reached"], 1)

    def test_named_pipe_source_is_rejected_without_blocking(self):
        path = self.root / "pipe.jsonl"
        os.mkfifo(path)
        result = self.scan([{"provider": "codex", "path": str(path)}])
        self.assertEqual(result["diagnostics"]["unreadable_sources"], 1)

    def test_corrupted_state_is_rejected_without_traceback(self):
        self.run_cli("start", "example")
        path = METRICS.state_root() / "example.json"
        task = json.loads(path.read_text())
        task["sources"] = [None]
        path.write_text(json.dumps(task))
        self.assertIn("invalid task state", self.run_cli("report", "example", expected=2))


def sys_executable():
    import sys
    return sys.executable


if __name__ == "__main__":
    unittest.main()
