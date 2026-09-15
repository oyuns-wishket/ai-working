"""Knowns must discover the owner contract and reject manual read bindings as writes."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("knowns_v2_test", Path(__file__).with_name("inspect_context.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class V2DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "knowledge"
        self.target = self.root / "sys-wiki/aidp/alpha"
        self.target.mkdir(parents=True)
        self.manual = self.root / "my-wiki/meeting.md"
        self.manual.parent.mkdir()
        self.manual.write_text("# A user-owned note\n")
        self.contract = {"schema_version": 2, "paths": {
            "canonical": "sys-wiki", "candidate": "candidate", "manual": "my-wiki",
            "registry": ".system/registry/project-registry.json", "registry_schema": ".system/registry/project-registry.schema.json",
            "schema": ".system/schemas/canonical-note.schema.json", "template": ".system/templates/canonical-note.md"}}
        for key in ("schema", "template", "registry_schema"):
            path = self.root / self.contract["paths"][key]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}")
        self.contract_path = self.root / ".system/knowledge-contract.json"
        self.contract_path.write_text(json.dumps(self.contract))
        (self.root / "CLAUDE.md").write_text("Use the owning knowledge contract.")

    def test_owner_contract_schema_template_are_discovered_without_note_scan(self):
        rules = M.seed_wiki_rules(self.root, self.target)
        self.assertIn(self.contract_path, rules)
        self.assertIn(self.root / self.contract["paths"]["template"], rules)
        self.assertNotIn(self.manual, rules)

    def test_read_bound_manual_and_other_customer_are_never_write_targets(self):
        M.validate_canonical_write_target(self.root, self.target / "new.md", self.target)
        for path in (self.manual, self.root / "sys-wiki/aidp/beta/new.md", self.root):
            with self.assertRaises(ValueError):
                M.validate_canonical_write_target(self.root, path, self.target)

    def test_symlink_write_escape_rejected(self):
        (self.target / "alias").symlink_to(self.manual.parent)
        with self.assertRaises(ValueError):
            M.validate_canonical_write_target(self.root, self.target / "alias/meeting.md", self.target)

    def test_owner_contract_escape_rejected(self):
        self.contract["paths"]["template"] = "../outside.md"
        self.contract_path.write_text(json.dumps(self.contract))
        with self.assertRaises(ValueError):
            M.discover_knowledge_contract(self.root)


if __name__ == "__main__":
    unittest.main()
