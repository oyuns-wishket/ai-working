#!/usr/bin/env python3
"""Integration tests for the knowns Git publisher."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional


SCRIPT = Path(__file__).with_name("publish_git.py")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=check,
    )


class PublishGitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.remote = root / "remote.git"
        self.repo = root / "wiki"
        self.project = root / "project"

        subprocess.run(["git", "init", "--bare", str(self.remote)], check=True, capture_output=True)
        subprocess.run(
            ["git", "init", "-b", "main", str(self.repo)],
            check=True,
            capture_output=True,
        )
        git(self.repo, "config", "user.name", "Knowns Test")
        git(self.repo, "config", "user.email", "knowns@invalid")
        (self.repo / "wiki.md").write_text("initial\n", encoding="utf-8")
        (self.repo / "other.md").write_text("other\n", encoding="utf-8")
        git(self.repo, "add", "wiki.md", "other.md")
        git(self.repo, "commit", "-m", "initial")
        git(self.repo, "remote", "add", "origin", str(self.remote))
        git(self.repo, "push", "-u", "origin", "main")

        subprocess.run(
            ["git", "init", "-b", "main", str(self.project)],
            check=True,
            capture_output=True,
        )
        git(self.project, "config", "user.name", "Project Test")
        git(self.project, "config", "user.email", "project@invalid")
        (self.project / "app.txt").write_text("project\n", encoding="utf-8")
        git(self.project, "add", "app.txt")
        git(self.project, "commit", "-m", "initial project")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_command(
        self,
        *extra: str,
        project_repo: Optional[Path] = None,
        approved_path: str = "wiki.md",
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo",
                str(self.repo),
                "--project-repo",
                str(project_repo or self.project),
                "--path",
                approved_path,
                "--message",
                "docs: ingest approved knowns",
                "--remote",
                "origin",
                "--remote-url",
                str(self.remote),
                "--branch",
                git(self.repo, "branch", "--show-current").stdout.strip(),
                *extra,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def run_publish(
        self,
        *extra: str,
        project_repo: Optional[Path] = None,
        approved_path: str = "wiki.md",
    ) -> subprocess.CompletedProcess:
        preflight = self.run_command(
            *extra,
            "--dry-run",
            project_repo=project_repo,
            approved_path=approved_path,
        )
        if preflight.returncode != 0:
            return preflight
        token = next(
            line.split(": ", 1)[1]
            for line in preflight.stdout.splitlines()
            if line.startswith("PREFLIGHT_TOKEN: ")
        )
        return self.run_command(
            *extra,
            "--preflight-token",
            token,
            project_repo=project_repo,
            approved_path=approved_path,
        )

    def test_dry_run_does_not_commit_or_push(self) -> None:
        head_before = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_command("--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("READY:", result.stdout)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD").stdout.strip(), head_before)
        self.assertEqual(
            git(self.remote, "show", "refs/heads/main:wiki.md").stdout,
            "initial\n",
        )

    def test_publish_commits_only_approved_file(self) -> None:
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")
        (self.repo / "other.md").write_text("unrelated dirty\n", encoding="utf-8")

        result = self.run_publish()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PUBLISHED:", result.stdout)
        self.assertEqual(
            git(self.remote, "show", "refs/heads/main:wiki.md").stdout,
            "approved\n",
        )
        self.assertEqual(
            git(self.remote, "show", "refs/heads/main:other.md").stdout,
            "other\n",
        )
        self.assertIn("other.md", git(self.repo, "status", "--short").stdout)

    def test_blocks_existing_staged_change(self) -> None:
        head_before = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")
        (self.repo / "other.md").write_text("staged unrelated\n", encoding="utf-8")
        git(self.repo, "add", "other.md")

        result = self.run_publish()

        self.assertEqual(result.returncode, 2)
        self.assertIn("index already has staged changes", result.stderr)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD").stdout.strip(), head_before)

    def test_blocks_project_repository_as_wiki_repository(self) -> None:
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_publish(project_repo=self.repo)

        self.assertEqual(result.returncode, 2)
        self.assertIn("wiki Git root is the project code repository", result.stderr)

    def test_blocks_linked_worktree_of_project_repository(self) -> None:
        linked = Path(self.temp.name) / "linked-project"
        git(self.repo, "worktree", "add", "-b", "linked-project", str(linked))
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_publish(project_repo=linked)

        self.assertEqual(result.returncode, 2)
        self.assertIn("wiki Git root is the project code repository", result.stderr)

    def test_blocks_when_remote_tip_differs(self) -> None:
        root = Path(self.temp.name)
        peer = root / "peer"
        subprocess.run(
            ["git", "clone", "--branch", "main", str(self.remote), str(peer)],
            check=True,
            capture_output=True,
        )
        git(peer, "config", "user.name", "Peer")
        git(peer, "config", "user.email", "peer@invalid")
        (peer / "peer.md").write_text("remote change\n", encoding="utf-8")
        git(peer, "add", "peer.md")
        git(peer, "commit", "-m", "remote update")
        git(peer, "push", "origin", "main")
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_publish()

        self.assertEqual(result.returncode, 2)
        self.assertIn("remote branch tip does not match local HEAD", result.stderr)

    def test_new_remote_branch_requires_explicit_approval(self) -> None:
        git(self.repo, "checkout", "-b", "knowledge-update")
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_publish()

        self.assertEqual(result.returncode, 2)
        self.assertIn("explicit --allow-new-branch is required", result.stderr)

    def test_allows_approved_new_branch_from_remote_commit(self) -> None:
        git(self.repo, "checkout", "-b", "knowledge-update")
        base = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_publish(
            "--allow-new-branch",
            "--new-branch-base",
            base,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            git(self.remote, "show", "refs/heads/knowledge-update:wiki.md").stdout,
            "approved\n",
        )

    def test_blocks_new_branch_that_contains_local_only_commit(self) -> None:
        git(self.repo, "checkout", "-b", "knowledge-update")
        (self.repo / "local-only.md").write_text("not on remote\n", encoding="utf-8")
        git(self.repo, "add", "local-only.md")
        git(self.repo, "commit", "-m", "local only")
        base = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_publish(
            "--allow-new-branch",
            "--new-branch-base",
            base,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("base is not advertised by the approved remote", result.stderr)

    def test_blocks_different_push_url(self) -> None:
        other_remote = Path(self.temp.name) / "other-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(other_remote)],
            check=True,
            capture_output=True,
        )
        git(self.repo, "remote", "set-url", "--push", "origin", str(other_remote))
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_command("--dry-run")

        self.assertEqual(result.returncode, 2)
        self.assertIn("fetch URL and push URL differ", result.stderr)

    def test_pathspec_like_filename_is_treated_literally(self) -> None:
        literal_name = ":(glob)*.md"
        (self.repo / literal_name).write_text("initial literal\n", encoding="utf-8")
        git(self.repo, "add", "--", f":(literal){literal_name}")
        git(self.repo, "commit", "-m", "add literal pathspec filename")
        git(self.repo, "push", "origin", "main")
        (self.repo / literal_name).write_text("approved literal\n", encoding="utf-8")
        (self.repo / "other.md").write_text("unrelated dirty\n", encoding="utf-8")

        result = self.run_publish(approved_path=literal_name)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            git(self.remote, "show", f"refs/heads/main:{literal_name}").stdout,
            "approved literal\n",
        )
        self.assertEqual(
            git(self.remote, "show", "refs/heads/main:other.md").stdout,
            "other\n",
        )

    def test_preflight_token_blocks_content_change(self) -> None:
        (self.repo / "wiki.md").write_text("approved once\n", encoding="utf-8")
        preflight = self.run_command("--dry-run")
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        token = next(
            line.split(": ", 1)[1]
            for line in preflight.stdout.splitlines()
            if line.startswith("PREFLIGHT_TOKEN: ")
        )
        (self.repo / "wiki.md").write_text("changed after preflight\n", encoding="utf-8")

        result = self.run_command("--preflight-token", token)

        self.assertEqual(result.returncode, 2)
        self.assertIn("changed after preflight", result.stderr)

    def test_active_commit_hook_blocks_before_local_commit(self) -> None:
        head_before = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\ngit add other.md\n", encoding="utf-8")
        hook.chmod(0o755)
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")
        (self.repo / "other.md").write_text("hook tries to add\n", encoding="utf-8")

        result = self.run_publish()

        self.assertEqual(result.returncode, 2)
        self.assertIn("active Git hook", result.stderr)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD").stdout.strip(), head_before)
        self.assertEqual(
            git(self.remote, "show", "refs/heads/main:wiki.md").stdout,
            "initial\n",
        )

    def test_active_pre_push_hook_blocks_before_local_commit(self) -> None:
        head_before = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        hook = self.repo / ".git" / "hooks" / "pre-push"
        hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        hook.chmod(0o755)
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_publish()

        self.assertEqual(result.returncode, 2)
        self.assertIn("active Git hook", result.stderr)
        self.assertIn("pre-push", result.stderr)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD").stdout.strip(), head_before)

    def test_required_signed_commit_policy_blocks_before_local_commit(self) -> None:
        head_before = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        git(self.repo, "config", "commit.gpgSign", "true")
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_publish()

        self.assertEqual(result.returncode, 2)
        self.assertIn("required signed commits", result.stderr)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD").stdout.strip(), head_before)

    def test_push_rejection_leaves_only_approved_local_commit(self) -> None:
        head_before = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        (self.repo / "wiki.md").write_text("approved\n", encoding="utf-8")

        result = self.run_publish()

        self.assertEqual(result.returncode, 2)
        self.assertIn("pre-receive hook declined", result.stderr)
        self.assertIn("push failed after local commit", result.stderr)
        head_after = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(head_after, head_before)
        self.assertEqual(
            git(self.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").stdout,
            "wiki.md\n",
        )
        self.assertEqual(
            git(self.remote, "show", "refs/heads/main:wiki.md").stdout,
            "initial\n",
        )


if __name__ == "__main__":
    unittest.main()
