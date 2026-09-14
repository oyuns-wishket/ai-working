#!/usr/bin/env python3
"""Synchronize explicitly scoped agent assets; dry-run unless --apply is supplied."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

BEGIN = '<!-- BEGIN AI-WORKING ASSET REFERENCES -->'
END = '<!-- END AI-WORKING ASSET REFERENCES -->'
MAX_FILE = 256 * 1024
MAX_RULES = 100
CONFIG_BEGIN = '# BEGIN AI-WORKING AGENT REGISTRATIONS'
CONFIG_END = '# END AI-WORKING AGENT REGISTRATIONS'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_text(path):
    if path.stat().st_size > MAX_FILE:
        raise ValueError('file exceeds 256 KiB inspection limit')
    return path.read_text(encoding='utf-8')


def exists(path):
    return path.exists() or path.is_symlink()


def safe_name(name):
    return bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', name))


def scalar(value):
    value = value.strip()
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith(('[', '{', '&', '*', '!')):
        raise ValueError('unsupported YAML scalar')
    return value


def frontmatter(text):
    """Small fail-closed YAML subset, not a permissive YAML reinterpretation."""
    if not text.startswith('---\n'):
        return {}, text
    end = text.find('\n---\n', 4)
    if end < 0:
        raise ValueError('unterminated frontmatter')
    lines = text[4:end].splitlines()
    result = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z][A-Za-z0-9_-]*):\s*(.*)', line)
        if not match or match[1] in result:
            raise ValueError('unsupported or duplicate frontmatter field')
        key, value = match.groups()
        if value in ('|', '>'):
            parts = []
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith('  ')):
                parts.append(lines[i][2:] if lines[i].startswith('  ') else '')
                i += 1
            result[key] = ('\n' if value == '|' else ' ').join(parts).strip()
        elif value == '':
            parts = []
            while i < len(lines) and re.match(r'^\s*- ', lines[i]):
                parts.append(scalar(re.sub(r'^\s*- ', '', lines[i])))
                i += 1
            result[key] = parts
        elif value.startswith('[') and value.endswith(']'):
            result[key] = [scalar(x) for x in value[1:-1].split(',') if x.strip()]
        else:
            result[key] = scalar(value)
    return result, text[end + 5:]


class Sync:
    def __init__(self, root, mode, apply=False, config=None):
        self.root = root.resolve()
        self.mode = mode
        self.apply = apply
        self.config = config or {}
        self.entries = []
        self.actions = []
        state_rel = '.config/ai-working/asset-sync-state.json' if mode == 'home' else '.agent/asset-sync-state.json'
        self.state_path = self.root / state_rel
        self.state_boundary = self.root
        if mode == 'project':
            try:
                git = subprocess.run(['git', '-C', str(self.root), 'rev-parse', '--git-common-dir'],
                                     capture_output=True, text=True, timeout=3, check=False)
                if git.returncode == 0:
                    common = Path(git.stdout.strip())
                    if not common.is_absolute():
                        common = self.root / common
                    common = common.resolve()
                    if common.is_dir():
                        self.state_boundary = common
                        scope_key = digest(str(self.root).encode())[:16]
                        self.state_path = common / 'ai-working-assets' / scope_key / 'asset-sync-state.json'
            except (OSError, subprocess.TimeoutExpired):
                pass
        if self.state_path.is_symlink() or not self.state_path.parent.resolve().is_relative_to(self.state_boundary):
            raise ValueError('sync state must remain inside selected scope')
        self.state = {'schema_version': 1, 'generated': {}}
        if self.state_path.is_file():
            loaded = json.loads(read_text(self.state_path))
            if loaded.get('schema_version') != 1 or not isinstance(loaded.get('generated'), dict):
                raise ValueError('unsupported sync state')
            self.state = loaded
        self.backup_root = self.state_path.parent / 'asset-sync-backups' / f'{time.time_ns()}'

    def report(self, path, status, reason):
        try:
            label = str(path.relative_to(self.root))
        except ValueError:
            label = path.name
        self.entries.append({'path': label, 'status': status, 'reason': reason})

    def local_destination(self, path):
        # Never follow a destination parent symlink outside the selected scope.
        return path.parent.resolve().is_relative_to(self.root)

    def write(self, path, data, reason, managed=False):
        if not self.local_destination(path):
            self.report(path, 'conflict', 'destination parent escapes selected scope')
            return
        raw = data.encode('utf-8')
        if exists(path):
            if path.is_symlink() or not path.is_file():
                self.report(path, 'conflict', 'existing symlink or non-regular file preserved')
                return
            if path.stat().st_size > MAX_FILE:
                self.report(path, 'unsupported', 'existing destination exceeds inspection limit')
                return
            old = path.read_bytes()
            if old == raw:
                self.report(path, 'ok', reason)
                return
            owned = self.state['generated'].get(str(path.relative_to(self.root))) == digest(old)
            has_managed_block = BEGIN.encode() in old or CONFIG_BEGIN.encode() in old
            if (not managed or has_managed_block) and not owned:
                self.report(path, 'conflict', 'existing differing content preserved')
                return
        self.actions.append(('write', path, raw, path.read_bytes() if path.is_file() else None))
        self.report(path, 'change', reason)

    def link(self, path, source):
        if not self.local_destination(path):
            self.report(path, 'conflict', 'destination parent escapes selected scope')
            return
        if exists(path):
            if path.resolve() == source.resolve():
                self.report(path, 'ok', 'same canonical skill source')
            elif path.is_dir() and (path / 'SKILL.md').is_file():
                # Equal entrypoint alone does not establish equal scripts/references.
                self.report(path, 'conflict', 'different skill source preserved, including support files')
            else:
                self.report(path, 'conflict', 'existing destination preserved')
            return
        if self.mode == 'project' and not source.absolute().is_relative_to(self.root):
            self.report(path, 'unsupported', 'external project skill requires an existing project-local source indirection')
            return
        # Project adapters point at the existing in-project entry, preserving its
        # own symlink indirection instead of publishing a machine-specific vendor path.
        link_source = source.absolute() if self.mode == 'project' else source.resolve()
        self.actions.append(('link', path, link_source, None))
        self.report(path, 'change', 'link missing skill counterpart to its existing source')

    def skills(self):
        left = self.root / '.claude/skills'
        right = self.root / '.agents/skills'
        sources = {}
        for folder in (left, right):
            if not folder.is_dir():
                continue
            for entry in sorted(folder.iterdir()):
                if safe_name(entry.name) and (entry / 'SKILL.md').is_file():
                    sources.setdefault(entry.name, entry)
        for item in self.config.get('skill_sources', []):
            if not isinstance(item, dict) or not safe_name(item.get('name', '')):
                raise ValueError('skill_sources requires safe names and explicit source paths')
            source = Path(item.get('path', '')).expanduser()
            if not source.is_absolute() or not (source / 'SKILL.md').is_file():
                raise ValueError('skill source must be an absolute existing skill directory')
            sources[item['name']] = source
        for name, source in sorted(sources.items()):
            for folder in (left, right):
                self.link(folder / name, source)

    def references(self):
        if self.mode != 'project':
            return
        docs = [self.root / 'AGENTS.md', self.root / 'CLAUDE.md']
        if not any(p.is_file() for p in docs):
            return
        rules_dir = self.root / '.claude/rules'
        rules = sorted(rules_dir.rglob('*.md')) if rules_dir.is_dir() else []
        if len(rules) > MAX_RULES:
            self.report(rules_dir, 'unsupported', 'more than 100 rule files; narrow project scope')
            return
        rule_lines = []
        for rule in rules:
            if rule.is_symlink() and not rule.resolve().is_relative_to(self.root):
                self.report(rule, 'unsupported', 'external rule symlink requires explicit review')
                return
            try:
                meta, _ = frontmatter(read_text(rule))
                if set(meta) - {'paths'}:
                    raise ValueError('unsupported rule frontmatter')
                paths = meta.get('paths')
                if paths is not None and (not isinstance(paths, list) or not paths or not all(isinstance(x, str) and x for x in paths)):
                    raise ValueError('rule paths must be a nonempty string list')
                label = str(rule.relative_to(self.root))
                if paths:
                    rule_lines.append(f'- `{label}` — read only when task files match: {json.dumps(paths, ensure_ascii=False)}.')
                else:
                    rule_lines.append(f'- `{label}` — project-wide rule; read once for this task.')
            except (ValueError, OSError, UnicodeError) as exc:
                self.report(rule, 'unsupported', str(exc))
                return
        for path in docs:
            if path.is_symlink():
                self.report(path, 'conflict', 'existing instruction symlink preserved')
                continue
            text = read_text(path) if path.is_file() else ''
            if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
                self.report(path, 'conflict', 'malformed managed reference markers')
                continue
            clean = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), '', text, flags=re.S).rstrip()
            other = docs[1] if path == docs[0] else docs[0]
            # Existing native imports remain unchanged. Added pointers are plain prose
            # so they cannot create a Claude @import cycle.
            lines = [BEGIN, '## Shared agent instruction references',
                     'Read referenced instruction bodies once per task if not already supplied. '
                     'Do not recursively follow this managed block or re-read an entrypoint already visited.']
            if other.is_file():
                other_text = read_text(other)
                other_body = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), '', other_text, flags=re.S).strip()
                if other_body and other_body not in ('@' + path.name, path.name):
                    lines.append(f'- `{other.name}` — also applies; preserve its project-specific requirements.')
            lines.extend(rule_lines)
            lines.append(END)
            desired = (clean + '\n\n' if clean else '') + '\n'.join(lines) + '\n'
            self.write(path, desired, 'bounded cross-agent instruction references', managed=True)

    def agents(self):
        source_dir = self.root / '.claude/agents'
        sources = {p.stem: p for p in sorted(source_dir.glob('*.md'))}
        for item in self.config.get('agent_sources', []):
            if not isinstance(item, dict) or not safe_name(item.get('name', '')):
                raise ValueError('agent_sources requires safe names and explicit source paths')
            path = Path(item.get('path', '')).expanduser()
            if not path.is_absolute():
                raise ValueError('agent source must be an absolute Markdown path')
            if not path.is_file():
                self.report(path, 'unsupported', 'configured agent source is missing')
                sources.pop(item['name'], None)
                continue
            sources[item['name']] = path
            local_source = source_dir / (item['name'] + '.md')
            if local_source.resolve() != path.resolve():
                self.write(local_source, read_text(path), 'expose explicitly selected external agent to Claude')
                if self.entries[-1]['status'] == 'conflict':
                    # Do not generate a divergent Codex worker when its Claude
                    # counterpart could not be aligned to the selected source.
                    sources.pop(item['name'], None)
        for target in sorted((self.root / '.codex/agents').glob('*.toml')):
            if target.stem not in sources:
                self.report(target, 'unsupported', 'Codex-only worker needs an explicit portable source; reverse conversion is not inferred')
        registrations = []
        for role, source in sorted(sources.items()):
            try:
                meta, body = frontmatter(read_text(source))
                unsupported = set(meta) - {'name', 'description', 'model', 'level', 'disallowedTools'}
                if unsupported:
                    raise ValueError('unsupported agent fields: ' + ', '.join(sorted(unsupported)))
                name = meta.get('name', source.stem)
                if not isinstance(name, str) or not safe_name(name):
                    raise ValueError('unsafe agent name')
                if not isinstance(meta.get('description'), str) or not meta['description']:
                    raise ValueError('agent description required')
                denied = meta.get('disallowedTools', [])
                if isinstance(denied, str):
                    denied = [x.strip() for x in denied.split(',') if x.strip()]
                if not isinstance(denied, list) or any(x not in ('Write', 'Edit') for x in denied):
                    raise ValueError('tool restrictions cannot be safely translated')
                model = meta.get('model', 'inherit')
                if not isinstance(model, str):
                    raise ValueError('model must be a string')
                mapped = self.config.get('model_map', {}).get(model)
                if model != 'inherit' and not mapped:
                    raise ValueError('model requires explicit model_map entry')
                if mapped is not None and (not isinstance(mapped, str) or not mapped):
                    raise ValueError('model_map target must be a nonempty model name')
                description = meta['description']
                if 'level' in meta:
                    description += ' (source level: ' + str(meta['level']) + ')'
                rows = ['# Generated by ai-working sync_agent_assets.py; source remains authoritative.',
                        'name = ' + json.dumps(name), 'description = ' + json.dumps(description)]
                if mapped and mapped != 'inherit':
                    rows.append('model = ' + json.dumps(mapped))
                if denied:
                    rows.append('sandbox_mode = "read-only"')
                rows.append('developer_instructions = ' + json.dumps(body.strip(), ensure_ascii=False))
                target = self.root / '.codex/agents' / (role + '.toml')
                self.write(target, '\n'.join(rows) + '\n', 'translate supported Claude agent; preserve write restrictions' + ('; model mapped to inherited platform default' if mapped == 'inherit' else ''))
                if self.entries[-1]['status'] in ('ok', 'change'):
                    registrations.append((role, meta['description']))
            except (ValueError, OSError, UnicodeError) as exc:
                self.report(source, 'unsupported', str(exc))
        self.register_agents(registrations)

    def register_agents(self, registrations):
        path = self.root / '.codex/config.toml'
        if path.is_symlink():
            self.report(path, 'conflict', 'existing config symlink preserved')
            return
        original = read_text(path) if path.is_file() else ''
        if not registrations and CONFIG_BEGIN not in original:
            return
        if original.count(CONFIG_BEGIN) != original.count(CONFIG_END) or original.count(CONFIG_BEGIN) > 1:
            self.report(path, 'conflict', 'malformed managed config markers')
            return
        block_match = re.search(re.escape(CONFIG_BEGIN) + r'.*?' + re.escape(CONFIG_END), original, flags=re.S)
        block = block_match.group(0) if block_match else ''
        old_roles = set(re.findall(r'^\[agents\.\"([A-Za-z0-9_.-]+)\"\]$', block, re.M))
        new_roles = {role for role, _ in registrations}
        stale_roles = old_roles - new_roles
        if block and (stale_roles or not registrations):
            owned_config = self.state['generated'].get(str(path.relative_to(self.root))) == digest(original.encode())
            if not owned_config:
                self.report(path, 'conflict', 'active stale worker registrations may remain: modified or unmanaged config preserved')
                return
            for role in sorted(stale_roles):
                worker = self.root / '.codex/agents' / (role + '.toml')
                owned_hash = self.state['generated'].get(str(worker.relative_to(self.root)))
                unchanged = owned_hash and (not exists(worker) or (worker.is_file() and not worker.is_symlink() and worker.stat().st_size <= MAX_FILE and digest(worker.read_bytes()) == owned_hash))
                if not unchanged:
                    self.report(path, 'conflict', 'active stale worker registration preserved because its worker was modified: ' + role)
                    return
        clean = re.sub(re.escape(CONFIG_BEGIN) + r'.*?' + re.escape(CONFIG_END), '', original, flags=re.S).rstrip()
        # Fail closed on syntax this dependency-free updater cannot safely locate.
        if chr(34) * 3 in clean or chr(39) * 3 in clean:
            self.report(path, 'unsupported', 'multiline TOML strings require parser-assisted registration')
            return
        agents_key = r'(?:agents|\"agents\"|' + chr(39) + 'agents' + chr(39) + ')'
        if re.search(r'^\s*(?:\[\s*' + agents_key + r'(?:\s*\]|\s*\.)|' + agents_key + r'\s*[.=])', clean, re.M):
            self.report(path, 'conflict', 'existing native agents configuration requires parser-assisted merge')
            return
        lines = [CONFIG_BEGIN]
        for role, description in registrations:
            header = re.compile(r'^\s*\[\s*agents\.(?:' + re.escape(role) + r'|\"' + re.escape(role) + r'\"|' + chr(39) + re.escape(role) + chr(39) + r')(?:\s*\]|\.)', re.M)
            if header.search(clean) or re.search(r'^\s*agents\s*=|^\s*agents\.', clean, re.M):
                self.report(path, 'conflict', 'existing native agent registration preserved: ' + role)
                continue
            lines.extend(['[agents.' + json.dumps(role) + ']',
                          'description = ' + json.dumps(description),
                          'config_file = ' + json.dumps('agents/' + role + '.toml'), ''])
        lines.append(CONFIG_END)
        if len(lines) == 2:
            if block:
                self.write(path, clean + ('\n' if clean else ''), 'unregister unchanged generated workers with missing or unsupported sources; retain worker files', managed=True)
            return
        desired = (clean + '\n\n' if clean else '') + '\n'.join(lines) + '\n'
        self.write(path, desired, 'register generated workers in native Codex configuration', managed=True)

    def commit(self):
        if not self.apply or not self.actions:
            return
        # All inspection happens before the first mutation. Never delete originals.
        for kind, path, value, expected in self.actions:
            if not self.local_destination(path) or path.is_symlink():
                raise ValueError('destination changed during inspection')
            if expected is None and exists(path):
                raise ValueError('destination appeared during inspection')
            if expected is not None and (not path.is_file() or path.read_bytes() != expected):
                raise ValueError('destination changed during inspection')
        if not self.backup_root.parent.resolve().is_relative_to(self.state_boundary):
            raise ValueError('backup parent escapes selected scope')
        self.backup_root.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        for kind, path, value, expected in self.actions:
            path.parent.mkdir(parents=True, exist_ok=True)
            if exists(path):
                backup = self.backup_root / path.relative_to(self.root)
                backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                if path.is_symlink():
                    backup.symlink_to(os.readlink(path))
                else:
                    shutil.copy2(path, backup)
                    backup.chmod(0o600)
            if kind == 'link':
                # Missing-only links: refuse a destination created after inspection.
                path.symlink_to(os.path.relpath(value, path.parent))
            else:
                fd, temp = tempfile.mkstemp(prefix='.asset-sync-', dir=path.parent)
                try:
                    with os.fdopen(fd, 'wb') as stream:
                        stream.write(value)
                    os.chmod(temp, path.stat().st_mode & 0o777 if path.exists() else 0o644)
                    os.replace(temp, path)
                finally:
                    if os.path.exists(temp):
                        os.unlink(temp)
                self.state['generated'][str(path.relative_to(self.root))] = digest(value)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix='.asset-state-', dir=self.state_path.parent)
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(self.state, stream, indent=2)
                stream.write('\n')
            os.replace(temp, self.state_path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        for entry in self.entries:
            if entry['status'] == 'change':
                entry['status'] = 'applied'

    def run(self):
        self.skills()
        self.references()
        self.agents()
        self.commit()
        return {'schema_version': 1, 'mode': self.mode, 'applied': self.apply,
                'entries': self.entries,
                'counts': {s: sum(x['status'] == s for x in self.entries)
                           for s in ('ok', 'change', 'applied', 'conflict', 'unsupported')}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--home', type=Path, help='explicit agent home to synchronize')
    scope.add_argument('--project', type=Path, help='one explicit project root to synchronize')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--apply', action='store_true')
    action.add_argument('--check', action='store_true', help='read-only; fail if drift or unresolved assets exist')
    parser.add_argument('--config', type=Path, help='machine-local JSON skill_sources and model_map')
    parser.add_argument('--json', action='store_true', help='JSON is always emitted; accepted for consistency')
    args = parser.parse_args(argv)
    try:
        root = args.home or args.project
        if not root.is_dir():
            raise ValueError('selected root must already exist')
        config = json.loads(read_text(args.config)) if args.config else {}
        if not isinstance(config, dict) or set(config) - {'schema_version', 'skill_sources', 'agent_sources', 'model_map'}:
            raise ValueError('unsupported config structure')
        if config.get('schema_version', 1) != 1 or not isinstance(config.get('skill_sources', []), list) or not isinstance(config.get('agent_sources', []), list) or not isinstance(config.get('model_map', {}), dict):
            raise ValueError('unsupported config schema')
        result = Sync(root, 'home' if args.home else 'project', args.apply, config).run()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(bool(result['counts']['conflict'] or result['counts']['unsupported'] or
                        (args.check and result['counts']['change'])))
    except (ValueError, TypeError, OSError, UnicodeError) as exc:
        # Do not print exception paths or config contents which may contain private data.
        print(json.dumps({'error': type(exc).__name__, 'message': 'asset sync failed; check scope/config and filesystem permissions'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
