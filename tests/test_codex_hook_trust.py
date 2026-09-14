import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("codex_hook_trust", Path(__file__).resolve().parents[1] / "scripts/codex_hook_trust.py")
trust = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trust)


def manifest():
    return {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{
        "type": "command", "command": "node $HOME/.claude/hooks/preview-db-guard.mjs", "timeout": 4,
    }]}]}}


def metadata(source, *, command=None):
    return {
        "key": str(source) + ":pre_tool_use:0:0", "sourcePath": str(source),
        "eventName": "preToolUse", "matcher": "Bash", "handlerType": "command",
        "command": command or manifest()["hooks"]["PreToolUse"][0]["hooks"][0]["command"],
        "timeoutSec": 4, "additionalContextLimit": None, "statusMessage": None, "async": False,
        "currentHash": "sha256:" + "a" * 64, "enabled": True, "isManaged": False,
        "trustStatus": "untrusted",
    }


class SelectionTests(unittest.TestCase):
    def test_shared_manifest_transform_preserves_source_and_native_fields(self):
        shared = manifest()
        for event in ["SessionStart", "SessionEnd", "UserPromptSubmit"]:
            shared["hooks"][event] = [{"hooks": [{"type": "command", "command": "node $HOME/.claude/hooks/session-entry.mjs", "timeout": 3}]}]
        original = copy.deepcopy(shared)
        native = trust.native_manifest(shared)
        self.assertEqual(shared, original)
        self.assertEqual(native["hooks"]["SessionEnd"][0]["matcher"], "other")
        self.assertEqual(native["hooks"]["SessionStart"][0]["hooks"][0]["additionalContextLimit"], 10000)
        self.assertEqual(native["hooks"]["UserPromptSubmit"][0]["hooks"][0]["additionalContextLimit"], 1200)
        self.assertEqual(native["hooks"]["PreToolUse"], shared["hooks"]["PreToolUse"])

    def test_exact_definition_and_owned_source_required(self):
        source = Path("/tmp/test-codex/hooks.json")
        good = metadata(source)
        ui = metadata(source, command="paseo hooks codex PreToolUse")
        project = metadata(Path("/tmp/project/.codex/hooks.json"))
        owned, others = trust.select_owned({"hooks": [ui, project, good]}, trust.manifest_fingerprints(manifest()), source)
        self.assertEqual(owned, [good])
        self.assertEqual(others, [ui, project])
        for field, value in [("matcher", "*"), ("timeoutSec", 99), ("command", good["command"] + "; true"), ("statusMessage", "changed")]:
            changed = {**good, field: value}
            with self.subTest(field=field), self.assertRaises(trust.NativeError):
                trust.select_owned({"hooks": [changed]}, trust.manifest_fingerprints(manifest()), source)

    def test_manifest_rejects_unknown_and_shell_chained_commands(self):
        for command in ["paseo hooks codex Stop", "node $HOME/.claude/hooks/test.mjs; true", "bash /tmp/unknown.sh"]:
            value = manifest()
            value["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = command
            with self.subTest(command=command), self.assertRaises(trust.NativeError):
                trust.manifest_fingerprints(value)

    def test_invalid_hash_rejected(self):
        source = Path("/tmp/test-codex/hooks.json")
        hook = {**metadata(source), "currentHash": "unknown-format"}
        with self.assertRaises(trust.NativeError):
            trust.select_owned({"hooks": [hook]}, trust.manifest_fingerprints(manifest()), source)


@unittest.skipUnless(shutil.which("codex"), "native Codex CLI not installed")
class NativeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-working-trust-test-")
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / "codex"
        self.home.mkdir()
        self.config = self.home / "config.toml"
        self.initial_config = '# Keep this unrelated comment.\nmodel_reasoning_effort = "medium"\n'
        self.config.write_text(self.initial_config)
        self.manifest = manifest()
        installed = copy.deepcopy(self.manifest)
        installed["hooks"]["PreToolUse"].append({"matcher": "Bash", "hooks": [{"type": "command", "command": "true", "timeout": 1}]})
        self.hooks_file = self.home / "hooks.json"
        self.hooks_file.write_text(json.dumps(installed))
        env = dict(os.environ, CODEX_HOME=str(self.home))
        self.client = trust.NativeClient(env=env, cwd=self.root)

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def run_sync(self, apply=False):
        return trust.synchronize(self.client, cwd=self.root, codex_home=self.home, manifest=self.manifest, apply=apply)

    def test_dry_run_apply_idempotency_and_external_preservation(self):
        hooks_before = self.hooks_file.read_bytes()
        result = self.run_sync()
        self.assertEqual(result["review_required"], 1)
        self.assertEqual(result["unmanaged_review_required"], 1)
        self.assertEqual(self.config.read_text(), self.initial_config)
        applied = self.run_sync(apply=True)
        self.assertEqual(applied["updated"], 1)
        self.assertEqual(applied["review_required"], 0)
        self.assertEqual(applied["unmanaged_review_required"], 1)
        self.assertTrue(self.config.read_text().startswith(self.initial_config.rstrip()))
        self.assertEqual(self.hooks_file.read_bytes(), hooks_before)
        after = self.config.read_bytes()
        self.assertEqual(self.run_sync(apply=True)["updated"], 0)
        self.assertEqual(self.config.read_bytes(), after)
        # Definition changes invalidate trust; matching only a script name must
        # never cause a silently changed matcher to acquire new trust.
        changed = json.loads(self.hooks_file.read_text())
        changed["hooks"]["PreToolUse"][0]["matcher"] = ".*"
        self.hooks_file.write_text(json.dumps(changed))
        with self.assertRaises(trust.NativeError):
            self.run_sync(apply=True)
        self.assertEqual(self.config.read_bytes(), after)

    def trust_external_then_shift(self, disabled=False):
        external = next(h for h in trust.list_hooks(self.client, self.root)["hooks"] if h.get("command") == "true")
        self.client.request("config/batchWrite", {"edits": [
            {"keyPath": "hooks.state." + json.dumps(external["key"]) + ".trusted_hash",
             "value": external["currentHash"], "mergeStrategy": "replace"},
            {"keyPath": "hooks.state." + json.dumps(external["key"]) + ".enabled",
             "value": not disabled, "mergeStrategy": "replace"},
        ], "filePath": str(self.config)})
        installed = json.loads(self.hooks_file.read_text())
        installed["hooks"]["PreToolUse"].insert(0, {"matcher": "Bash", "hooks": [
            {"type": "command", "command": "printf unknown", "timeout": 1}]})
        self.hooks_file.write_text(json.dumps(installed))

    def test_reviewed_ui_reuses_prior_trust_after_index_shift(self):
        self.trust_external_then_shift()
        before = self.config.read_bytes()
        dry = trust.synchronize(self.client, cwd=self.root, codex_home=self.home,
                                manifest=self.manifest, reviewed_ui=["true"])
        self.assertEqual(dry["reviewed_ui_restorable"], 1)
        self.assertEqual(self.config.read_bytes(), before)
        applied = trust.synchronize(self.client, cwd=self.root, codex_home=self.home,
                                    manifest=self.manifest, reviewed_ui=["true"], apply=True)
        self.assertEqual(applied["reviewed_ui_restored"], 1)
        states = {h.get("command"): h["trustStatus"] for h in trust.list_hooks(self.client, self.root)["hooks"]}
        self.assertEqual(states["true"], "trusted")
        self.assertEqual(states["printf unknown"], "untrusted")

    def test_changed_external_command_cannot_gain_new_trust(self):
        self.trust_external_then_shift()
        installed = json.loads(self.hooks_file.read_text())
        installed["hooks"]["PreToolUse"][2]["hooks"][0]["command"] = "true; printf changed"
        self.hooks_file.write_text(json.dumps(installed))
        before = self.config.read_bytes()
        with self.assertRaisesRegex(trust.NativeError, "no previously trusted"):
            trust.synchronize(self.client, cwd=self.root, codex_home=self.home,
                              manifest=self.manifest, reviewed_ui=["true; printf changed"], apply=True)
        self.assertEqual(self.config.read_bytes(), before)

    def test_prior_disabled_external_is_not_retrusted_after_shift(self):
        self.trust_external_then_shift(disabled=True)
        applied = trust.synchronize(self.client, cwd=self.root, codex_home=self.home,
                                    manifest=self.manifest, reviewed_ui=["true"], apply=True)
        self.assertEqual(applied["reviewed_ui_restored"], 0)
        external = next(h for h in trust.list_hooks(self.client, self.root)["hooks"] if h.get("command") == "true")
        self.assertNotEqual(external["trustStatus"], "trusted")

    def test_instruction_fallback_preserves_existing_names(self):
        self.client.request("config/value/write", {
            "keyPath": "project_doc_fallback_filenames", "value": ["TEAM_GUIDE.md"],
            "mergeStrategy": "replace", "filePath": str(self.config),
        })
        before = self.config.read_bytes()
        result = trust.synchronize(self.client, cwd=self.root, codex_home=self.home,
                                   manifest=self.manifest, ensure_instructions=True)
        self.assertTrue(result["instructions_update_required"])
        self.assertEqual(self.config.read_bytes(), before)
        result = trust.synchronize(self.client, cwd=self.root, codex_home=self.home,
                                   manifest=self.manifest, ensure_instructions=True, apply=True)
        self.assertTrue(result["instructions_fallback"])
        self.assertEqual(self.client.request("config/read", {"cwd": str(self.root)})["config"]["project_doc_fallback_filenames"],
                         ["TEAM_GUIDE.md", "CLAUDE.md"])

    def test_concurrent_user_config_edit_is_not_overwritten(self):
        original = self.client.request
        def racing_request(method, params):
            result = original(method, params)
            if method == "config/read":
                self.config.write_text(self.config.read_text() + '\n# Concurrent user edit.\n')
            return result
        self.client.request = racing_request
        with self.assertRaisesRegex(trust.NativeError, "config changed"):
            self.run_sync(apply=True)
        self.assertIn("Concurrent user edit", self.config.read_text())
        self.assertNotIn("trusted_hash", self.config.read_text())

    def test_disabled_hook_is_not_enabled_or_trusted(self):
        entry = trust.list_hooks(self.client, self.root)
        hook = entry["hooks"][0]
        self.client.request("config/value/write", {
            "keyPath": "hooks.state." + json.dumps(hook["key"]) + ".enabled",
            "value": False, "mergeStrategy": "replace", "filePath": str(self.config),
        })
        before = self.config.read_bytes()
        result = self.run_sync(apply=True)
        self.assertEqual(result["disabled_owned"], 1)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(self.config.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
