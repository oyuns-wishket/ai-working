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

    def add_note(self, name, body="unrelated detail", *, related=None, aliases=None, tags=None, **kwargs):
        path = self.root / "sys-wiki/aidp/alpha" / name
        note(path, body, **kwargs)
        text = path.read_text()
        if related is not None:
            text = text.replace("related: []", "related: " + json.dumps(related))
        for key, value in (("aliases", aliases), ("tags", tags)):
            if value is not None:
                text = text.replace("related:", key + ": " + json.dumps(value, ensure_ascii=False) + "\nrelated:")
        path.write_text(text)
        return path

    def sections(self, rows=None, defaults=None):
        value = contract(self.root)
        if rows is not None:
            value["canonical_sections"] = {"sys-wiki/aidp/alpha": rows}
        if defaults is not None:
            value["default_project_sections"] = defaults
        (self.root / ".system/knowledge-contract.json").write_text(json.dumps(value))

    def test_alias_tag_spacing_matches_are_bounded_whole_phrases(self):
        self.add_note("dispatch.md", aliases=["송장 등록"], tags=["fulfillment"])
        for query in ("송장등록", "송장 등록", "송장등록을 개선", "fulfillment"):
            with self.subTest(query=query):
                document = self.route(query)["documents"][0]
                self.assertTrue(set(document["selection_reasons"]) & {"alias-match", "tag-match"})
        for query in ("등록", "송장등록취소", "prefullfillment"):
            self.assertFalse(self.route(query)["documents"])

    def test_body_spacing_match_without_aliases(self):
        self.add_note("dispatch.md", "송장 등록 업무 원칙")
        self.assertIn("spacing-phrase", self.route("송장등록")["documents"][0]["selection_reasons"])

    def test_invalid_search_metadata_and_relations_are_rejected(self):
        for values in (["term"] * 9, ["x" * 81], ["line\nbreak"], ["delete\x7fcharacter"], [False], ["term", "term"]):
            with self.subTest(values=values):
                self.add_note("bad.md", "shipping", aliases=values)
                self.assertFalse(self.route()["documents"])
        for related in (["KB-BAD"], ["../beta/secret.md"], ["[[KB-OTHER]]"], ["KB-X", "KB-X"], [f"KB-X{i}" for i in range(7)]):
            self.add_note("bad.md", "shipping", related=related)
            self.assertFalse(self.route()["documents"])

    def test_block_metadata_list_is_supported(self):
        path = self.add_note("dispatch.md")
        path.write_text(path.read_text().replace("related: []", 'aliases:\n  - "송장 등록"\n  - shipping\nrelated: []'))
        self.assertTrue(self.route("송장등록")["documents"])

    def test_one_hop_requires_direct_seed_and_never_recurses(self):
        self.entry["retrieval"]["max_documents"] = 4
        self.add_note("seed.md", "shipping", related=["KB-TARGET", "KB-OTHER"])
        self.add_note("target.md", related=["KB-THIRD"])
        self.add_note("other.md")
        self.add_note("third.md")
        result = self.route()
        self.assertEqual([d["id"] for d in result["documents"]], ["KB-SEED", "KB-TARGET"])
        related = result["documents"][1]
        self.assertEqual(related["selection_reasons"], ["related-one-hop"])
        self.assertEqual(related["related_via"]["id"], "KB-SEED")
        self.assertFalse(self.route("no-match")["documents"])

    def test_relation_does_not_displace_direct_results_or_exceed_budget(self):
        self.add_note("seed.md", "shipping", related=["KB-TARGET"])
        self.add_note("direct.md", "shipping")
        self.add_note("target.md")
        result = self.route()
        self.assertEqual({d["id"] for d in result["documents"]}, {"KB-SEED", "KB-DIRECT"})
        (self.root / "sys-wiki/aidp/alpha/direct.md").unlink()
        self.entry["retrieval"]["max_total_bytes"] = (self.root / "sys-wiki/aidp/alpha/seed.md").stat().st_size
        result = self.route()
        self.assertEqual([d["id"] for d in result["documents"]], ["KB-SEED"])
        self.assertLessEqual(result["selected_bytes"], self.entry["retrieval"]["max_total_bytes"])

    def test_relation_targets_must_be_current_canonical_allowed_and_unique(self):
        for kwargs in ({"review": "2020-01-01"}, {"status": "contested"}, {"security": "personal"}, {"customer": "beta"}):
            with self.subTest(kwargs=kwargs):
                self.add_note("seed.md", "shipping", related=["KB-TARGET"])
                self.add_note("target.md", **kwargs)
                self.assertEqual([d["id"] for d in self.route()["documents"]], ["KB-SEED"])
        self.add_note("target.md")
        self.add_note("duplicate.md", note_id="KB-TARGET", review="2020-01-01")
        self.assertEqual([d["id"] for d in self.route()["documents"]], ["KB-SEED"])

    def test_forbidden_corpora_and_dangling_ids_are_not_followed(self):
        self.add_note("seed.md", "shipping", related=["KB-TARGET"])
        for relative, kwargs in (("candidate/target.md", {}), ("raw/target.md", {}),
                                 ("my-wiki/target.md", {}), ("sys-wiki/aidp/beta/target.md", {"customer": "beta"})):
            note(self.root / relative, **kwargs)
        self.assertEqual([d["id"] for d in self.route()["documents"]], ["KB-SEED"])

    def test_manual_notes_are_neither_relation_seeds_nor_targets(self):
        path = self.root / "my-wiki/manual.md"
        note(path, "shipping", note_id="KB-MANUAL", status="draft")
        path.write_text(path.read_text().replace("related: []", 'related: ["KB-TARGET"]'))
        self.entry["manual_read_bindings"] = [{"path": "my-wiki/manual.md", "id": "KB-MANUAL", "security_domain": "work", "customer_scope": "alpha"}]
        self.add_note("target.md")
        self.assertEqual([d["id"] for d in self.route()["documents"]], ["KB-MANUAL"])
        note(path, "unrelated", note_id="KB-MANUAL", status="draft")
        self.add_note("seed.md", "shipping", related=["KB-MANUAL"])
        self.assertEqual([d["id"] for d in self.route()["documents"]], ["KB-SEED"])

    def test_relation_can_read_allowed_common_but_cycles_stop(self):
        self.add_note("seed.md", "shipping", related=["KB-SHARED"])
        shared = self.root / "sys-wiki/aidp/shared.md"
        note(shared, "common evidence", customer="common")
        shared.write_text(shared.read_text().replace("related: []", 'related: ["KB-SEED"]'))
        self.assertEqual([d["id"] for d in self.route()["documents"]], ["KB-SEED", "KB-SHARED"])

    def test_alias_only_large_note_uses_real_body_ranges(self):
        path = self.add_note("large.md", "## Knowledge\n" + "업무 원칙 설명\n" * 3000, aliases=["송장 등록"])
        result = self.route("송장등록")
        document = result["documents"][0]
        self.assertEqual(document["read_mode"], "sections")
        lines = path.read_text().splitlines(keepends=True)
        text = "".join("".join(lines[r["line_start"]-1:r["line_end"]]) for r in document["sections"])
        self.assertNotIn("schema_version:", text)
        self.assertEqual(len(text.encode()), result["selected_bytes"])
        self.assertLessEqual(result["selected_bytes"], 6000)

    def test_declared_one_level_sections_only_and_relation_crosses_sections(self):
        self.sections([{"slug": "orders", "title": "Orders"}, {"slug": "delivery", "title": "Delivery"}])
        self.add_note("orders/seed.md", "shipping", related=["KB-TARGET"])
        self.add_note("delivery/target.md")
        self.add_note("undeclared/hidden.md", "shipping")
        self.add_note("orders/nested/hidden.md", "shipping")
        self.add_note("orders/index.md", "shipping")
        result = self.route()
        self.assertEqual({d["relative_path"] for d in result["documents"]},
                         {"sys-wiki/aidp/alpha/orders/seed.md", "sys-wiki/aidp/alpha/delivery/target.md"})
        self.assertFalse(result["navigation"]["injected"])

    def test_defaults_are_lazy_do_not_expand_common_or_other_customers(self):
        self.sections(defaults=[{"slug": "business", "title": "Business"}])
        self.add_note("business/rules.md", "shipping")
        note(self.root / "sys-wiki/aidp/business/common.md", customer="common")
        note(self.root / "sys-wiki/aidp/beta/business/hidden.md", customer="beta")
        self.assertEqual(self.selected(self.route()), {"sys-wiki/aidp/alpha/business/rules.md"})
        self.sections(rows=[], defaults=[{"slug": "business", "title": "Business"}])
        self.assertFalse(self.route()["documents"])

    def test_unsafe_section_contracts_fail_closed(self):
        for rows in ([{"slug": "../beta", "title": "Bad"}], [{"slug": "raw", "title": "Bad"}],
                     [{"slug": "orders", "title": "Bad", "unknown": True}],
                     [{"slug": "orders", "title": "Bad", "terms": ["x", "x"]}],
                     [{"slug": "orders", "title": "Bad"}] * 2):
            self.sections(rows)
            with self.assertRaises(M.ContextError):
                self.route()
        self.sections([{"slug": "orders", "title": "Orders"}])
        outside = self.root / "candidate/orders"
        outside.mkdir(parents=True)
        (self.root / "sys-wiki/aidp/alpha/orders").symlink_to(outside)
        with self.assertRaises(M.ContextError):
            self.route()

    def test_stale_or_duplicate_seed_cannot_expand_relations(self):
        self.add_note("seed.md", "shipping", related=["KB-TARGET"], review="2020-01-01")
        self.add_note("target.md")
        self.assertFalse(self.route()["documents"])
        self.add_note("seed.md", "shipping", related=["KB-TARGET"])
        self.add_note("duplicate.md", note_id="KB-SEED")
        self.assertFalse(self.route()["documents"])

    def test_large_related_note_keeps_remaining_utf8_budget(self):
        seed = self.add_note("seed.md", "shipping", related=["KB-TARGET"])
        target = self.add_note("target.md", "## Evidence\n" + "업무 지식 설명\n" * 3000)
        result = self.route()
        self.assertEqual(len(result["documents"]), 2)
        document = result["documents"][1]
        self.assertEqual(document["read_mode"], "sections")
        lines = target.read_text().splitlines(keepends=True)
        text = "".join("".join(lines[r["line_start"]-1:r["line_end"]]) for r in document["sections"])
        self.assertEqual(result["selected_bytes"], seed.stat().st_size + len(text.encode()))
        self.assertLessEqual(result["selected_bytes"], 6000)

    def test_undeclared_namespace_contract_fails_closed(self):
        for namespace in (".", "sys-wiki/aidp", "raw/project", "sys-wiki/aidp/alpha/orders", "sys-wiki/../candidate", "sys-wiki/" + "a" * 65, "sys-wiki/raw", "sys-wiki/aidp/index"):
            value = contract(self.root)
            value["canonical_sections"] = {namespace: []}
            (self.root / ".system/knowledge-contract.json").write_text(json.dumps(value))
            with self.assertRaises(M.ContextError):
                self.route()

    def test_section_terms_normalization_and_reserved_long_slugs(self):
        for row in ({"slug": "a" * 65, "title": "Long"},
                    {"slug": "orders", "title": "Orders", "terms": ["Task", " task "]},
                    {"slug": "orders", "title": "Multi\nline"},
                    {"slug": "orders", "title": "Delete\x7f"},
                    {"slug": "orders", "title": "Orders", "terms": ["Delete\x7f"]}):
            self.sections([row])
            with self.assertRaises(M.ContextError):
                self.route()

    def test_common_seed_does_not_expand_customer_knowledge(self):
        shared = self.root / "sys-wiki/aidp/shared.md"
        note(shared, "shipping", customer="common")
        shared.write_text(shared.read_text().replace("related: []", 'related: ["KB-TARGET"]'))
        self.add_note("target.md")
        self.assertEqual([d["id"] for d in self.route()["documents"]], ["KB-SHARED"])

    def test_normalized_duplicate_signals_cannot_inflate_scores(self):
        self.add_note("dispatch.md", aliases=["Task", " task "])
        self.assertFalse(self.route("task")["documents"])
        self.add_note("dispatch.md", aliases=["송장 등록", "송장등록"])
        document = self.route("송장등록")["documents"][0]
        self.assertEqual(document["score"], 30)
        self.assertEqual(len(document["matched_aliases"]), 1)

    def test_block_search_metadata_rejects_nonstring_scalars(self):
        for key in ("aliases", "tags"):
            for scalar in ("false", " false ", "null", "123", "[]", "{}", '["nested"]'):
                with self.subTest(key=key, scalar=scalar):
                    path = self.add_note("bad.md", "shipping")
                    path.write_text(path.read_text().replace("related: []", f"{key}:\n  - {scalar}\nrelated: []"))
                    self.assertFalse(self.route()["documents"])
        path = self.add_note("bad.md")
        path.write_text(path.read_text().replace("related: []", 'aliases:\n  - "false"\nrelated: []'))
        self.assertTrue(self.route("false")["documents"])

    def test_nested_intent_matches_namespace_relative_path(self):
        self.sections([{"slug": "engineering", "title": "Engineering"}])
        self.add_note("engineering/landscape.md")
        self.entry["retrieval"]["intent_routes"] = {"architecture": {"terms": ["architecture"], "documents": ["engineering/landscape.md"]}}
        result = self.route("architecture")
        self.assertEqual(self.selected(result), {"sys-wiki/aidp/alpha/engineering/landscape.md"})
        self.assertEqual(result["documents"][0]["selection_reasons"], ["intent-route"])


if __name__ == "__main__":
    unittest.main()
