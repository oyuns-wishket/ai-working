"""CLI regression tests: plans do not install; audit cannot install; providers agree."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/design-workflow/scripts/setup_design_tools.py'


class DesignToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.marker = self.root / 'calls'
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ.get('PATH', ''))
        self.stub('node', "print('v22.12.0')")
        self.stub('npx', '''
import sys
from pathlib import Path
args = sys.argv[1:]
name = args[args.index('--skill') + 1] if '--skill' in args else 'impeccable'
for provider in ('.claude', '.agents'):
    target = Path.cwd() / provider / 'skills' / name
    target.mkdir(parents=True, exist_ok=True)
    (target / 'SKILL.md').write_text('---\\nname: ' + name + '\\n---\\nShared fixture\\n')
''')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text('#!' + sys.executable + '\nfrom pathlib import Path\n'
                        + 'with Path(' + repr(str(self.marker)) + ").open('a') as log: log.write("
                        + repr(name + '\n') + ')\n' + body + '\n')
        path.chmod(0o755)

    def cli(self, mode, *extra, project=None):
        return subprocess.run([sys.executable, str(SCRIPT), '--project', str(project or self.project),
                               '--mode', mode, '--json', *extra], env=self.env,
                              text=True, capture_output=True)

    def files(self):
        return {p.relative_to(self.project).as_posix(): p.read_bytes()
                for p in self.project.rglob('*') if p.is_file()
                and '.git' not in p.relative_to(self.project).parts}

    def installed(self, provider, content='same', name='impeccable'):
        path = self.project / provider / 'skills' / name
        path.mkdir(parents=True)
        (path / 'SKILL.md').write_text(content)
        return path

    def test_audit_plan_is_empty_and_does_not_need_node(self):
        (self.bin / 'node').unlink()
        before = self.files()
        result = self.cli('audit', '--taste-skill', 'gpt-taste')
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan['commands'], [])
        self.assertEqual(plan['expected_files'], [])
        self.assertIsNone(plan['taste_skill'])
        self.assertEqual(self.files(), before)
        self.assertFalse(self.marker.exists())

    def test_audit_apply_rejected_before_tool_execution(self):
        before = self.files()
        result = self.cli('audit', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('read-only', json.loads(result.stdout)['error'])
        self.assertEqual(self.files(), before)
        self.assertFalse(self.marker.exists())

    def test_new_dry_run_plans_but_does_not_install(self):
        before = self.files()
        result = self.cli('new')
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual([c['name'] for c in plan['commands']], ['taste', 'impeccable'])
        self.assertEqual(self.files(), before)
        self.assertNotIn('npx', self.marker.read_text())

    def test_apply_installs_both_providers_and_is_idempotent(self):
        first = self.cli('small-feature', '--apply')
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertTrue(all(s['complete'] for s in json.loads(first.stdout)['states_after']))
        before = self.files()
        self.marker.unlink()
        second = self.cli('small-feature', '--apply')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)['commands'], [])
        self.assertEqual(self.files(), before)
        self.assertNotIn('npx', self.marker.read_text())

    def test_partial_provider_is_preserved(self):
        self.installed('.claude')
        before = self.files()
        result = self.cli('small-feature', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.files(), before)
        self.assertNotIn('npx', self.marker.read_text())

    def test_differing_supporting_files_are_not_overwritten(self):
        for provider in ('.claude', '.agents'):
            path = self.installed(provider)
            (path / 'reference.md').write_text(provider)
        before = self.files()
        result = self.cli('small-feature', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('differing', json.loads(result.stdout)['error'])
        self.assertEqual(self.files(), before)
        self.assertNotIn('npx', self.marker.read_text())

    def test_empty_directories_are_not_valid_installations(self):
        for provider in ('.claude', '.agents'):
            (self.project / provider / 'skills' / 'impeccable').mkdir(parents=True)
        result = self.cli('small-feature', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Invalid', json.loads(result.stdout)['error'])
        self.assertFalse(any(self.files()))
        self.assertNotIn('npx', self.marker.read_text())

    def test_provider_runtime_cache_does_not_force_reinstall(self):
        first = self.installed('.claude')
        self.installed('.agents')
        cache = first / '__pycache__'
        cache.mkdir()
        (cache / 'local.pyc').write_bytes(b'local runtime cache')
        result = self.cli('small-feature')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['commands'], [])

    def test_empty_entrypoints_are_not_valid_installations(self):
        for provider in ('.claude', '.agents'):
            self.installed(provider, content='  \n')
        before = self.files()
        result = self.cli('small-feature', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.files(), before)
        self.assertNotIn('npx', self.marker.read_text())

    def test_plain_audit_does_not_suggest_apply(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.project),
                                 '--mode', 'audit'], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('--apply', result.stdout)
        self.assertFalse(self.marker.exists())

    def test_nested_project_rejected_without_installation(self):
        nested = self.project / 'nested'
        nested.mkdir()
        result = self.cli('small-feature', '--apply', project=nested)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Git project root', json.loads(result.stdout)['error'])
        self.assertFalse(self.marker.exists())


if __name__ == '__main__':
    unittest.main()
