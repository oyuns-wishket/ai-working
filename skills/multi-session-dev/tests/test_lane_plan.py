from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lane_plan import ownership_root, roots_overlap, validate_plan  # noqa: E402


def base_plan(**overrides):
    plan = {
        "schema_version": 1,
        "task": "sample",
        "target_branch": "feat/sample",
        "commit_allowed": True,
        "lanes": [
            {
                "id": "api", "role": "implementation-worker", "mode": "session", "platform": "claude",
                "write": True, "owned_paths": ["apps/api/**"], "acceptance": "works", "prompt": "do it",
            },
            {
                "id": "web", "role": "implementation-worker", "mode": "session", "platform": "codex",
                "write": True, "owned_paths": ["apps/web/src/**"], "acceptance": "works", "prompt": "do it",
            },
            {
                "id": "review", "role": "reviewer", "mode": "session", "platform": "claude",
                "write": False, "depends_on": ["api", "web"], "acceptance": "pass", "prompt": "review",
            },
        ],
    }
    plan.update(overrides)
    return plan


class LanePlanTest(unittest.TestCase):
    def test_valid_plan_yields_waves(self) -> None:
        errors, waves = validate_plan(base_plan())
        self.assertEqual(errors, [])
        self.assertEqual(waves, [["api", "web"], ["review"]])

    def test_ownership_overlap_fails(self) -> None:
        plan = base_plan()
        plan["lanes"][1]["owned_paths"] = ["apps/api/src/orders/**"]
        errors, waves = validate_plan(plan)
        self.assertTrue(any("ownership overlap" in e for e in errors))
        self.assertEqual(waves, [])

    def test_ownership_root_and_overlap_helpers(self) -> None:
        self.assertEqual(ownership_root("apps/api/src/**"), "apps/api/src")
        self.assertEqual(ownership_root("./apps/web/*.ts"), "apps/web")
        self.assertTrue(roots_overlap("apps/api", "apps/api/src"))
        self.assertFalse(roots_overlap("apps/api", "apps/api-v2"))
        self.assertTrue(roots_overlap("", "apps/api"))

    def test_cycle_fails(self) -> None:
        plan = base_plan()
        plan["lanes"][0]["depends_on"] = ["review"]
        errors, _ = validate_plan(plan)
        self.assertTrue(any("cycle" in e for e in errors))

    def test_write_lane_requires_session_and_commit_permission(self) -> None:
        plan = base_plan(commit_allowed=False)
        plan["lanes"][0]["mode"] = "subagent"
        errors, _ = validate_plan(plan)
        self.assertTrue(any("mode 'session'" in e for e in errors))
        self.assertTrue(any("commit_allowed=true" in e for e in errors))

    def test_shared_target_branch_rejected(self) -> None:
        errors, _ = validate_plan(base_plan(target_branch="main"))
        self.assertTrue(any("shared branch" in e for e in errors))

    def test_advisory_only_for_read_lanes(self) -> None:
        plan = base_plan()
        plan["lanes"][0]["advisory"] = True
        errors, _ = validate_plan(plan)
        self.assertTrue(any("advisory" in e for e in errors))

    def test_cli_reports_invalid_with_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "plan.json"
            plan = base_plan()
            plan["lanes"][1]["depends_on"] = ["missing"]
            path.write_text(json.dumps(plan), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "lane_plan.py"), "validate", "--plan", str(path), "--json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["valid"])
            self.assertIn("unknown dependency 'missing'", " ".join(payload["errors"]))


if __name__ == "__main__":
    unittest.main()
