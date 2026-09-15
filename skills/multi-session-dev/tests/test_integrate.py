from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
FAKES = SKILL_ROOT / "tests" / "fakes"


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True, text=True)


class IntegrateTest(unittest.TestCase):
    """Runs two fake write lanes, then integrates, verifies and cleans up."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="msd-integrate-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "sample"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.com")
        (self.repo / "shared.txt").write_text("base\n", encoding="utf-8")
        git(self.repo, "add", "shared.txt")
        git(self.repo, "commit", "-qm", "initial")
        git(self.repo, "checkout", "-qb", "feat/sample")
        self.state_root = self.root / "state"
        self.config = self.root / "config.json"
        for fake in ("claude", "codex"):
            os.chmod(FAKES / fake, 0o755)
        self.config.write_text(json.dumps({
            "schema_version": 1,
            "worktree_root": str(self.root / "worktrees"),
            "platforms": ["claude", "codex"],
            "binaries": {"claude": str(FAKES / "claude"), "codex": str(FAKES / "codex")},
        }), encoding="utf-8")
        self.env = {k: v for k, v in os.environ.items() if k != "MULTI_SESSION_DEV_LANE"}

    def tearDown(self) -> None:
        subprocess.run(["git", "-C", str(self.repo), "worktree", "prune"], check=False, capture_output=True)
        self.temp.cleanup()

    def script(self, name: str, *args: str, action: str = "complete", marker: str = "lane.txt"):
        env = dict(self.env, MSD_FAKE_ACTION=action, MSD_FAKE_MARKER=marker)
        return subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            capture_output=True, text=True, check=False, env=env,
        )

    def plan(self, second_marker_same: bool = False) -> Path:
        plan = {
            "schema_version": 1, "task": "sample", "repo": str(self.repo),
            "target_branch": "feat/sample", "commit_allowed": True,
            "lanes": [
                {"id": "api", "role": "implementation-worker", "mode": "session", "platform": "claude",
                 "write": True, "owned_paths": ["api/**"], "acceptance": "ok", "prompt": "x"},
                {"id": "web", "role": "implementation-worker", "mode": "session", "platform": "codex",
                 "write": True, "owned_paths": ["web/**"], "acceptance": "ok", "prompt": "x"},
                # never run before integration: integrate.py must tolerate lanes absent from state
                {"id": "review", "role": "reviewer", "mode": "session", "platform": "claude",
                 "write": False, "depends_on": ["api", "web"], "acceptance": "pass", "prompt": "x"},
            ],
        }
        path = self.root / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def run_lane(self, plan: Path, lane: str, marker: str) -> None:
        result = self.script(
            "session_runner.py", "--config", str(self.config), "--state-root", str(self.state_root),
            "--repo", str(self.repo), "run", "--plan", str(plan), "--lane", lane, "--json", marker=marker,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_sequential_merge_verify_and_cleanup(self) -> None:
        plan = self.plan()
        self.run_lane(plan, "api", "api.txt")
        self.run_lane(plan, "web", "web.txt")

        dry = self.script("integrate.py", "--task", "sample", "--repo", str(self.repo),
                          "--state-root", str(self.state_root), "--dry-run")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual([m["lane"] for m in json.loads(dry.stdout)["merged"]], ["api", "web"])
        self.assertEqual(git(self.repo, "rev-list", "--count", "HEAD").stdout.strip(), "1")

        real = self.script("integrate.py", "--task", "sample", "--repo", str(self.repo),
                           "--state-root", str(self.state_root),
                           "--verify", "test -f api.txt && test -f web.txt", "--verify", "false")
        payload = json.loads(real.stdout)
        self.assertEqual(real.returncode, 1)  # second verify command fails
        self.assertEqual([m["lane"] for m in payload["merged"]], ["api", "web"])
        self.assertEqual([v["exit_code"] for v in payload["verify"]], [0, 1])
        self.assertTrue((self.repo / "api.txt").is_file())
        self.assertTrue((self.repo / "web.txt").is_file())
        self.assertIn("merge(msd): lane web", git(self.repo, "log", "-1", "--pretty=%s").stdout)

        again = self.script("integrate.py", "--task", "sample", "--repo", str(self.repo),
                            "--state-root", str(self.state_root))
        self.assertEqual(again.returncode, 0)
        self.assertEqual({s["reason"] for s in json.loads(again.stdout)["skipped"]}, {"already-integrated"})

        cleanup = self.script("worktree_manager.py", "--state-root", str(self.state_root), "cleanup",
                              "--repo", str(self.repo), "--session", "sample", "--target-ref", "feat/sample", "--json")
        removed = json.loads(cleanup.stdout)
        self.assertEqual(sorted(r["worker"] for r in removed["removed"]), ["api", "web"])
        self.assertEqual(removed["preserved"], [])
        self.assertEqual(git(self.repo, "worktree", "list").stdout.count("\n"), 1)

    def test_conflict_is_reported_not_resolved(self) -> None:
        plan = self.plan()
        self.run_lane(plan, "api", "shared.txt")
        self.run_lane(plan, "web", "shared.txt")
        result = self.script("integrate.py", "--task", "sample", "--repo", str(self.repo),
                             "--state-root", str(self.state_root))
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual([m["lane"] for m in payload["merged"]], ["api"])
        self.assertEqual(payload["conflicted"][0]["lane"], "web")
        self.assertIn("shared.txt", payload["conflicted"][0]["files"])
        self.assertEqual(payload["verify"], [])
        self.assertEqual(git(self.repo, "status", "--porcelain").stdout, "")  # no half-merge left behind
        self.assertNotIn("<<<<", (self.repo / "shared.txt").read_text(encoding="utf-8"))

    def test_refuses_wrong_branch_or_dirty_workspace(self) -> None:
        plan = self.plan()
        self.run_lane(plan, "api", "api.txt")
        git(self.repo, "checkout", "-q", "main")
        wrong = self.script("integrate.py", "--task", "sample", "--repo", str(self.repo),
                            "--state-root", str(self.state_root))
        self.assertNotEqual(wrong.returncode, 0)
        self.assertIn("expected target", wrong.stderr)
        git(self.repo, "checkout", "-q", "feat/sample")
        (self.repo / "wip.txt").write_text("x", encoding="utf-8")
        dirty = self.script("integrate.py", "--task", "sample", "--repo", str(self.repo),
                            "--state-root", str(self.state_root))
        self.assertNotEqual(dirty.returncode, 0)
        self.assertIn("dirty", dirty.stderr)


if __name__ == "__main__":
    unittest.main()
