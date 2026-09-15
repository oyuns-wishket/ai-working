#!/usr/bin/env python3
"""Opt-in, local-only retrieval traces and explicit outcomes; never retain source text."""
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import uuid

ID = re.compile(r'[a-f0-9]{32}\Z')
DOC = re.compile(r'KB-[A-Z0-9][A-Z0-9_-]{0,76}\Z')
KINDS = ('development', 'evaluation', 'maintenance')
OUTCOMES = ('used', 'not_used', 'missing', 'incorrect', 'outdated', 'unknown')
MAX_BYTES = 65536
MAX_RECORDS = 10000


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def state_path():
    value = os.environ.get('AI_WORKING_WIKI_FEEDBACK_STATE')
    return Path(value).expanduser().absolute() if value else Path.home()/'.local/state/ai-working/wiki-feedback'


def directory(create=False):
    path = state_path()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('feedback state must not traverse symlinks')
    if any((p/'.git').exists() for p in (path, *path.parents)):
        raise ValueError('feedback state must be outside Git repositories')
    if not path.exists():
        if not create:
            return None
        path.mkdir(mode=0o700, parents=True)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('feedback state requires a private owner directory')
    return path


def read_record(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > MAX_BYTES:
            raise ValueError('unsafe feedback record')
        raw = stream.read(MAX_BYTES+1)
    if len(raw) > MAX_BYTES:
        raise ValueError('oversized feedback record')
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get('schema_version') != 1 or value.get('trace_id') != path.stem:
        raise ValueError('invalid feedback record')
    validate_record(value)
    return value


def validate_record(value):
    def number(x):
        return type(x) in (int, float) and 0 <= x <= 86400000 and math.isfinite(x)
    def hashed(x):
        return isinstance(x, str) and re.fullmatch(r'[a-f0-9]{64}', x) is not None
    def timestamp(x):
        if not isinstance(x, str) or len(x) > 40:
            return False
        try:
            return datetime.fromisoformat(x.replace('Z', '+00:00')).tzinfo is not None
        except ValueError:
            return False
    fields = {'schema_version', 'trace_id', 'recorded_at', 'sample_kind', 'project_key', 'query_hash',
              'route_mode', 'routing_ms', 'selected_bytes', 'documents', 'rejected_count', 'feedback'}
    if (set(value) != fields or value.get('schema_version') != 1
            or not isinstance(value.get('trace_id'), str) or not ID.fullmatch(value['trace_id'])
            or not timestamp(value.get('recorded_at'))):
        raise ValueError('invalid trace schema')
    docs = value.get('documents')
    if (value.get('sample_kind') not in KINDS or value.get('route_mode') not in ('wiki-bounded', 'repo-only')
            or not hashed(value.get('project_key')) or not hashed(value.get('query_hash'))
            or not number(value.get('routing_ms')) or type(value.get('selected_bytes')) is not int
            or not 0 <= value['selected_bytes'] <= 16*1024*1024
            or type(value.get('rejected_count')) is not int or value['rejected_count'] < 0
            or not isinstance(docs, list) or len(docs) > 20):
        raise ValueError('invalid trace fields')
    for doc in docs:
        if (not isinstance(doc, dict) or set(doc) != {'id', 'bytes', 'read_mode', 'body_sha256', 'sections'} or not isinstance(doc.get('id'), str) or not DOC.fullmatch(doc['id'])
                or type(doc.get('bytes')) is not int or doc['bytes'] < 0
                or doc.get('read_mode') not in ('document', 'sections')
                or (doc.get('body_sha256') is not None and not hashed(doc['body_sha256']))
                or not isinstance(doc.get('sections'), list) or len(doc['sections']) > 3
                or any(not isinstance(r, dict) or set(r) != {'line_start', 'line_end'} or type(r.get('line_start')) is not int or type(r.get('line_end')) is not int
                       or not 1 <= r['line_start'] <= r['line_end'] for r in doc['sections'])):
            raise ValueError('invalid traced document')
    selected = {doc['id'] for doc in docs}
    if len(selected) != len(docs):
        raise ValueError('duplicate traced documents')
    result = value.get('feedback')
    if result is not None:
        if (not isinstance(result, dict) or set(result) != {'outcome', 'document_ids', 'actor', 'recorded_at', 'evidence_kind', 'evidence_ref_hash'}
                or not timestamp(result.get('recorded_at')) or result.get('outcome') not in OUTCOMES
                or result.get('actor') not in ('agent', 'human')
                or not isinstance(result.get('document_ids'), list)
                or any(not isinstance(x, str) or x not in selected for x in result['document_ids'])
                or len(set(result['document_ids'])) != len(result['document_ids'])
                or result.get('evidence_kind') not in (None, 'code', 'test', 'deployment', 'decision')
                or (result.get('evidence_ref_hash') is not None and not hashed(result['evidence_ref_hash']))):
            raise ValueError('invalid outcome fields')
        if result['outcome'] in ('used', 'incorrect', 'outdated') and not result['document_ids']:
            raise ValueError('missing affected documents')
        if result['outcome'] in ('used', 'missing', 'incorrect', 'outdated') and not result.get('evidence_ref_hash'):
            raise ValueError('missing outcome evidence')


def write_record(path, value):
    validate_record(value)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode()+b'\n'
    if len(encoded) > MAX_BYTES:
        raise ValueError('feedback record exceeds bound')
    fd, name = tempfile.mkstemp(prefix='.feedback-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked(root):
    fd = os.open(root/'.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('unsafe feedback lock')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def record_route(route, query, elapsed_ms, kind='development'):
    if kind not in KINDS:
        raise ValueError('unknown sample kind')
    root = directory(create=True)
    identity = uuid.uuid4().hex
    project = route.get('project') or {}
    project_identity = project.get('canonical_remote') or project.get('id') or route.get('git_root') or route.get('project_path') or 'unresolved'
    selected = []
    for doc in route.get('documents', [])[:20]:
        doc_id = doc.get('id')
        if doc.get('corpus', 'canonical') != 'canonical' or not isinstance(doc_id, str) or not DOC.fullmatch(doc_id):
            continue
        selected.append({'id': doc_id, 'bytes': int(doc.get('bytes', 0)),
                         'read_mode': doc.get('read_mode', 'document'), 'body_sha256': doc.get('body_sha256'),
                         'sections': [{'line_start': r['line_start'], 'line_end': r['line_end']} for r in doc.get('sections', [])[:3]]})
    rejected = route.get('rejected') or []
    value = {'schema_version': 1, 'trace_id': identity, 'recorded_at': now(), 'sample_kind': kind,
             'project_key': digest(str(project_identity)), 'query_hash': digest(query),
             'route_mode': route.get('mode', 'wiki-bounded' if selected else 'repo-only'),
             'routing_ms': round(max(0, elapsed_ms), 3), 'selected_bytes': int(route.get('selected_bytes', 0)),
             'documents': selected, 'rejected_count': len(rejected), 'feedback': None}
    with locked(root):
        write_record(root/(identity+'.json'), value)
    return {'trace_id': identity, 'sample_kind': kind, 'feedback_status': 'pending'}


def feedback(trace_id, outcome, document_ids, evidence_kind=None, evidence_ref=None, actor='agent'):
    if not ID.fullmatch(trace_id) or outcome not in OUTCOMES or actor not in ('agent', 'human'):
        raise ValueError('invalid feedback identity/outcome/actor')
    root = directory()
    if root is None:
        raise ValueError('trace not found')
    if evidence_kind not in (None, 'code', 'test', 'deployment', 'decision'):
        raise ValueError('invalid evidence kind')
    if outcome in ('used', 'missing', 'incorrect', 'outdated') and (not evidence_kind or not evidence_ref):
        raise ValueError('this outcome requires an actual verification reference')
    if bool(evidence_kind) != bool(evidence_ref) or (evidence_ref and (not evidence_ref.strip() or len(evidence_ref) > 2048 or any(ord(c) < 32 or ord(c) == 127 for c in evidence_ref))):
        raise ValueError('invalid evidence reference')
    if len(document_ids) > 20 or len(set(document_ids)) != len(document_ids):
        raise ValueError('invalid feedback document list')
    with locked(root):
        path = root/(trace_id+'.json')
        value = read_record(path)
        if value.get('feedback') is not None:
            raise ValueError('feedback is already final; preserve the observation')
        selected = {d['id'] for d in value['documents']}
        if any(doc not in selected for doc in document_ids):
            raise ValueError('feedback documents must belong to this trace')
        if outcome in ('used', 'incorrect', 'outdated') and not document_ids:
            raise ValueError('this outcome requires the affected selected documents')
        value['feedback'] = {'outcome': outcome, 'document_ids': document_ids, 'actor': actor,
                             'recorded_at': now(), 'evidence_kind': evidence_kind,
                             'evidence_ref_hash': digest(evidence_ref) if evidence_ref else None}
        write_record(path, value)
    return {'trace_id': trace_id, 'outcome': outcome, 'actor': actor}


def report(kind='development', limit=MAX_RECORDS):
    if kind not in KINDS or not 1 <= limit <= MAX_RECORDS:
        raise ValueError('invalid report bound')
    root = directory()
    rows, examined, rejected, truncated = [], 0, 0, False
    if root is not None:
        with os.scandir(root) as entries:
            for entry in entries:
                if not entry.name.endswith('.json'):
                    continue
                if examined >= limit:
                    truncated = True
                    break
                examined += 1
                try:
                    row = read_record(Path(entry.path))
                    if row['sample_kind'] == kind:
                        rows.append(row)
                except (OSError, ValueError, KeyError, TypeError):
                    rejected += 1
    outcomes = Counter((r.get('feedback') or {}).get('outcome', 'unreported') for r in rows)
    durations = sorted(r['routing_ms'] for r in rows)
    bad_docs = Counter(d for r in rows if (r.get('feedback') or {}).get('outcome') in ('incorrect', 'outdated')
                       for d in r['feedback']['document_ids'])
    n = len(rows)
    return {'sample_kind': kind, 'traces': n, 'outcomes': dict(outcomes),
            'feedback_coverage': round((n-outcomes['unreported'])/n, 4) if n else None,
            'no_canonical_context_routes': sum(not r['documents'] for r in rows),
            'routing_ms_p50': durations[(n-1)//2] if n else None,
            'routing_ms_p95': durations[min(n-1, int(n*.95))] if n else None,
            'selected_bytes_total': sum(r['selected_bytes'] for r in rows),
            'flagged_documents': dict(bad_docs.most_common(20)), 'flagged_document_count': len(bad_docs), 'examined_records': examined,
            'invalid_records': rejected, 'truncated': truncated,
            'interpretation': 'Reported observations, not causal productivity or cost measurements; unreported is unknown.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    f = sub.add_parser('feedback')
    f.add_argument('--trace-id', required=True)
    f.add_argument('--outcome', choices=OUTCOMES, required=True)
    f.add_argument('--document-id', action='append', default=[])
    f.add_argument('--evidence-kind', choices=('code', 'test', 'deployment', 'decision'))
    f.add_argument('--evidence-ref', help='Existing project verification reference; only its hash is retained')
    f.add_argument('--actor', choices=('agent', 'human'), default='agent')
    r = sub.add_parser('report')
    r.add_argument('--kind', choices=KINDS, default='development')
    r.add_argument('--limit', type=int, default=MAX_RECORDS)
    args = p.parse_args()
    try:
        value = feedback(args.trace_id, args.outcome, args.document_id, args.evidence_kind, args.evidence_ref, args.actor) if args.command == 'feedback' else report(args.kind, args.limit)
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({'error': 'Feedback operation rejected; check the trace, arguments and private state permissions.'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
