#!/usr/bin/env python3
"""Apply a reviewed machine-local lean runtime profile; never edit plugin caches."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time


def plan(home, repo):
    changes = []
    profile_path = home / '.config/ai-working/runtime-profile.json'
    profile = json.loads(profile_path.read_text()) if profile_path.exists() else {}
    settings_path = home / '.claude/settings.json'
    settings_snapshot = settings_path.read_bytes() if settings_path.exists() else None
    settings = json.loads(settings_snapshot) if settings_snapshot is not None else {}
    original = json.dumps(settings, sort_keys=True)
    if profile.get('lean_omc', True):
        env = settings.setdefault('env', {})
        skip = [s.strip() for s in env.get('OMC_SKIP_HOOKS', '').split(',') if s.strip()]
        for name in ['keyword-detector', 'skill-injector', 'pre-tool-use', 'post-tool-use']:
            if name not in skip:
                skip.append(name)
        env['OMC_SKIP_HOOKS'] = ','.join(skip)
    # Only explicitly selected local integrations; no vendor/account IDs in SSOT.
    for name in profile.get('disabled_claude_plugins', []):
        if name in settings.get('enabledPlugins', {}):
            settings['enabledPlugins'][name] = False
    if json.dumps(settings, sort_keys=True) != original:
        changes.append((settings_path, json.dumps(settings, ensure_ascii=False, indent=2) + '\n', settings_snapshot))
    wrapper = home / '.claude/CLAUDE.md'
    canonical = (repo / 'global/CLAUDE.md').read_text()
    if wrapper.is_file() and not wrapper.is_symlink():
        old_bytes = wrapper.read_bytes()
        old = old_bytes.decode('utf-8')
        new = old
        if profile.get('lean_omc', True):
            new = re.sub(r'(?ms)^<!-- OMC:START -->\n.*?^<!-- OMC:END -->\n*', '', new)
        match = re.search(r'(?ms)^## Interaction Principles \(Global Override\)\n(.*?)(?=^---\s*$|^## |^<!-- BEGIN AI-WORKING|\Z)', new)
        if match and match.group(1).strip() in canonical:
            new = new[:match.start()] + new[match.end():]
        if new != old:
            changes.append((wrapper, new, old_bytes))
    return changes


def apply_changes(home, changes):
    backup = home / '.local/state/ai-working/runtime-backups' / str(time.time_ns())
    for target, content, expected in changes:
        if target.is_symlink():
            raise RuntimeError('Refusing to replace a linked runtime configuration')
        current = target.read_bytes() if target.exists() else None
        if current != expected:
            raise RuntimeError('Runtime configuration changed after planning; inspect and retry')
    for target, content, expected in changes:
        if (target.read_bytes() if target.exists() else None) != expected:
            raise RuntimeError('Runtime configuration changed during apply; inspect and retry')
        if target.exists():
            saved = backup / target.relative_to(home)
            saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.ai-working-', dir=target.parent)
        try:
            with os.fdopen(fd, 'w') as out:
                out.write(content)
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    changes = plan(args.home, args.repo)
    result = {'changes': [str(p.relative_to(args.home)) for p, _, _ in changes], 'applied': args.apply}
    if args.apply and changes:
        apply_changes(args.home, changes)
    print(json.dumps(result))
    return int(args.check and bool(changes))


if __name__ == '__main__':
    raise SystemExit(main())
