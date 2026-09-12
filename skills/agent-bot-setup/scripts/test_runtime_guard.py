"""Behavioral filesystem regressions; live native OS policy uses the probe CLI."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import runtime_guard as guard


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agent-guard-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "source"
        self.source.mkdir()
        self.private = self.root / "private"
        self.private.mkdir(mode=0o700)
        self.file = self.source / "read.txt"
        self.file.write_text("approved source")
        self.manifest = self.source / guard.MANIFEST
        self.manifest.write_text(
            json.dumps(
                {
                    "files": {
                        "read.txt": hashlib.sha256(self.file.read_bytes()).hexdigest(),
                    }
                }
            )
        )
        # Filesystem validation tests use a synthetic header, never execute it.
        self.binary = self.root / "native-fixture"
        self.binary.write_bytes(b"\x7fELF")
        self.binary.chmod(0o700)

    def render(self, target=None):
        return guard.render(
            self.source, self.binary, target or self.private / "config.toml"
        )

    def test_valid_projection_and_private_output(self):
        self.assertEqual(guard.verify_projection(self.source), self.source)
        output = self.render()
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        self.assertTrue(output.read_text())

    def test_detects_modified_and_extra_files(self):
        self.file.write_text("unreviewed change")
        with self.assertRaises(ValueError):
            self.render()
        self.file.write_text("approved source")
        (self.source / "extra.txt").write_text("unlisted")
        with self.assertRaises(ValueError):
            self.render()
        self.assertFalse((self.private / "config.toml").exists())

    def test_symlinks_and_fifo_fail_before_output(self):
        link = self.source / "escape"
        link.symlink_to(self.private, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.render()
        link.unlink()
        os.mkfifo(link)
        with self.assertRaises(ValueError):
            self.render()

    def test_symlink_manifest_rejected(self):
        self.manifest.rename(self.root / "manifest")
        self.manifest.symlink_to(self.root / "manifest")
        with self.assertRaises(ValueError):
            self.render()

    def test_traversal_manifest_cannot_authorize_other_files(self):
        self.manifest.write_text(json.dumps({"files": {"../native-fixture": "a" * 64}}))
        with self.assertRaises(ValueError):
            self.render()

    def test_non_object_manifest_rejected_without_output(self):
        self.manifest.write_text("[]")
        with self.assertRaises(TypeError):
            self.render()
        self.assertFalse((self.private / "config.toml").exists())

    def test_no_overwrite_or_symlink_follow(self):
        target = self.private / "config.toml"
        target.write_text("existing config")
        with self.assertRaises(FileExistsError):
            self.render()
        self.assertEqual(target.read_text(), "existing config")
        target.unlink()
        target.symlink_to(self.root / "absent")
        with self.assertRaises(FileExistsError):
            self.render()
        self.assertFalse((self.root / "absent").exists())

    def test_state_must_be_private_and_separate(self):
        self.private.chmod(0o755)
        with self.assertRaises(ValueError):
            self.render()
        with self.assertRaises(ValueError):
            self.render(self.source / "config.toml")
        self.root.chmod(0o700)
        with self.assertRaises(ValueError):
            self.render(self.root / "config.toml")

    def test_wrapper_rejected(self):
        self.binary.write_text("#!/bin/sh\nexit 0\n")
        with self.assertRaises(ValueError):
            self.render()

    def test_host_environment_not_inherited(self):
        with patch.dict(
            os.environ,
            {"AWS_SECRET_ACCESS_KEY": "synthetic", "SLACK_BOT_TOKEN": "synthetic"},
        ):
            env = guard.runtime_environment(self.private)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        self.assertNotIn("SLACK_BOT_TOKEN", env)
        self.assertEqual(env["CODEX_HOME"], str(self.private))

    def test_cleanup_continues_after_signal_permission_error(self):
        client = object.__new__(guard.NativeProbe)
        client.process = MagicMock(pid=12345)
        client.selector = MagicMock()
        with (
            patch.object(guard.os, "killpg", side_effect=PermissionError) as kill,
            self.assertRaises(RuntimeError),
        ):
            client.close()
        self.assertEqual(kill.call_count, 2)
        self.assertEqual(client.process.wait.call_count, 3)
        client.selector.close.assert_called_once()
        client.process.stdin.close.assert_called_once()
        client.process.stdout.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
