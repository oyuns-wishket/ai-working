import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/sync_agent_assets.py'
SPEC = importlib.util.spec_from_file_location('sync_agent_assets', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AssetSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()

    def put(self, name, content):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def run_sync(self, apply=False, mode='project', config=None):
        return MODULE.Sync(self.root, mode, apply, config).run()

    def test_dry_run_never_mutates(self):
        self.put('.claude/skills/demo/SKILL.md', '# demo\n')
        self.put('CLAUDE.md', '# project rule\n')
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        result = self.run_sync()
        self.assertGreater(result['counts']['change'], 0)
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*')))
        self.assertEqual((self.root / 'CLAUDE.md').read_text(), '# project rule\n')

    def test_apply_links_skill_with_all_support_assets(self):
        source = self.put('.claude/skills/demo/SKILL.md', '# demo\n').parent
        self.put('.claude/skills/demo/scripts/run.py', 'print(1)\n')
        self.run_sync(True)
        dest = self.root / '.agents/skills/demo'
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.resolve(), source.resolve())
        self.assertEqual((dest / 'scripts/run.py').read_text(), 'print(1)\n')
        self.assertEqual(self.run_sync()['counts']['change'], 0)

    def test_different_skill_preserved_even_equal_entrypoint(self):
        self.put('.claude/skills/demo/SKILL.md', '# demo\n')
        self.put('.agents/skills/demo/SKILL.md', '# demo\n')
        self.put('.agents/skills/demo/helper.py', 'original\n')
        result = self.run_sync(True)
        self.assertEqual(result['counts']['conflict'], 1)
        self.assertFalse((self.root / '.agents/skills/demo').is_symlink())
        self.assertEqual((self.root / '.agents/skills/demo/helper.py').read_text(), 'original\n')

    def test_external_skill_config_links_both_home_adapters(self):
        source = Path(self.temp.name) / 'external'
        source.mkdir()
        (source / 'SKILL.md').write_text('# external\n')
        config = {'skill_sources': [{'name': 'external', 'path': str(source)}]}
        result = self.run_sync(True, 'home', config)
        self.assertEqual(result['counts']['applied'], 2)
        for d in ['.claude/skills', '.agents/skills']:
            self.assertEqual((self.root / d / 'external').resolve(), source.resolve())
        self.assertEqual(self.run_sync(False, 'home', config)['counts']['change'], 0)

    def test_project_links_preserve_existing_source_indirection(self):
        external = Path(self.temp.name) / 'private-vendor-source'
        external.mkdir()
        (external / 'SKILL.md').write_text('# external\n')
        source = self.root / '.claude/skills/demo'
        source.parent.mkdir(parents=True)
        source.symlink_to(external, target_is_directory=True)
        self.run_sync(True)
        target = self.root / '.agents/skills/demo'
        import os
        self.assertEqual(os.readlink(target), '../../.claude/skills/demo')
        self.assertNotIn(str(external), os.readlink(target))
        self.assertNotIn('private-vendor-source', os.readlink(target))
        self.assertEqual(self.run_sync()['counts']['change'], 0)

    def test_external_project_source_requires_local_indirection(self):
        external = Path(self.temp.name) / 'private-vendor-source'
        external.mkdir()
        (external / 'SKILL.md').write_text('# external\n')
        config = {'skill_sources': [{'name': 'demo', 'path': str(external)}]}
        result = self.run_sync(True, config=config)
        self.assertEqual(result['counts']['unsupported'], 2)
        self.assertFalse((self.root / '.claude/skills/demo').exists())
        self.assertFalse((self.root / '.agents/skills/demo').exists())

    def test_instruction_bodies_preserved_and_references_idempotent(self):
        original = '# A\n\nKeep existing requirement.\n'
        self.put('AGENTS.md', original)
        self.put('CLAUDE.md', '# C\n\nAnother requirement.\n')
        self.put('.claude/rules/db.md', '---\npaths:\n  - "db/**"\n---\nPrivate body never injected.\n')
        self.run_sync(True)
        a = (self.root / 'AGENTS.md').read_text()
        self.assertTrue(a.startswith(original))
        self.assertIn('`CLAUDE.md`', a)
        self.assertIn('db/**', a)
        self.assertNotIn('Private body', a)
        self.assertNotIn('@CLAUDE.md', a)
        self.assertEqual(self.run_sync()['counts']['change'], 0)
        backups = list((self.root / '.agent/asset-sync-backups').rglob('AGENTS.md'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), original)
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)

    def test_missing_instruction_bridge_has_no_native_import_cycle(self):
        self.put('CLAUDE.md', '# requirements\n')
        self.run_sync(True)
        self.assertIn('`CLAUDE.md`', (self.root / 'AGENTS.md').read_text())
        self.assertNotIn('`AGENTS.md`', (self.root / 'CLAUDE.md').read_text())
        self.assertEqual(self.run_sync()['counts']['change'], 0)

    def test_existing_native_import_not_duplicated(self):
        self.put('CLAUDE.md', '@AGENTS.md\n')
        self.put('AGENTS.md', '# canonical\n')
        self.run_sync(True)
        self.assertNotIn('`CLAUDE.md`', (self.root / 'AGENTS.md').read_text())
        self.assertEqual(self.run_sync()['counts']['change'], 0)

    def test_rule_unknown_metadata_not_reinterpreted(self):
        self.put('CLAUDE.md', '# original\n')
        self.put('.claude/rules/db.md', '---\ncustom: dangerous\n---\nbody\n')
        result = self.run_sync(True)
        self.assertEqual(result['counts']['unsupported'], 1)
        self.assertEqual((self.root / 'CLAUDE.md').read_text(), '# original\n')
        self.assertFalse((self.root / 'AGENTS.md').exists())

    def test_agent_readonly_and_explicit_model_mapping(self):
        self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review changes\nmodel: opus\ndisallowedTools: Write, Edit\n---\nInspect before reporting.\n')
        config = {'model_map': {'opus': 'configured-model'}}
        self.run_sync(True, config=config)
        target = self.root / '.codex/agents/reviewer.toml'
        text = target.read_text()
        self.assertIn('sandbox_mode = "read-only"', text)
        self.assertIn('model = "configured-model"', text)
        self.assertIn('Inspect before reporting.', text)
        config_text = (self.root / '.codex/config.toml').read_text()
        self.assertIn('[agents.\"reviewer\"]', config_text)
        self.assertIn('config_file = \"agents/reviewer.toml\"', config_text)
        self.assertEqual(self.run_sync(config=config)['counts']['change'], 0)

    def test_explicit_model_mapping_can_inherit_native_default(self):
        self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\nmodel: opus\n---\nbody\n')
        result = self.run_sync(True, config={'model_map': {'opus': 'inherit'}})
        text = (self.root / '.codex/agents/reviewer.toml').read_text()
        self.assertNotIn('model =', text)
        self.assertTrue(any('inherited platform default' in row['reason'] for row in result['entries']))

    def test_git_project_state_and_backups_stay_outside_working_tree(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True, capture_output=True)
        self.put('CLAUDE.md', '# original\n')
        self.run_sync(True)
        self.assertFalse((self.root / '.agent').exists())
        self.assertEqual(len(list((self.root / '.git/ai-working-assets').rglob('asset-sync-state.json'))), 1)
        self.assertEqual(len(list((self.root / '.git/ai-working-assets').rglob('CLAUDE.md'))), 1)
        output = subprocess.run(['git', '-C', str(self.root), 'status', '--short', '--untracked-files=all'], capture_output=True, text=True, check=True).stdout
        self.assertNotIn('asset-sync', output)
        self.assertEqual(self.run_sync()['counts']['change'], 0)

    def test_agent_unsupported_restrictions_no_output(self):
        for field in ['tools: Read, Bash', 'disallowedTools: Bash', 'hooks: anything', 'permissionMode: bypassPermissions']:
            with self.subTest(field=field):
                self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n' + field + '\n---\nbody\n')
                result = self.run_sync(True)
                self.assertEqual(result['counts']['unsupported'], 1)
                self.assertFalse((self.root / '.codex/agents/reviewer.toml').exists())

    def test_agent_model_not_silently_dropped(self):
        self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\nmodel: opus\n---\nbody\n')
        result = self.run_sync(True)
        self.assertEqual(result['counts']['unsupported'], 1)
        self.assertFalse((self.root / '.codex/agents/reviewer.toml').exists())

    def test_generated_agent_updates_but_user_modifications_conflict(self):
        source = self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n---\nbody\n')
        self.run_sync(True)
        source.write_text(source.read_text().replace('body', 'changed'))
        self.run_sync(True)
        target = self.root / '.codex/agents/reviewer.toml'
        self.assertIn('changed', target.read_text())
        target.write_text(target.read_text() + '# user customization\n')
        source.write_text(source.read_text().replace('changed', 'newest'))
        result = self.run_sync(True)
        self.assertGreaterEqual(result['counts']['conflict'], 1)
        self.assertIn('user customization', target.read_text())
        self.assertNotIn('newest', target.read_text())

    def test_destination_escape_preserved(self):
        self.put('.claude/skills/demo/SKILL.md', '# demo\n')
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.root / '.agents').symlink_to(outside, target_is_directory=True)
        result = self.run_sync(True)
        self.assertEqual(result['counts']['conflict'], 1)
        self.assertEqual(list(outside.iterdir()), [])

    def test_state_directory_escape_rejected(self):
        outside = Path(self.temp.name) / 'outside-state'
        outside.mkdir()
        (self.root / '.agent').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_sync(True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_instruction_symlink_preserved(self):
        target = Path(self.temp.name) / 'external.md'
        target.write_text('# external\n')
        (self.root / 'CLAUDE.md').symlink_to(target)
        result = self.run_sync(True)
        self.assertGreater(result['counts']['conflict'], 0)
        self.assertEqual(target.read_text(), '# external\n')
        self.assertTrue((self.root / 'CLAUDE.md').is_symlink())

    def test_native_registration_preserves_existing_configuration(self):
        self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n---\nbody\n')
        original = '# keep comment\nmodel = "local-choice"\n[projects."/local/project"]\ntrust_level = "trusted"\n'
        self.put('.codex/config.toml', original)
        self.run_sync(True)
        result = (self.root / '.codex/config.toml').read_text()
        self.assertTrue(result.startswith(original))
        self.assertIn('[agents."reviewer"]', result)
        self.assertEqual(self.run_sync()['counts']['change'], 0)

    def test_existing_native_role_not_overwritten(self):
        self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n---\nbody\n')
        original = '[agents.reviewer]\nconfig_file = "custom.toml"\n'
        self.put('.codex/config.toml', original)
        result = self.run_sync(True)
        self.assertEqual(result['counts']['conflict'], 1)
        self.assertEqual((self.root / '.codex/config.toml').read_text(), original)

    def test_inline_and_quoted_native_agents_configs_preserved(self):
        self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n---\nbody\n')
        for config in ['[agents]\nreviewer = { config_file = "custom.toml" }\n', '["agents"."reviewer"]\nconfig_file = "custom.toml"\n', 'agents = { reviewer = {config_file = "custom.toml"} }\n']:
            with self.subTest(config=config):
                self.put('.codex/config.toml', config)
                result = self.run_sync(True)
                self.assertGreater(result['counts']['conflict'], 0)
                self.assertEqual((self.root / '.codex/config.toml').read_text(), config)

    def test_external_source_conflict_blocks_dependent_codex_generation(self):
        self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Local restricted role\ndisallowedTools: Write, Edit\n---\nlocal body\n')
        external = Path(self.temp.name) / 'reviewer.md'
        external.write_text('---\nname: reviewer\ndescription: External unrestricted role\n---\nexternal body\n')
        config = {'agent_sources': [{'name': 'reviewer', 'path': str(external)}]}
        result = self.run_sync(True, 'home', config)
        self.assertGreater(result['counts']['conflict'], 0)
        self.assertFalse((self.root / '.codex/agents/reviewer.toml').exists())
        self.assertFalse((self.root / '.codex/config.toml').exists())
        self.assertIn('Local restricted role', (self.root / '.claude/agents/reviewer.md').read_text())

    def test_external_agent_source_has_both_native_adapters(self):
        external = Path(self.temp.name) / 'reviewer.md'
        external.write_text('---\nname: reviewer\ndescription: Review\ndisallowedTools: [Write, Edit]\n---\nbody\n')
        config = {'agent_sources': [{'name': 'reviewer', 'path': str(external)}]}
        result = self.run_sync(True, 'home', config)
        self.assertEqual(result['counts']['conflict'], 0)
        self.assertTrue((self.root / '.claude/agents/reviewer.md').is_file())
        self.assertIn('sandbox_mode = "read-only"', (self.root / '.codex/agents/reviewer.toml').read_text())
        self.assertEqual(self.run_sync(False, 'home', config)['counts']['change'], 0)

    def test_modified_managed_config_conflicts(self):
        source = self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n---\nbody\n')
        self.run_sync(True)
        cfg = self.root / '.codex/config.toml'
        cfg.write_text(cfg.read_text().replace('description = "Review"', 'description = "My customized role"'))
        source.write_text(source.read_text().replace('description: Review', 'description: New source description'))
        result = self.run_sync(True)
        self.assertGreater(result['counts']['conflict'], 0)
        self.assertIn('My customized role', cfg.read_text())

    def test_new_unsupported_restriction_unregisters_owned_stale_worker(self):
        source = self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n---\nbody\n')
        self.run_sync(True)
        worker = self.root / '.codex/agents/reviewer.toml'
        original_worker = worker.read_text()
        source.write_text(source.read_text().replace('description: Review', 'description: Review\ntools: Read'))
        result = self.run_sync(True)
        self.assertEqual(result['counts']['unsupported'], 1)
        self.assertNotIn('[agents.', (self.root / '.codex/config.toml').read_text())
        self.assertEqual(worker.read_text(), original_worker)
        self.assertTrue(any('unregister unchanged' in row['reason'] for row in result['entries']))

    def test_deleted_source_unregisters_owned_stale_worker(self):
        source = self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n---\nbody\n')
        self.run_sync(True)
        source.unlink()
        result = self.run_sync(True)
        self.assertNotIn('[agents.', (self.root / '.codex/config.toml').read_text())
        self.assertTrue((self.root / '.codex/agents/reviewer.toml').is_file())
        self.assertGreater(result['counts']['unsupported'], 0)
        self.assertEqual(self.run_sync()['counts']['change'], 0)

    def test_stale_registration_in_modified_config_preserved_and_warned(self):
        source = self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n---\nbody\n')
        self.run_sync(True)
        cfg = self.root / '.codex/config.toml'
        cfg.write_text(cfg.read_text() + '# personal edit\n')
        original = cfg.read_text()
        source.unlink()
        result = self.run_sync(True)
        self.assertEqual(cfg.read_text(), original)
        self.assertTrue(any(row['status'] == 'conflict' and 'active stale' in row['reason'] for row in result['entries']))

    def test_modified_stale_worker_is_not_silently_unregistered(self):
        source = self.put('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: Review\n---\nbody\n')
        self.run_sync(True)
        worker = self.root / '.codex/agents/reviewer.toml'
        worker.write_text(worker.read_text() + '# personal worker edit\n')
        source.unlink()
        result = self.run_sync(True)
        self.assertIn('[agents.', (self.root / '.codex/config.toml').read_text())
        self.assertTrue(any(row['status'] == 'conflict' and 'active stale' in row['reason'] for row in result['entries']))

    def test_codex_only_agent_is_explicitly_unresolved(self):
        self.put('.codex/agents/custom.toml', 'developer_instructions = "custom"\n')
        result = self.run_sync()
        self.assertEqual(result['counts']['unsupported'], 1)

    def test_cli_check_exit_and_no_private_config_echo(self):
        self.put('.claude/skills/demo/SKILL.md', '# demo\n')
        result = subprocess.run([sys.executable, str(SCRIPT), '--project', str(self.root), '--check'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(str(self.root), result.stdout)
        self.assertFalse((self.root / '.agents').exists())
        invalid = self.put('invalid.json', '{"secret_token":"test-secret-do-not-print"}')
        result = subprocess.run([sys.executable, str(SCRIPT), '--home', str(self.root), '--config', str(invalid)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('test-secret', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
