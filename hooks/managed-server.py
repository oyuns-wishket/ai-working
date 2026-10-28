#!/usr/bin/env python3
"""Start session-owned temporary servers; never adopt arbitrary existing PIDs."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(os.environ.get('AGENT_RESOURCE_GUARD_CACHE_DIR', Path.home() / '.cache/ai-working-resource-guard'))


def write(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value) + '\n')
    tmp.chmod(0o600)
    tmp.replace(path)


def identity(pid):
    try:
        fields = subprocess.check_output(['ps', '-p', str(pid), '-o', 'uid=,pgid=,lstart='], text=True, timeout=2).strip().split(None, 2)
        if len(fields) != 3:
            raise ValueError('Uncertain process identity')
        return {'pid': pid, 'uid': int(fields[0]), 'pgid': int(fields[1]), 'started': fields[2]}
    except (subprocess.SubprocessError, ValueError):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return None
        raise RuntimeError('Process identity probe failed')


def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def same(record):
    return record.get('uid') == os.getuid() and record.get('pid') == record.get('pgid') and identity(record['pid']) == {k: record[k] for k in ('pid', 'uid', 'pgid', 'started')}


def finish_group():
    # Supervisor remains the group leader through TERM grace time, preventing
    # PID/group reuse before escalation. Its descendants share this new group.
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    os.killpg(os.getpid(), signal.SIGTERM)
    time.sleep(1)
    os.killpg(os.getpid(), signal.SIGKILL)


def supervise(record_path, command):
    signal.signal(signal.SIGTERM, lambda *_: finish_group())
    record = identity(os.getpid())
    if not record or record['pgid'] != os.getpid():
        raise RuntimeError('Expected isolated process group')
    write(record_path, record)
    try:
        child = subprocess.Popen(command)
        child.wait()
    finally:
        # A server may fork then exit. Clean its group even on natural exit.
        finish_group()


def cleanup(session):
    directory = ROOT / 'processes' / session
    results = []
    for marker in directory.glob('*.json'):
        status = 'failed'
        try:
            record = json.loads(marker.read_text())
            pid = record['pid']
            if not isinstance(pid, int) or pid <= 1:
                raise ValueError('Invalid PID')
            current = identity(pid)
            if current is None:
                status = 'orphaned' if group_exists(pid) else 'already-exited'
            elif not same(record):
                status = 'identity-mismatch'
            else:
                os.killpg(pid, signal.SIGTERM)
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline and same(record):
                    time.sleep(.05)
                status = 'stopped' if identity(pid) is None and not group_exists(pid) else 'failed'
            if status in ('stopped', 'already-exited'):
                marker.unlink(missing_ok=True)
                marker.with_suffix('.log').unlink(missing_ok=True)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError):
            status = 'failed'
        results.append({'resource': marker.stem, 'status': status})
    if results:
        write(ROOT / 'process-results' / f'{session}.json', {'at': time.time(), 'results': results})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'cleanup', '_supervise'])
    parser.add_argument('--session', required=True)
    parser.add_argument('--resource')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    # Options precede action because REMAINDER owns everything after action.
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,199}', args.session):
        parser.error('Invalid session ID')
    directory = ROOT / 'processes' / args.session
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if args.action == '_supervise':
        if not re.fullmatch(r'[a-f0-9]{32}', args.resource or ''):
            parser.error('Invalid resource ID')
        supervise(directory / f'{args.resource}.json', args.command)
        return
    lockpath = ROOT / 'process-locks' / f'{args.session}.lock'
    lockpath.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with lockpath.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.action == 'cleanup':
            print(json.dumps(cleanup(args.session)))
            return
        command = args.command
        if command[:1] == ['--']:
            command = command[1:]
        if not command:
            parser.error('Server command is required')
        resource = uuid.uuid4().hex
        log = directory / f'{resource}.log'
        with log.open('ab') as output:
            log.chmod(0o600)
            child = subprocess.Popen([sys.executable, __file__, '--session', args.session, '--resource', resource, '_supervise', *command], stdin=subprocess.DEVNULL, stdout=output, stderr=output, start_new_session=True)
        marker = directory / f'{resource}.json'
        deadline = time.monotonic() + 5
        while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        if not marker.exists():
            if child.poll() is None:
                child.terminate()
            raise RuntimeError('Server supervisor failed to register')
        print(json.dumps({'resource': resource, 'pid': child.pid, 'log': str(log)}))


if __name__ == '__main__':
    main()
