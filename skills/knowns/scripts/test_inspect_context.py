#!/usr/bin/env python3
"""Fixture tests for inspect_context.py."""

from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("inspect_context.py")
SPEC = importlib.util.spec_from_file_location("knowns_inspect_context", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InspectContextTests(unittest.TestCase):
    def test_explicit_connection_and_referenced_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            knowledge = root / "knowledge-base"
            (project / ".claude" / "rules").mkdir(parents=True)
            (knowledge / "raw").mkdir(parents=True)
            (knowledge / "wiki" / "90-agent").mkdir(parents=True)
            (knowledge / "policies").mkdir()
            (knowledge / "scripts").mkdir()
            (project / "AGENTS.md").write_text(
                f"공유 지식베이스는 `{knowledge}`의 wiki를 따른다.\n",
                encoding="utf-8",
            )
            (project / ".claude" / "rules" / "knowledge.md").write_text(
                "작업 종료 시 지식베이스 규칙을 확인한다.\n",
                encoding="utf-8",
            )
            (knowledge / "CLAUDE.md").write_text(
                "ingest는 `wiki/90-agent/maintenance-runbook.md`를 따르고 "
                "추가 규칙은 `policies/`에 있으며 "
                "`python3 scripts/kb_check.py`를 실행한다.\n",
                encoding="utf-8",
            )
            runbook = knowledge / "wiki" / "90-agent" / "maintenance-runbook.md"
            runbook.write_text("# Maintenance runbook\n", encoding="utf-8")
            check_script = knowledge / "scripts" / "kb_check.py"
            check_script.write_text("print('ok')\n", encoding="utf-8")
            custom_policy = knowledge / "policies" / "custom-ingest.md"
            custom_policy.write_text("# Custom ingest policy\n", encoding="utf-8")

            project_rules = MODULE.collect_project_rules(project)
            candidates = MODULE.discover_wiki_candidates(project_rules, project)
            self.assertEqual([str(knowledge.resolve())], [item["path"] for item in candidates])

            wiki_root = MODULE.determine_wiki_root(knowledge / "wiki")
            rules = MODULE.collect_wiki_rules(wiki_root, knowledge / "wiki")
            self.assertIn((knowledge / "CLAUDE.md").resolve(), rules)
            self.assertIn(runbook.resolve(), rules)
            self.assertIn(check_script.resolve(), rules)
            self.assertIn(custom_policy.resolve(), rules)

    def test_unmentioned_env_is_not_a_connection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            vault = root / "vault"
            project.mkdir()
            vault.mkdir()
            (project / "AGENTS.md").write_text("일반 프로젝트 규칙\n", encoding="utf-8")
            previous = os.environ.get("OBSIDIAN_VAULT_PATH")
            os.environ["OBSIDIAN_VAULT_PATH"] = str(vault)
            try:
                rules = MODULE.collect_project_rules(project)
                self.assertEqual([], MODULE.discover_wiki_candidates(rules, project))
            finally:
                if previous is None:
                    os.environ.pop("OBSIDIAN_VAULT_PATH", None)
                else:
                    os.environ["OBSIDIAN_VAULT_PATH"] = previous

    def test_env_named_by_project_rule_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            vault = root / "vault"
            project.mkdir()
            vault.mkdir()
            (project / "CLAUDE.md").write_text(
                "프로젝트 wiki는 `PROJECT_WIKI_PATH`를 사용한다.\n",
                encoding="utf-8",
            )
            previous = os.environ.get("PROJECT_WIKI_PATH")
            os.environ["PROJECT_WIKI_PATH"] = str(vault)
            try:
                rules = MODULE.collect_project_rules(project)
                candidates = MODULE.discover_wiki_candidates(rules, project)
                self.assertEqual([str(vault.resolve())], [item["path"] for item in candidates])
            finally:
                if previous is None:
                    os.environ.pop("PROJECT_WIKI_PATH", None)
                else:
                    os.environ["PROJECT_WIKI_PATH"] = previous

    def test_obsidian_project_note_stays_mapped_to_the_note(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            vault = root / "work-vault"
            note = vault / "01 Projects" / "Example ERP.md"
            project.mkdir()
            (vault / ".obsidian").mkdir(parents=True)
            note.parent.mkdir()
            note.write_text("# Example ERP\n", encoding="utf-8")
            (project / "AGENTS.md").write_text(
                f"프로젝트 wiki는 `{note}`를 사용한다.\n",
                encoding="utf-8",
            )

            rules = MODULE.collect_project_rules(project)
            candidates = MODULE.discover_wiki_candidates(rules, project)
            self.assertEqual([str(note.resolve())], [item["path"] for item in candidates])

    def test_skill_contract_contains_post_deploy_single_batch_gates(self) -> None:
        skill = SCRIPT_PATH.parents[1] / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        required = [
            "운영배포 뒤에만 묻는다",
            "사용자 선택은 한 번 받는다",
            "추천대로",
            "wiki 스킵",
            "추가 승인을 묻지 않는다",
            "재귀 호출을 막는다",
            "exact publish plan",
            "force push·amend·rebase·reset·자동 pull을 하지 않는다",
            "publish_git.py",
            "KNOWNs".upper(),
        ]
        upper_content = content.upper()
        for phrase in required:
            self.assertIn(phrase.upper(), upper_content)


if __name__ == "__main__":
    unittest.main()
