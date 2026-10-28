import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[1] / 'hooks/managed-server.py'
spec = importlib.util.spec_from_file_location('managed_server', HELPER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ManagedServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ, AGENT_RESOURCE_GUARD_CACHE_DIR=self.temp.name)
        self.pids = []

    def tearDown(self):
        for pid in self.pids:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.temp.cleanup()

    def call(self, action, *command):
        return json.loads(subprocess.check_output([sys.executable, str(HELPER), '--session', 'test-session', action, *command], env=self.env, text=True))

    def launch(self):
        result = self.call('start', '--', sys.executable, '-c', 'import time; time.sleep(300)')
        self.pids.append(result['pid'])
        return result

    def test_cleanup_isolated_and_removes_log(self):
        result = self.launch()
        bystander = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'])
        try:
            cleaned = self.call('cleanup')
            self.assertEqual(cleaned[0]['status'], 'stopped')
            self.assertIsNone(bystander.poll())
            self.assertFalse(Path(result['log']).exists())
            self.assertEqual(self.call('cleanup'), [])
        finally:
            bystander.terminate()
            bystander.wait()

    def test_identity_mismatch_preserves_process_and_record(self):
        result = self.launch()
        marker = Path(result['log']).with_suffix('.json')
        record = json.loads(marker.read_text())
        record['started'] = 'different-start-time'
        marker.write_text(json.dumps(record))
        self.assertEqual(self.call('cleanup')[0]['status'], 'identity-mismatch')
        self.assertIsNotNone(module.identity(result['pid']))
        self.assertTrue(marker.exists())

    def test_process_only_session_end(self):
        result = self.launch()
        hook = HELPER.parent / 'dev-resource-guard.mjs'
        subprocess.run(['node', str(hook), '--archive-cleanup'], input=json.dumps({'hook_event_name': 'SessionEnd', 'session_id': 'test-session'}), env=self.env, text=True, check=True, capture_output=True)
        receipt = Path(self.temp.name) / 'process-results/test-session.json'
        deadline = time.monotonic() + 8
        while not receipt.exists() and time.monotonic() < deadline:
            time.sleep(.05)
        self.assertEqual(json.loads(receipt.read_text())['results'][0]['status'], 'stopped')
        self.assertFalse(Path(result['log']).exists())

    def test_invalid_identity(self):
        result = subprocess.run([sys.executable, str(HELPER), '--session', '../other', 'cleanup'], env=self.env, capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_probe_failure_is_not_absence(self):
        with patch.object(module.subprocess, 'check_output', side_effect=subprocess.TimeoutExpired('ps', 2)), patch.object(module.os, 'kill', return_value=None):
            with self.assertRaises(RuntimeError):
                module.identity(123)

    def test_orphan_group_preserves_evidence(self):
        root = Path(self.temp.name)
        marker = root / 'processes/test-session/orphan.json'
        marker.parent.mkdir(parents=True)
        marker.write_text(json.dumps({'pid': 99999}))
        with patch.object(module, 'ROOT', root), patch.object(module, 'identity', return_value=None), patch.object(module, 'group_exists', return_value=True):
            result = module.cleanup('test-session')
        self.assertEqual(result[0]['status'], 'orphaned')
        self.assertTrue(marker.exists())
