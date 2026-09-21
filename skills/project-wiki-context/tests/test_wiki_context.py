#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/wiki_context.py"
SPEC = importlib.util.spec_from_file_location("wiki_context", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class WikiContextTest(unittest.TestCase):
    def make_repo(self, base: Path) -> Path:
        repo = base / "repo"
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
        (repo / "README.md").write_text("initial\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
        return repo

    def write_doc(
        self,
        path: Path,
        *,
        title: str,
        body: str,
        review_by: str = "2099-01-01",
        source_refs: list[str] | None = None,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        refs = source_refs or ["user-confirmation:2099-01-01"]
        ref_lines = "\n".join(f"  - {ref}" for ref in refs)
        path.write_text(
            "---\n"
            f"title: {title}\n"
            "status: canonical\n"
            f"review_by: {review_by}\n"
            "source_refs:\n"
            f"{ref_lines}\n"
            "---\n"
            f"{body}\n",
            encoding="utf-8",
        )

    def test_normalize_remote_variants(self):
        expected = "github.com/example-org/sample-app"
        self.assertEqual(MODULE.normalize_remote("https://github.com/example-org/sample-app.git"), expected)
        self.assertEqual(MODULE.normalize_remote("git@github.com:example-org/sample-app.git"), expected)
        self.assertEqual(MODULE.normalize_remote("ssh://git@github.com/example-org/sample-app.git"), expected)

    def test_contested_and_overdue_documents_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            namespace = Path(temp)
            contested = namespace / "contested.md"
            contested.write_text(
                "---\nstatus: contested\nreview_by: 2099-01-01\ntitle: bad\n---\nbody\n",
                encoding="utf-8",
            )
            overdue = namespace / "overdue.md"
            overdue.write_text(
                "---\nstatus: canonical\nreview_by: 2020-01-01\ntitle: old\n---\nbody\n",
                encoding="utf-8",
            )
            ok, reason, _, _ = MODULE.safe_document(contested, namespace, dt.date.today())
            self.assertFalse(ok)
            self.assertEqual(reason, "status:contested")
            ok, reason, _, _ = MODULE.safe_document(overdue, namespace, dt.date.today())
            self.assertFalse(ok)
            self.assertTrue(reason.startswith("overdue:"))

    def test_unterminated_frontmatter_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            namespace = Path(temp)
            malformed = namespace / "malformed.md"
            malformed.write_text(
                "---\nstatus: canonical\nreview_by: 2099-01-01\ntitle: unsafe\nbody\n",
                encoding="utf-8",
            )
            ok, reason, _, _ = MODULE.safe_document(malformed, namespace, dt.date.today())
            self.assertFalse(ok)
            self.assertEqual(reason, "status:missing")

    def test_route_keeps_index_outside_limit_and_skips_zero_overlap_pin(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = self.make_repo(base)
            namespace = base / "wiki" / "project"
            index = namespace / "index.md"
            relevant = namespace / "domain" / "orders.md"
            second = namespace / "domain" / "shipping.md"
            pinned = namespace / "system" / "infra.md"
            self.write_doc(index, title="Project index", body="navigation")
            self.write_doc(relevant, title="주문 수집", body="주문 수집 계약")
            self.write_doc(second, title="주문 배송", body="주문 배송 계약")
            self.write_doc(pinned, title="인프라", body="배포 네트워크")
            identity = MODULE.git_identity(repo)
            resolved = {
                "mode": "wiki-bounded",
                "namespace_path": str(namespace),
                "index_path": str(index),
                "git_root": str(repo),
                "repo_state": MODULE.repository_state(identity),
                "project": {
                    "id": "example.test/team/repo",
                    "local_aliases": ["repo"],
                    "retrieval": {
                        "max_documents": 2,
                        "max_total_bytes": 80000,
                        "pinned": ["system/infra.md"],
                    },
                },
            }
            routed = MODULE.routed_documents(resolved, "주문")
            self.assertEqual(len(routed["query_documents"]), 2)
            self.assertEqual(routed["documents"][0]["relative_path"], "index.md")
            self.assertNotIn("system/infra.md", [row["relative_path"] for row in routed["documents"]])
            self.assertFalse(routed["index_counts_toward_document_limit"])

    def test_intent_route_can_select_a_document_without_exact_query_token(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = self.make_repo(base)
            namespace = base / "wiki" / "project"
            index = namespace / "index.md"
            architecture = namespace / "system" / "landscape.md"
            self.write_doc(index, title="Project index", body="navigation")
            self.write_doc(architecture, title="System landscape", body="service ownership")
            identity = MODULE.git_identity(repo)
            resolved = {
                "mode": "wiki-bounded",
                "namespace_path": str(namespace),
                "index_path": str(index),
                "git_root": str(repo),
                "repo_state": MODULE.repository_state(identity),
                "project": {
                    "id": "example.test/team/repo",
                    "local_aliases": ["repo"],
                    "retrieval": {
                        "max_documents": 1,
                        "max_total_bytes": 80000,
                        "pinned": [],
                        "intent_routes": {
                            "architecture": {
                                "terms": ["아키텍처"],
                                "documents": ["system/landscape.md"],
                            }
                        },
                    },
                },
            }
            routed = MODULE.routed_documents(resolved, "아키텍처가 궁금해")
            self.assertEqual(routed["matched_intents"], ["architecture"])
            self.assertEqual(routed["query_documents"][0]["relative_path"], "system/landscape.md")
            self.assertIn("intent-route", routed["query_documents"][0]["selection_reasons"])

    def test_oversized_index_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = self.make_repo(base)
            namespace = base / "wiki" / "project"
            index = namespace / "index.md"
            self.write_doc(index, title="Project index", body="navigation" * 20)
            identity = MODULE.git_identity(repo)
            resolved = {
                "mode": "wiki-bounded",
                "namespace_path": str(namespace),
                "index_path": str(index),
                "git_root": str(repo),
                "repo_state": MODULE.repository_state(identity),
                "project": {
                    "id": "example.test/team/repo",
                    "local_aliases": ["repo"],
                    "retrieval": {"max_documents": 1, "max_total_bytes": 10, "pinned": []},
                },
            }
            routed = MODULE.routed_documents(resolved, "navigation")
            self.assertEqual(routed["mode"], "repo-only")
            self.assertEqual(routed["documents"], [])
            self.assertEqual(routed["route_reason"], "namespace index exceeds max_total_bytes")

    def test_document_with_missing_source_is_not_routed(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = self.make_repo(base)
            namespace = base / "wiki" / "project"
            self.write_doc(namespace / "index.md", title="Index", body="navigation")
            self.write_doc(
                namespace / "orders.md",
                title="주문",
                body="주문 처리",
                source_refs=["repo:repo@deadbee/missing.md"],
            )
            identity = MODULE.git_identity(repo)
            resolved = {
                "mode": "wiki-bounded",
                "namespace_path": str(namespace),
                "index_path": str(namespace / "index.md"),
                "git_root": str(repo),
                "repo_state": MODULE.repository_state(identity),
                "project": {
                    "id": "example.test/team/repo",
                    "local_aliases": ["repo"],
                    "retrieval": {"max_documents": 1, "max_total_bytes": 80000, "pinned": []},
                },
            }
            routed = MODULE.routed_documents(resolved, "주문")
            self.assertEqual(routed["query_documents"], [])
            self.assertIn(
                {"path": "orders.md", "reason": "invalid-source-ref"},
                routed["rejected"],
            )
            self.assertEqual(routed["warnings"][0], "knowledge degraded: 1 document rejected (invalid-source-ref 1)")
            self.assertIn("orders.md: invalid-source-ref", routed["warnings"])
            self.assertEqual(routed["knowledge_health"]["rejected_reasons"], {"invalid-source-ref": 1})
            self.assertEqual(routed["knowledge_health"]["rejected_count"], 1)

    def test_repository_state_and_source_reference_drift_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = self.make_repo(base)
            first_sha = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            (repo / "README.md").write_text("changed\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "change"], check=True, capture_output=True)
            namespace = base / "wiki" / "project"
            doc = namespace / "system.md"
            self.write_doc(
                doc,
                title="System",
                body="system",
                source_refs=[f"repo:repo@{first_sha}/README.md"],
            )
            identity = MODULE.git_identity(repo)
            resolved = {
                "git_root": str(repo),
                "repo_state": MODULE.repository_state(identity),
                "project": {"id": "example.test/team/repo", "local_aliases": ["repo"]},
            }
            state = resolved["repo_state"]
            health = MODULE.source_reference_health(doc, resolved)
            self.assertIsNotNone(state["branch"])
            self.assertEqual(state["dirty_count"], 0)
            self.assertEqual(health["checked"], 1)
            self.assertEqual(health["changed_paths"], 1)
            self.assertEqual(health["missing_commits"], 0)
            self.assertEqual(health["missing_paths"], 0)

    def test_namespace_health_marks_overdue_pinned_as_degraded(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = self.make_repo(base)
            namespace = base / "wiki" / "project"
            index = namespace / "index.md"
            pinned = namespace / "source.md"
            self.write_doc(index, title="Index", body="navigation")
            self.write_doc(pinned, title="Source authority", body="authority", review_by="2020-01-01")
            identity = MODULE.git_identity(repo)
            resolved = {
                "namespace_path": str(namespace),
                "git_root": str(repo),
                "repo_state": MODULE.repository_state(identity),
                "project": {
                    "id": "example.test/team/repo",
                    "local_aliases": ["repo"],
                    "retrieval": {"pinned": ["source.md"]},
                },
            }
            health = MODULE.namespace_health(resolved, dt.date(2026, 8, 31))
            self.assertEqual(health["status"], "degraded")
            self.assertEqual(health["canonical_overdue"], 1)
            self.assertIn("pinned-unavailable", health["reasons"])

    def test_valid_source_from_another_branch_is_not_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = self.make_repo(base)
            initial = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(["git", "-C", str(repo), "checkout", "-b", "release"], check=True, capture_output=True)
            (repo / "release.md").write_text("release\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "release.md"], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-m", "release evidence"],
                check=True,
                capture_output=True,
            )
            release_sha = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(["git", "-C", str(repo), "checkout", "--detach", initial], check=True, capture_output=True)
            namespace = base / "wiki" / "project"
            pinned = namespace / "source.md"
            self.write_doc(
                namespace / "index.md", title="Index", body="navigation"
            )
            self.write_doc(
                pinned,
                title="Source",
                body="authority",
                source_refs=[f"repo:repo@{release_sha}/release.md"],
            )
            resolved = {
                "namespace_path": str(namespace),
                "git_root": str(repo),
                "project": {
                    "id": "example.test/team/repo",
                    "local_aliases": ["repo"],
                    "retrieval": {"pinned": ["source.md"]},
                },
            }
            health = MODULE.namespace_health(resolved, dt.date(2026, 8, 31))
            self.assertEqual(health["status"], "healthy")
            self.assertEqual(health["pinned"][0]["source_health"]["non_ancestor_commits"], 1)

    def test_namespace_health_rejects_pinned_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = self.make_repo(base)
            namespace = base / "wiki" / "project"
            self.write_doc(namespace / "index.md", title="Index", body="navigation")
            outside = base / "outside.md"
            self.write_doc(outside, title="Outside", body="must not read")
            (namespace / "source.md").symlink_to(outside)
            resolved = {
                "namespace_path": str(namespace),
                "git_root": str(repo),
                "project": {
                    "id": "example.test/team/repo",
                    "local_aliases": ["repo"],
                    "retrieval": {"pinned": ["source.md"]},
                },
            }
            health = MODULE.namespace_health(resolved, dt.date(2026, 8, 31))
            self.assertEqual(health["status"], "degraded")
            self.assertEqual(health["pinned"][0]["reason"], "path escapes namespace")

    def test_resolve_rejects_registry_namespace_outside_wiki(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = self.make_repo(base)
            wiki_root = base / "wiki-repo"
            registry_dir = wiki_root / "registry"
            registry_dir.mkdir(parents=True)
            outside = wiki_root / "outside"
            self.write_doc(outside / "index.md", title="Outside", body="must not route")
            (registry_dir / "project-registry.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "projects": [
                            {
                                "id": "local/repo",
                                "canonical_remote": None,
                                "remote_aliases": [],
                                "local_aliases": ["repo"],
                                "connection_status": "connected",
                                "wiki_namespace": "wiki/../outside",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            resolved = MODULE.resolve(repo, str(wiki_root))
            self.assertEqual(resolved["mode"], "repo-only")
            self.assertIn("outside wiki", resolved["reason"])

    def test_load_registry_rejects_parseable_invalid_types(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self.make_repo(root)
            registry_dir = root / "registry"
            registry_dir.mkdir(parents=True)
            (registry_dir / "project-registry.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "projects": [
                            {
                                "id": "local/repo",
                                "canonical_remote": None,
                                "remote_aliases": [],
                                "local_aliases": ["repo"],
                                "connection_status": "connected",
                                "wiki_namespace": 123,
                                "retrieval": {"max_documents": "four"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(MODULE.ContextError):
                MODULE.load_registry(root)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--wiki-root",
                    str(root),
                    "route",
                    "--project",
                    str(repo),
                    "--query",
                    "safe fallback",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(json.loads(result.stdout)["mode"], "repo-only")

    def test_worktree_and_clone_remote_resolve_same_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            remote = base / "remote.git"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
            repo = base / "repo"
            subprocess.run(["git", "clone", str(remote), str(repo)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            (repo / "README.md").write_text("test\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
            worktree = base / "worktree"
            subprocess.run(["git", "-C", str(repo), "worktree", "add", "-b", "test-worktree", str(worktree)], check=True, capture_output=True)
            registry = {
                "projects": [
                    {
                        "id": MODULE.normalize_remote(str(remote)),
                        "canonical_remote": str(remote),
                        "remote_aliases": [],
                    }
                ]
            }
            first, _ = MODULE.resolve_entry(registry, MODULE.git_identity(repo))
            second, _ = MODULE.resolve_entry(registry, MODULE.git_identity(worktree))
            self.assertEqual(first["id"], second["id"])

    def test_missing_wiki_cli_falls_back_repo_only(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            repo = base / "repo"
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            env = os.environ.copy()
            env["HOME"] = str(base / "empty-home")
            env.pop("AI_WORKING_CONTEXT_REGISTRY_PATH", None)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--wiki-root",
                    str(base / "missing-wiki"),
                    "route",
                    "--project",
                    str(repo),
                    "--query",
                    "safe fallback",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "repo-only")
            self.assertEqual(payload["documents"], [])
            self.assertFalse(payload["managed"])


if __name__ == "__main__":
    unittest.main()
