"""Behavior checks for scoped routing, manual ownership, and late-section recall."""
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/wiki_context.py"
SPEC = importlib.util.spec_from_file_location("wiki_context_v2_test", SCRIPT)
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def contract(root):
    value = {"schema_version": 2, "paths": {
        "canonical": "sys-wiki", "candidate": "candidate", "manual": "my-wiki",
        "registry": ".system/registry/project-registry.json",
        "registry_schema": ".system/registry/project-registry.schema.json",
        "schema": ".system/schemas/canonical-note.schema.json", "template": ".system/templates/canonical-note.md"}}
    path = root / ".system/knowledge-contract.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return value


def note(path, body="shipping", *, customer="alpha", security="work", status="canonical", review="2099-01-01", note_id=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'''---
schema_version: 2
id: {note_id or "KB-" + path.stem.upper().replace("-", "_")}
title: {path.stem}
type: domain
status: {status}
owner: reviewer
security_domain: {security}
customer_scope: {customer}
verified_at: 2026-01-01
review_by: {review}
source_refs:
  - user-confirmation:2026-01-01
related: []
---
# {path.stem}
{body}
''')


class V2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "knowledge"
        self.repo = self.base / "project"
        subprocess.run(["git", "init", str(self.repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", "https://example.invalid/team/product"], check=True)
        contract(self.root)
        self.entry = {"id": "example.invalid/team/product", "canonical_remote": "https://example.invalid/team/product",
                      "remote_aliases": [], "local_aliases": ["project"], "connection_status": "connected",
                      "wiki_namespace": "sys-wiki/aidp/alpha", "canonical_write_target": "sys-wiki/aidp/alpha",
                      "security_domain": "work/customer/alpha", "customer_scope": "alpha",
                      "read_scopes": [{"path": "sys-wiki/aidp/alpha", "recursive": False, "security_domain": "work", "customer_scope": "alpha"},
                                      {"path": "sys-wiki/aidp", "recursive": False, "security_domain": "work", "customer_scope": "common"}],
                      "manual_read_bindings": [], "retrieval": {"max_documents": 2}}
        self.registry = {"schema_version": 2, "defaults": {"retrieval": {"max_total_bytes": 6000}}, "projects": [self.entry]}
        note(self.root / "sys-wiki/aidp/alpha/index.md", "navigation")
        note(self.root / "sys-wiki/aidp/index.md", "common navigation", customer="common")
        self.save()

    def save(self):
        path = self.root / ".system/registry/project-registry.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(self.registry))

    def route(self, query="shipping"):
        self.save()
        return M.routed_documents(M.resolve(self.repo, str(self.root)), query)

    def selected(self, result):
        return {d["relative_path"] for d in result.get("query_documents", [])}

    def test_defaults_merge_and_customer_isolation(self):
        note(self.root / "sys-wiki/aidp/alpha/rules.md")
        note(self.root / "sys-wiki/aidp/beta/rules.md", customer="beta")
        note(self.root / "sys-wiki/aidp/shared.md", customer="common")
        result = self.route()
        self.assertEqual(result["project"]["retrieval"]["max_total_bytes"], 6000)
        self.assertEqual(self.selected(result), {"sys-wiki/aidp/alpha/rules.md", "sys-wiki/aidp/shared.md"})
        self.assertLessEqual(result["selected_bytes"], 6000)

    def test_common_only_reads_direct_common_documents(self):
        self.entry.update(connection_status="common-only", wiki_namespace=None, canonical_write_target=None,
                          read_scopes=[self.entry["read_scopes"][1]])
        note(self.root / "sys-wiki/aidp/common.md", customer="common")
        note(self.root / "sys-wiki/aidp/beta/secret.md", customer="beta")
        result = self.route()
        self.assertEqual(result["mode"], "wiki-bounded")
        self.assertEqual(self.selected(result), {"sys-wiki/aidp/common.md"})
        self.assertIsNone(result["canonical_write_target"])

    def test_wrong_security_stale_contested_and_wrong_customer_rejected(self):
        note(self.root / "sys-wiki/aidp/alpha/personal.md", security="personal")
        note(self.root / "sys-wiki/aidp/alpha/wrong.md", customer="beta")
        note(self.root / "sys-wiki/aidp/alpha/old.md", review="2020-01-01")
        note(self.root / "sys-wiki/aidp/alpha/contested.md", status="contested")
        self.assertFalse(self.selected(self.route()))
        self.assertEqual(len(self.route()["rejected"]), 4)

    def test_manual_note_requires_exact_optin_id_and_unlink_is_immediate(self):
        path = self.root / "my-wiki/customer-meeting.md"
        note(path, status="draft", note_id="MANUAL-1")
        self.assertFalse(self.selected(self.route()))
        self.entry["manual_read_bindings"] = [{"path": "my-wiki/customer-meeting.md", "id": "MANUAL-1", "security_domain": "work", "customer_scope": "alpha"}]
        result = self.route()
        self.assertEqual(self.selected(result), {"my-wiki/customer-meeting.md"})
        self.assertEqual(result["query_documents"][0]["corpus"], "manual")
        self.assertEqual(result["query_documents"][0]["status"], "draft")
        self.assertEqual(result["canonical_write_target"], str(self.root / "sys-wiki/aidp/alpha"))
        self.entry["manual_read_bindings"][0]["id"] = "WRONG"
        self.assertFalse(self.selected(self.route()))
        self.entry["manual_read_bindings"] = []
        self.assertFalse(self.selected(self.route()))

    def test_late_section_is_recalled_with_real_budgeted_line_ranges(self):
        path = self.root / "sys-wiki/aidp/alpha/large.md"
        note(path, "## Background\n" + ("irrelevant context\n" * 5000) + "## Reconciliation\nshipping reconciliation invariant\n")
        result = self.route("reconciliation")
        document = result["query_documents"][0]
        self.assertEqual(document["read_mode"], "sections")
        self.assertLessEqual(result["selected_bytes"], 6000)
        lines = path.read_text().splitlines(keepends=True)
        selected = "".join("".join(lines[r["line_start"]-1:r["line_end"]]) for r in document["sections"])
        self.assertIn("shipping reconciliation invariant", selected)
        self.assertEqual(document["bytes"], len(selected.encode()))
        self.assertGreater(document["sections"][0]["line_start"], 5000)

    def test_symlink_escape_and_candidate_never_selected(self):
        outside = self.root / "candidate/secret.md"
        note(outside)
        (self.root / "sys-wiki/aidp/alpha/escape.md").symlink_to(outside)
        self.assertFalse(self.selected(self.route()))
        self.assertTrue(self.route()["rejected"])

    def test_cross_customer_registry_and_manual_write_targets_are_invalid(self):
        self.entry["read_scopes"][0]["path"] = "sys-wiki/aidp/beta"
        self.save()
        with self.assertRaises(M.ContextError):
            M.load_registry(self.root)
        self.entry["read_scopes"][0]["path"] = "sys-wiki/aidp/alpha"
        self.entry["canonical_write_target"] = "my-wiki/meeting.md"
        self.save()
        with self.assertRaises(M.ContextError):
            M.load_registry(self.root)

    def test_adapter_resolves_owning_contract_without_data_copy(self):
        adapter = self.base / "adapter/registry"
        adapter.mkdir(parents=True)
        (adapter / "knowledge-root.json").write_text(json.dumps({"knowledge_root": str(self.root)}))
        self.assertEqual(M.find_wiki_root(str(adapter.parent)), self.root)
        (self.root / ".system/knowledge-contract.json").unlink()
        with self.assertRaises(M.ContextError):
            M.find_wiki_root(str(adapter.parent))

    def test_fifo_is_rejected_without_waiting_for_a_writer(self):
        path = self.root / "sys-wiki/aidp/alpha/pipe.md"
        os.mkfifo(path)
        self.assertFalse(self.selected(self.route()))
        self.assertEqual(self.route()["rejected"][0]["reason"], "not a regular document")

    def test_owner_qualified_repository_source_is_actually_checked(self):
        path = self.root / "sys-wiki/aidp/alpha/rules.md"
        note(path)
        path.write_text(path.read_text().replace("user-confirmation:2026-01-01", "repo:team/product@deadbeef/missing.py"))
        result = self.route()
        self.assertFalse(self.selected(result))
        self.assertEqual(result["rejected"][0]["reason"], "invalid-source-ref")

    def test_inline_json_source_refs_used_by_owner_renderer(self):
        path = self.root / "sys-wiki/aidp/alpha/rules.md"
        note(path)
        path.write_text(path.read_text().replace("source_refs:\n  - user-confirmation:2026-01-01", 'source_refs: ["user-confirmation:2026-01-01"]'))
        self.assertEqual(self.selected(self.route()), {"sys-wiki/aidp/alpha/rules.md"})

    def test_bare_index_is_navigation_only_without_fabricated_freshness(self):
        (self.root / "sys-wiki/aidp/alpha/index.md").write_text("# Navigation\n[sibling secret](../beta/secret.md)")
        note(self.root / "sys-wiki/aidp/alpha/rules.md")
        result = self.route()
        self.assertFalse(result["navigation"]["injected"])
        self.assertIsNone(result["index_document"])
        self.assertEqual(len(result["documents"]), 1)

    def test_duplicate_metadata_and_missing_source_not_accepted(self):
        path = self.root / "sys-wiki/aidp/alpha/duplicate.md"
        note(path)
        path.write_text(path.read_text().replace("status: canonical", "status: canonical\nstatus: canonical"))
        self.assertFalse(self.selected(self.route()))
        self.assertIn("duplicate", self.route()["rejected"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
