import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('runtime', Path(__file__).resolve().parents[1] / 'scripts/configure_agent_runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeProfileTests(unittest.TestCase):
    def test_preserves_other_settings_and_only_removes_migrated_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'home'
            repo = Path(tmp) / 'repo'
            (home / '.claude').mkdir(parents=True)
            (repo / 'global').mkdir(parents=True)
            (repo / 'global/CLAUDE.md').write_text('shared principle\n')
            wrapper = home / '.claude/CLAUDE.md'
            wrapper.write_text('<!-- OMC:START -->\nold routing\n<!-- OMC:END -->\ncustom text\n## Interaction Principles (Global Override)\nshared principle\n---\n@source\n')
            settings = home / '.claude/settings.json'
            settings.write_text(json.dumps({'env': {'KEEP': 'value', 'OMC_SKIP_HOOKS': 'custom'}, 'hooks': {'Stop': []}, 'enabledPlugins': {'keep': True}}))
            changes = runtime.plan(home, repo)
            self.assertIn('old routing', wrapper.read_text())  # plan is read-only
            backup = runtime.apply_changes(home, changes)
            self.assertIn('old routing', (backup / '.claude/CLAUDE.md').read_text())
            self.assertEqual(wrapper.read_text(), 'custom text\n---\n@source\n')
            current = json.loads(settings.read_text())
            self.assertEqual(current['env']['KEEP'], 'value')
            self.assertTrue(current['enabledPlugins']['keep'])
            self.assertIn('custom', current['env']['OMC_SKIP_HOOKS'])
            self.assertEqual(runtime.plan(home, repo), [])

    def test_unmigrated_preferences_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.claude').mkdir()
            (home / 'global').mkdir()
            (home / 'global/CLAUDE.md').write_text('different')
            wrapper = home / '.claude/CLAUDE.md'
            wrapper.write_text('## Interaction Principles (Global Override)\nunique preference\n---\n')
            runtime.apply_changes(home, runtime.plan(home, home))
            self.assertIn('unique preference', wrapper.read_text())


if __name__ == '__main__':
    unittest.main()
