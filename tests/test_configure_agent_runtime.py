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

class OmcRetirementTests(unittest.TestCase):
    def test_retired_omc_is_not_reenabled_and_only_its_status_is_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.claude').mkdir()
            (home / '.config/ai-working').mkdir(parents=True)
            (home / 'global').mkdir()
            (home / 'global/CLAUDE.md').write_text('shared')
            profile = home / '.config/ai-working/runtime-profile.json'
            profile.write_text(json.dumps({'omc_mode': 'removed', 'native_statusline': True}))
            settings = home / '.claude/settings.json'
            settings.write_text(json.dumps({'env': {'KEEP': 'value', 'OMC_SKIP_HOOKS': 'old'}, 'enabledPlugins': {'oh-my-claudecode@omc': True, 'other': True}, 'statusLine': {'type': 'command', 'command': 'sh /example/hud/omc-hud-cache.sh'}}))
            runtime.apply_changes(home, runtime.plan(home, home))
            current = json.loads(settings.read_text())
            self.assertNotIn('OMC_SKIP_HOOKS', current['env'])
            self.assertEqual(current['env']['KEEP'], 'value')
            self.assertFalse(current['enabledPlugins']['oh-my-claudecode@omc'])
            self.assertTrue(current['enabledPlugins']['other'])
            self.assertEqual(current['statusLine']['command'], 'node "$HOME/.claude/statusline.mjs"')
            self.assertEqual(runtime.plan(home, home), [])
            current['statusLine'] = {'type': 'command', 'command': 'custom-status'}
            settings.write_text(json.dumps(current))
            self.assertEqual(runtime.plan(home, home), [])


if __name__ == '__main__':
    unittest.main()
