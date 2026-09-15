from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"


def run_script(
    name: str, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


class MultiAgentDevScriptsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="multi-session-dev-test-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "sample-erp"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "commit", "--allow-empty", "-qm", "initial")
        self.config = self.root / "config.json"
        self.state_root = self.root / "state"
        self.worktree_root = self.root / "worktrees"

    def tearDown(self) -> None:
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "prune"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.temp.cleanup()

    def configure(self) -> dict:
        domain = self.root / "erp-domain.md"
        domain.write_text("# ERP domain\n", encoding="utf-8")
        result = run_script(
            "configure.py",
            "--config",
            str(self.config),
            "set",
            "--workspace-root",
            str(self.root),
            "--erp-domain-reference",
            str(domain),
            "--worktree-root",
            str(self.worktree_root),
            "--platform",
            "both",
        )
        return json.loads(result.stdout)

    def worker_spec(self, name: str = "erp-domain-analyst") -> Path:
        path = self.root / f"{name}.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "name": name,
                    "description": "ERP 업무 불변조건을 검토하는 Worker",
                    "capability": "erp-domain-analyst",
                    "write_access": False,
                    "command_access": False,
                    "codex_reasoning_effort": "high",
                    "instructions": "프로젝트 규칙과 ERP 문서를 먼저 읽고 근거를 보고한다.",
                    "required_references": ["CLAUDE.md", "AGENTS.md"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path

    def test_configure_and_validate(self) -> None:
        saved = self.configure()
        self.assertTrue(saved["valid"])
        validation = run_script(
            "configure.py",
            "--config",
            str(self.config),
            "validate",
            "--json",
        )
        payload = json.loads(validation.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["config"]["platforms"], ["claude", "codex"])

    def test_inspect_project_detects_stack_and_existing_worker(self) -> None:
        self.configure()
        (self.repo / "package.json").write_text(
            json.dumps(
                {
                    "name": "sample-erp",
                    "scripts": {"build": "next build", "test": "vitest run"},
                    "dependencies": {
                        "next": "16.0.0",
                        "@supabase/supabase-js": "2.0.0",
                    },
                }
            ),
            encoding="utf-8",
        )
        (self.repo / "supabase" / "migrations").mkdir(parents=True)
        agent_dir = self.repo / ".claude" / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "developer.md").write_text(
            "---\nname: developer\ndescription: ERP 기능 구현\n---\n",
            encoding="utf-8",
        )
        result = run_script(
            "inspect_project.py",
            "--project",
            str(self.repo),
            "--config",
            str(self.config),
            "--json",
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["signals"]["database"])
        self.assertTrue(payload["signals"]["ui"])
        implementation = next(
            item
            for item in payload["recommended_capabilities"]
            if item["capability"] == "implementation-worker"
        )
        self.assertEqual(implementation["existing_candidates"][0]["name"], "developer")

    def test_render_worker_creates_both_adapters_and_preserves_existing(self) -> None:
        spec = self.worker_spec()
        dry_run = run_script(
            "render_worker.py",
            "--project",
            str(self.repo),
            "--spec",
            str(spec),
            "--platform",
            "both",
            "--dry-run",
        )
        self.assertTrue(json.loads(dry_run.stdout)["dry_run"])
        run_script(
            "render_worker.py",
            "--project",
            str(self.repo),
            "--spec",
            str(spec),
            "--platform",
            "both",
        )
        claude_path = self.repo / ".claude" / "agents" / "erp-domain-analyst.md"
        codex_path = self.repo / ".codex" / "agents" / "erp-domain-analyst.toml"
        canonical_path = (
            self.repo
            / ".agents"
            / "multi-session-dev"
            / "workers"
            / "erp-domain-analyst.json"
        )
        self.assertTrue(claude_path.is_file())
        self.assertTrue(codex_path.is_file())
        self.assertTrue(canonical_path.is_file())
        self.assertNotIn("effort:", claude_path.read_text(encoding="utf-8"))
        codex_text = codex_path.read_text(encoding="utf-8")
        self.assertIn('model_reasoning_effort = "high"', codex_text)
        self.assertIn('sandbox_mode = "read-only"', codex_text)

        changed = json.loads(spec.read_text(encoding="utf-8"))
        changed["description"] = "changed"
        spec.write_text(json.dumps(changed), encoding="utf-8")
        refused = run_script(
            "render_worker.py",
            "--project",
            str(self.repo),
            "--spec",
            str(spec),
            check=False,
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("Refusing to overwrite", refused.stderr)

    def test_worktree_cleanup_preserves_unintegrated_then_removes_integrated(
        self,
    ) -> None:
        self.configure()
        created = run_script(
            "worktree_manager.py",
            "--config",
            str(self.config),
            "--state-root",
            str(self.state_root),
            "create",
            "--repo",
            str(self.repo),
            "--session",
            "order-return",
            "--worker",
            "developer",
            "--json",
        )
        creation = json.loads(created.stdout)
        worker_path = Path(creation["worktree_path"])
        worker_file = worker_path / "feature.txt"
        worker_file.write_text("implemented\n", encoding="utf-8")
        git(worker_path, "add", "feature.txt")
        git(worker_path, "commit", "-qm", "implement feature")

        first_cleanup = run_script(
            "worktree_manager.py",
            "--state-root",
            str(self.state_root),
            "cleanup",
            "--repo",
            str(self.repo),
            "--session",
            "order-return",
            "--target-ref",
            "main",
            "--json",
        )
        first = json.loads(first_cleanup.stdout)
        self.assertEqual(first["preserved"][0]["reason"], "not-integrated")
        self.assertTrue(worker_path.is_dir())

        git(self.repo, "merge", "--no-ff", "-m", "merge worker", creation["branch"])
        second_cleanup = run_script(
            "worktree_manager.py",
            "--state-root",
            str(self.state_root),
            "cleanup",
            "--repo",
            str(self.repo),
            "--session",
            "order-return",
            "--target-ref",
            "main",
            "--json",
        )
        second = json.loads(second_cleanup.stdout)
        self.assertEqual(second["removed"][0]["worker"], "developer")
        self.assertFalse(worker_path.exists())
        branch = git(
            self.repo,
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/heads/{creation['branch']}",
            check=False,
        )
        self.assertNotEqual(branch.returncode, 0)

    def test_worktree_allows_only_generated_worker_metadata(self) -> None:
        self.configure()
        spec = self.worker_spec()
        run_script(
            "render_worker.py",
            "--project",
            str(self.repo),
            "--spec",
            str(spec),
        )
        refused = run_script(
            "worktree_manager.py",
            "--config",
            str(self.config),
            "--state-root",
            str(self.state_root),
            "create",
            "--repo",
            str(self.repo),
            "--session",
            "metadata-only",
            "--worker",
            "developer",
            check=False,
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("Lead workspace is dirty", refused.stderr)

        allowed = run_script(
            "worktree_manager.py",
            "--config",
            str(self.config),
            "--state-root",
            str(self.state_root),
            "create",
            "--repo",
            str(self.repo),
            "--session",
            "metadata-only",
            "--worker",
            "developer",
            "--allow-generated-worker-metadata",
            "--json",
        )
        payload = json.loads(allowed.stdout)
        self.assertEqual(len(payload["excluded_dirty_worker_metadata"]), 3)
        run_script(
            "worktree_manager.py",
            "--state-root",
            str(self.state_root),
            "cleanup",
            "--repo",
            str(self.repo),
            "--session",
            "metadata-only",
            "--target-ref",
            "main",
            "--json",
        )


if __name__ == "__main__":
    unittest.main()
