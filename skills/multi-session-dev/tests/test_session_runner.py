from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
FAKES = SKILL_ROOT / "tests" / "fakes"


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True, text=True)


class SessionRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="msd-runner-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "sample"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.com")
        (self.repo / "README.md").write_text("# sample\n", encoding="utf-8")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-qm", "initial")
        git(self.repo, "checkout", "-qb", "feat/sample")
        self.state_root = self.root / "state"
        self.worktree_root = self.root / "worktrees"
        self.config = self.root / "config.json"
        for fake in ("claude", "codex"):
            os.chmod(FAKES / fake, 0o755)
        self.config.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "worktree_root": str(self.worktree_root),
                    "platforms": ["claude", "codex"],
                    "max_parallel": 2,
                    "binaries": {"claude": str(FAKES / "claude"), "codex": str(FAKES / "codex")},
                    "role_defaults": {"reviewer": {"claude_model": "opus"}},
                }
            ),
            encoding="utf-8",
        )
        self.log = self.root / "fake.log"
        self.env = {k: v for k, v in os.environ.items() if k != "MULTI_SESSION_DEV_LANE"}
        self.env["MSD_FAKE_LOG"] = str(self.log)
        self.env["CLAUDECODE"] = "1"  # simulate running inside a Claude session

    def tearDown(self) -> None:
        subprocess.run(["git", "-C", str(self.repo), "worktree", "prune"], check=False, capture_output=True)
        self.temp.cleanup()

    def write_plan(self, lanes: list[dict], **extra) -> Path:
        plan = {
            "schema_version": 1,
            "task": "sample",
            "repo": str(self.repo),
            "target_branch": "feat/sample",
            "commit_allowed": True,
            "max_parallel": 2,
            "retry_limit": 1,
            "lanes": lanes,
        }
        plan.update(extra)
        path = self.root / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def runner(self, *args: str, action: str = "complete", check: bool = False, marker: str | None = None):
        env = dict(self.env)
        env["MSD_FAKE_ACTION"] = action
        if marker:
            env["MSD_FAKE_MARKER"] = marker
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "session_runner.py"), "--config", str(self.config),
             "--state-root", str(self.state_root), "--repo", str(self.repo), *args],
            capture_output=True, text=True, check=check, env=env,
        )

    def fake_calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def two_write_lanes(self) -> list[dict]:
        return [
            {"id": "api", "role": "implementation-worker", "mode": "session", "platform": "claude",
             "write": True, "owned_paths": ["api/**"], "acceptance": "ok", "prompt": "impl api",
             "model": "sonnet", "effort": "high"},
            {"id": "web", "role": "implementation-worker", "mode": "session", "platform": "codex",
             "write": True, "owned_paths": ["web/**"], "acceptance": "ok", "prompt": "impl web"},
        ]

    def test_run_wave_spawns_both_platforms_in_worktrees_and_collects(self) -> None:
        plan = self.write_plan(self.two_write_lanes())
        result = self.runner("run", "--plan", str(plan), "--wave", "0", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        lanes = {lane["lane"]: lane for lane in payload["lanes"]}
        self.assertEqual(lanes["api"]["status"], "complete")
        self.assertEqual(lanes["web"]["status"], "complete")
        self.assertEqual(lanes["api"]["branch"], "msd/sample/api")
        self.assertTrue(Path(lanes["web"]["worktree_path"]).is_dir())
        self.assertEqual(lanes["api"]["dirty_paths"], [])
        self.assertIsNotNone(lanes["api"]["head_sha"])
        self.assertEqual(lanes["api"]["result"]["status"], "complete")
        self.assertIsNotNone(lanes["web"]["thread_id"])

        calls = {call["cwd"]: call for call in self.fake_calls()}
        api_call = calls[lanes["api"]["worktree_path"]]
        self.assertIn("--disallowedTools", api_call["argv"])
        self.assertIn("Bash(git push*)", api_call["argv"][api_call["argv"].index("--disallowedTools") + 1])
        self.assertNotIn("Edit", api_call["argv"][api_call["argv"].index("--disallowedTools") + 1])
        self.assertIn("--model", api_call["argv"])
        self.assertEqual(api_call["env_lane"], "sample/api")
        web_call = calls[lanes["web"]["worktree_path"]]
        self.assertIn("workspace-write", web_call["argv"])
        self.assertIn("--output-schema", web_call["argv"])
        # Lead checkout untouched
        self.assertEqual(git(self.repo, "status", "--porcelain").stdout, "")

    def test_read_lane_runs_in_lead_checkout_with_read_only_tools(self) -> None:
        plan = self.write_plan([
            {"id": "review", "role": "reviewer", "mode": "session", "platform": "claude",
             "write": False, "acceptance": "pass", "prompt": "review"},
            {"id": "second", "role": "reviewer", "mode": "session", "platform": "codex",
             "write": False, "advisory": True, "acceptance": "challenge", "prompt": "challenge"},
        ])
        result = self.runner("run", "--plan", str(plan), "--json", action="review-pass")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        lanes = {lane["lane"]: lane for lane in payload["lanes"]}
        self.assertIsNone(lanes["review"]["worktree_path"])
        self.assertEqual(lanes["review"]["result"]["verdict"], "PASS")
        calls = self.fake_calls()
        claude_call = next(c for c in calls if "--session-id" in c["argv"])
        disallowed = claude_call["argv"][claude_call["argv"].index("--disallowedTools") + 1]
        self.assertIn("Edit", disallowed)
        self.assertIn("Bash(git commit*)", disallowed)
        self.assertIn("opus", claude_call["argv"])  # role default applied
        codex_call = next(c for c in calls if "exec" in c["argv"])
        self.assertIn("read-only", codex_call["argv"])

    def test_review_fail_marks_run_not_ok_unless_advisory(self) -> None:
        plan = self.write_plan([
            {"id": "gate", "role": "reviewer", "mode": "session", "platform": "claude",
             "write": False, "acceptance": "pass", "prompt": "review"},
        ])
        result = self.runner("run", "--plan", str(plan), "--json", action="review-fail")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["ok"])

        plan = self.write_plan([
            {"id": "advice", "role": "reviewer", "mode": "session", "platform": "codex",
             "write": False, "advisory": True, "acceptance": "challenge", "prompt": "x"},
        ])
        result = self.runner("run", "--plan", str(plan), "--json", action="review-fail")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_dependency_skipped_when_upstream_blocked(self) -> None:
        lanes = self.two_write_lanes()
        lanes[1]["depends_on"] = ["api"]
        plan = self.write_plan(lanes)
        result = self.runner("run", "--plan", str(plan), "--json", action="blocked")
        self.assertEqual(result.returncode, 1)
        lanes_out = {lane["lane"]: lane for lane in json.loads(result.stdout)["lanes"]}
        self.assertEqual(lanes_out["api"]["status"], "blocked")
        self.assertEqual(lanes_out["api"]["result"]["blocked_reason"], "needs migration approval")
        self.assertEqual(lanes_out["web"]["status"], "skipped")
        # blocked lane's worktree is preserved for inspection
        self.assertTrue(Path(lanes_out["api"]["worktree_path"]).is_dir())

    def test_dirty_write_lane_is_failed_not_complete(self) -> None:
        plan = self.write_plan(self.two_write_lanes()[:1])
        result = self.runner("run", "--plan", str(plan), "--json", action="dirty")
        self.assertEqual(result.returncode, 1)
        lane = json.loads(result.stdout)["lanes"][0]
        self.assertEqual(lane["status"], "failed")
        self.assertIn("uncommitted", lane["result_problems"][0])

    def test_process_failure_is_failed(self) -> None:
        plan = self.write_plan(self.two_write_lanes()[1:])
        result = self.runner("run", "--plan", str(plan), "--json", action="fail")
        lane = json.loads(result.stdout)["lanes"][0]
        self.assertEqual(lane["status"], "failed")
        self.assertEqual(lane["exit_code"], 1)
        self.assertTrue(lane["runner_errors"])

    def test_nested_spawn_refused(self) -> None:
        plan = self.write_plan(self.two_write_lanes()[:1])
        env = dict(self.env)
        env["MULTI_SESSION_DEV_LANE"] = "other/lane"
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "session_runner.py"), "--config", str(self.config),
             "--state-root", str(self.state_root), "--repo", str(self.repo), "run", "--plan", str(plan)],
            capture_output=True, text=True, check=False, env=env,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("nested spawn refused", result.stderr)

    def test_dirty_lead_workspace_refuses_worktree(self) -> None:
        (self.repo / "scratch.txt").write_text("wip\n", encoding="utf-8")
        plan = self.write_plan(self.two_write_lanes()[:1])
        result = self.runner("spawn", "--plan", str(plan), "--lane", "api")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dirty", result.stderr)

    def test_spawn_wait_cancel_preserves_worktree(self) -> None:
        plan = self.write_plan(self.two_write_lanes()[:1])
        spawned = self.runner("spawn", "--plan", str(plan), "--lane", "api", action="sleep", check=True)
        record = json.loads(spawned.stdout)
        self.assertTrue(Path(record["worktree_path"]).is_dir())
        status = self.runner("status", "--task", "sample")
        self.assertIn("running", status.stdout)
        cancelled = self.runner("cancel", "--task", "sample")
        self.assertEqual(json.loads(cancelled.stdout)["cancelled"], ["api"])
        time.sleep(0.5)
        with self.assertRaises(ProcessLookupError):
            os.kill(record["pid"], 0)
        after = json.loads(self.runner("status", "--task", "sample", "--json").stdout)
        self.assertEqual(after["lanes"][0]["status"], "cancelled")
        self.assertTrue(Path(record["worktree_path"]).is_dir())

    def test_run_interrupt_cancels_children(self) -> None:
        plan = self.write_plan(self.two_write_lanes()[:1])
        env = dict(self.env)
        env["MSD_FAKE_ACTION"] = "sleep"
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPTS / "session_runner.py"), "--config", str(self.config),
             "--state-root", str(self.state_root), "--repo", str(self.repo), "run", "--plan", str(plan)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        deadline = time.time() + 20
        state_path = self.state_root / "tasks"
        pid = None
        while time.time() < deadline and pid is None:
            for task_json in state_path.glob("*/sample/task.json"):
                data = json.loads(task_json.read_text(encoding="utf-8"))
                pid = data["lanes"].get("api", {}).get("pid")
            time.sleep(0.2)
        self.assertIsNotNone(pid, "lane never started")
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=20)
        time.sleep(0.5)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_retry_limit_and_follow_up(self) -> None:
        plan = self.write_plan(self.two_write_lanes()[:1])
        self.runner("run", "--plan", str(plan), "--json", action="dirty")
        # attempt 2 with follow-up allowed (retry_limit=1 → 2 attempts total)
        second = self.runner("spawn", "--plan", str(plan), "--lane", "api", "--follow-up", "commit your work", action="complete")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.runner("wait", "--task", "sample")
        prompt = Path(json.loads(second.stdout)["attempt_dir"]) / "prompt.md"
        self.assertIn("Lead follow-up", prompt.read_text(encoding="utf-8"))
        third = self.runner("spawn", "--plan", str(plan), "--lane", "api", action="complete")
        self.assertNotEqual(third.returncode, 0)
        self.assertIn("retry limit", third.stderr)


if __name__ == "__main__":
    unittest.main()
