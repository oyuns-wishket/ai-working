import base64
import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_audit", ROOT / "scripts" / "public_audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(AUDIT)


class PublicAuditTests(unittest.TestCase):
    def categories(self, text: bytes, path: str = "example.txt") -> set[str]:
        return set(AUDIT.scan_blob(path, text, AUDIT.patterns(), history=False))

    def test_extended_secret_formats_are_rejected(self):
        samples = [
            b"xa" + b"pp-1-ABCDEF1234567890",
            b"sk-pro" + b"j-abcdefghijklmnopqrstuvwxyz",
            b"AI" + b"za" + b"A" * 35,
            b"ey" + b"J" + b"A" * 20 + b"." + b"B" * 20 + b"." + b"C" * 20,
        ]
        for sample in samples:
            with self.subTest(sample=sample[:8]):
                self.assertIn("credential", self.categories(sample))

    def test_personal_local_hostname_is_rejected(self):
        self.assertIn("local_hostname", self.categories(b"ssh://my-private-mac." + b"local/path"))

    def test_original_author_checkout_name_is_rejected(self):
        self.assertIn("author_checkout", self.categories(b"$HOME/de" + b"v-oh/ai-working"))

    def test_machine_local_denylist_is_rejected_without_public_values(self):
        encoded = base64.b64encode(b"Example Confidential Name\n").decode()
        with patch.dict(os.environ, {"AI_WORKING_AUDIT_DENYLIST_B64": encoded}, clear=False):
            self.assertIn("local_denylist", self.categories(b"example confidential name"))

    def test_forbidden_history_shapes_are_identified(self):
        self.assertIsNotNone(AUDIT.forbidden_path("memory/session.md"))
        self.assertIsNotNone(AUDIT.forbidden_path("private/data.md"))
        self.assertIsNotNone(AUDIT.forbidden_path("skills/x/__pycache__/x.pyc"))

    def test_reachable_historical_private_path_and_symlink_fail(self):
        with tempfile.TemporaryDirectory(prefix="public-audit-history-") as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            shutil.copy2(ROOT / "scripts" / "public_audit.py", root / "scripts" / "public_audit.py")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "private").mkdir()
            (root / "private" / "data.md").write_text("placeholder\n")
            os.symlink("private/data.md", root / "unsafe-link")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "bad history"], cwd=root, check=True)
            (root / "private" / "data.md").unlink()
            (root / "private").rmdir()
            (root / "unsafe-link").unlink()
            subprocess.run(["git", "add", "-u"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "clean tree"], cwd=root, check=True)
            result = subprocess.run(
                ["python3", "scripts/public_audit.py", "--history"], cwd=root, text=True, capture_output=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("history-tree:private/data.md:private-only directory", result.stderr)
            self.assertIn("history-tree:unsafe-link:unsupported-blob-120000", result.stderr)


if __name__ == "__main__":
    unittest.main()
