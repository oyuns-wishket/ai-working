import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/retrieval_feedback.py'
ROUTER = SCRIPT.with_name('wiki_context.py')
spec = importlib.util.spec_from_file_location('retrieval_feedback', SCRIPT)
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base/'private'
        self.env = patch.dict(os.environ, {'AI_WORKING_WIKI_FEEDBACK_STATE': str(self.root)})
        self.env.start()
        self.route = {'project': {'canonical_remote': 'https://example.invalid/private-project'},
                      'selected_bytes': 200, 'documents': [{'id': 'KB-TEST', 'title': 'CONFIDENTIAL',
                      'path': '/private/secret', 'bytes': 200, 'body': 'SECRET', 'corpus': 'canonical'}]}

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def record(self, kind='development'):
        return f.record_route(self.route, 'PRIVATE USER QUERY', 12.5, kind)['trace_id']

    def test_no_source_or_query_or_locator_persisted(self):
        identity = self.record()
        raw = (self.root/(identity+'.json')).read_text()
        for forbidden in ['CONFIDENTIAL', 'SECRET', 'PRIVATE USER QUERY', '/private/secret', 'https://example.invalid']:
            self.assertNotIn(forbidden, raw)
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.root/(identity+'.json')).stat().st_mode & 0o777, 0o600)
        f.feedback(identity, 'used', ['KB-TEST'], 'test', '/private/verification.log')
        self.assertNotIn('/private/verification.log', (self.root/(identity+'.json')).read_text())

    def test_feedback_requires_selected_document_and_evidence(self):
        identity = self.record()
        for args in [('used', ['KB-TEST'], None, None), ('used', ['KB-OTHER'], 'test', 'proof'),
                     ('incorrect', [], 'code', 'proof'), ('missing', [], None, None)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                f.feedback(identity, *args)
        f.feedback(identity, 'incorrect', ['KB-TEST'], 'code', 'checked-reference')
        result = f.report()
        self.assertEqual(result['flagged_documents'], {'KB-TEST': 1})
        self.assertEqual(result['outcomes'], {'incorrect': 1})

    def test_missing_feedback_is_unknown_and_kinds_are_separate(self):
        self.record()
        evaluated = self.record('evaluation')
        self.record('maintenance')
        f.feedback(evaluated, 'used', ['KB-TEST'], 'test', 'fixture-result')
        report = f.report()
        self.assertEqual(report['traces'], 1)
        self.assertEqual(report['feedback_coverage'], 0)
        self.assertEqual(report['outcomes'], {'unreported': 1})
        self.assertEqual(f.report('evaluation')['outcomes'], {'used': 1})

    def test_final_feedback_cannot_be_overwritten_even_concurrently(self):
        identity = self.record()
        command = [sys.executable, str(SCRIPT), 'feedback', '--trace-id', identity, '--outcome', 'not_used']
        a = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        b = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        a.communicate(); b.communicate()
        self.assertEqual(sorted([a.returncode, b.returncode]), [0, 2])
        with self.assertRaises(ValueError):
            f.feedback(identity, 'unknown', [])

    def test_unsafe_state_symlink_world_readable_and_git_are_rejected(self):
        self.root.symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(ValueError): self.record()
        self.root.unlink(); self.root.mkdir(mode=0o755)
        with self.assertRaises(ValueError): self.record()
        self.root.chmod(0o700); (self.base/'.git').mkdir()
        with self.assertRaises(ValueError): self.record()

    def test_report_skips_fifo_symlink_oversize_and_malformed_records(self):
        self.record()
        outside = self.base/'outside'; outside.write_text('private')
        (self.root/('a'*32+'.json')).symlink_to(outside)
        os.mkfifo(self.root/('b'*32+'.json'),0o600)
        large = self.root/('c'*32+'.json'); large.write_bytes(b'x'*(f.MAX_BYTES+1));large.chmod(0o600)
        corrupt = self.root/('d'*32+'.json'); corrupt.write_text(json.dumps({'schema_version':1,'trace_id':'d'*32,'sample_kind':'development','documents':'bad'}));corrupt.chmod(0o600)
        result = f.report()
        self.assertEqual(result['traces'],1)
        self.assertEqual(result['invalid_records'],4)

    def test_lock_contention_fails_open_without_waiting(self):
        self.record()
        env={**os.environ,'AI_WORKING_CONTEXT_REGISTRY_PATH':str(self.base/'absent'),'HOME':str(self.base)}
        with f.locked(self.root):
            result=subprocess.run([sys.executable,str(ROUTER),'route','--project',str(self.base),'--query','test','--record'],capture_output=True,text=True,env=env,check=True,timeout=2)
        self.assertEqual(json.loads(result.stdout)['retrieval_feedback']['status'],'unavailable')

    def test_unknown_fields_and_huge_numeric_values_cannot_be_retained(self):
        identity=self.record();path=self.root/(identity+'.json'); original=json.loads(path.read_text())
        for mutate in [lambda x:x.update(unexpected_body='PRIVATE'), lambda x:x.update(routing_ms=10**400),
                       lambda x:x['documents'][0].update(body='PRIVATE'), lambda x:x.update(recorded_at='invalid')]:
            value=json.loads(json.dumps(original));mutate(value);path.write_text(json.dumps(value))
            with self.assertRaises(ValueError): f.feedback(identity,'not_used',[])
            self.assertEqual(f.report()['invalid_records'],1)
        path.write_text(json.dumps(original))
        f.feedback(identity,'used',['KB-TEST'],'test','evidence')
        value=json.loads(path.read_text());value['feedback']['unexpected_body']='PRIVATE';path.write_text(json.dumps(value))
        self.assertEqual(f.report()['invalid_records'],1)

    def test_manual_only_trace_preserves_route_mode_without_private_document_ids(self):
        route={'mode':'wiki-bounded','selected_bytes':100,'documents':[{'id':'KB-MANUAL','corpus':'manual','bytes':100}]}
        identity=f.record_route(route,'private query',1)['trace_id']
        record=f.read_record(self.root/(identity+'.json'))
        self.assertEqual(record['route_mode'],'wiki-bounded')
        self.assertEqual(record['documents'],[])
        self.assertEqual(f.report()['no_canonical_context_routes'],1)

    def test_report_is_bounded_and_does_not_create_state(self):
        self.assertEqual(f.report()['traces'],0)
        self.assertFalse(self.root.exists())
        self.record();self.record()
        self.assertTrue(f.report(limit=1)['truncated'])

    def test_route_without_record_does_not_write_and_failure_still_records(self):
        command = [sys.executable,str(ROUTER),'--wiki-root',str(self.base/'absent'),'route','--project',str(self.base),'--query','PRIVATE QUERY']
        env={**os.environ,'AI_WORKING_CONTEXT_REGISTRY_PATH':str(self.base/'absent'),'HOME':str(self.base)}
        a=subprocess.run(command,capture_output=True,text=True,env=env,check=True)
        self.assertNotIn('retrieval_feedback',json.loads(a.stdout))
        self.assertFalse(self.root.exists())
        b=subprocess.run(command+['--record','--sample-kind','evaluation'],capture_output=True,text=True,env=env,check=True)
        self.assertIn('trace_id',json.loads(b.stdout)['retrieval_feedback'])
        self.assertEqual(f.report('evaluation')['no_canonical_context_routes'],1)

    def test_recording_failure_never_breaks_routing(self):
        self.root.mkdir(mode=0o755)
        env={**os.environ,'AI_WORKING_CONTEXT_REGISTRY_PATH':str(self.base/'absent'),'HOME':str(self.base)}
        result=subprocess.run([sys.executable,str(ROUTER),'route','--project',str(self.base),'--query','test','--record'],capture_output=True,text=True,env=env,check=True)
        value=json.loads(result.stdout)
        self.assertEqual(value['mode'],'repo-only')
        self.assertEqual(value['retrieval_feedback']['status'],'unavailable')
        self.assertEqual(list(self.root.iterdir()),[])


    def test_since_days_window_filters_by_trace_time(self):
        recent = self.record()
        old = self.record()
        path = self.root/(old+'.json')
        value = f.read_record(path)
        value['recorded_at'] = '2020-01-01T00:00:00Z'
        f.write_record(path, value)
        self.assertEqual(f.report()['traces'], 2)
        windowed = f.report(since_days=14)
        self.assertEqual((windowed['traces'], windowed['since_days'], windowed['outcomes']), (1, 14, {'unreported': 1}))
        f.feedback(recent, 'not_used', [])
        self.assertEqual(f.report(since_days=14)['outcomes'], {'not_used': 1})
        for bad in (0, -1, f.MAX_SINCE_DAYS+1, True, 1.5):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                f.report(since_days=bad)
        result = subprocess.run([sys.executable, str(SCRIPT), 'report', '--kind', 'development', '--since-days', '14'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['traces'], 1)


if __name__ == '__main__': unittest.main()
