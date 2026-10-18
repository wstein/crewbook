"""Synthetic metadata-only acceptance cases for local Codex usage reporting."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import usage_report as ur


def meta(thread='thread-a', session='session-a', guardian=False):
    source = {'subagent': {'other': 'guardian'}} if guardian else 'cli'
    return {'type': 'session_meta', 'payload': {
        'id': thread, 'session_id': session, 'source': source,
        'thread_source': 'guardian_review' if guardian else 'cli'}}


def model(name='gpt-6.1-sol'):
    return {'type': 'turn_context', 'payload': {'model': name}}


def usage(response='response-a', thread='thread-a', session='session-a', **changes):
    values = dict(input_tokens=100, cached_input_tokens=60, cache_write_input_tokens=0,
                  output_tokens=20, reasoning_output_tokens=12, total_tokens=120)
    values.update(changes)
    return {'type': 'token_usage_record', 'timestamp': '2026-10-18T00:00:00Z',
            'payload': {'thread_id': thread, 'session_id': session,
                        'response_id': response, 'usage': values,
                        'thread_token_usage': dict(total_tokens=999999),
                        'turn_token_usage': dict(total_tokens=999999)}}


class CodexUsageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, records, tail=''):
        p = self.root / name
        p.write_text(''.join(json.dumps(r) + '\n' for r in records) + tail)
        return p

    def run_report(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ur.main([str(self.root), '--codex', '--json', *args])
        self.assertEqual(code, 0, err.getvalue())
        return json.loads(out.getvalue())

    def test_response_dedup_across_resumed_files_ignores_model_totals(self):
        records = [meta(), model(), usage(), {'type': 'event_msg', 'payload': {
            'type': 'token_count', 'info': {'total_token_usage': {'total_tokens': 999999},
                                         'last_token_usage': {'total_tokens': 999999}}}}]
        self.write('a.jsonl', records)
        self.write('resume.jsonl', records)
        rep = self.run_report()
        self.assertEqual(rep['summary']['requests'], 1)
        self.assertEqual(rep['summary']['tokens'], dict(input=40, cache_read=60, output=20))
        self.assertEqual(rep['summary']['reasoning_output_tokens'], 12)
        self.assertEqual(rep['skipped_unknown']['duplicates'], 1)

    def test_session_collision_and_mixed_models_remain_separate(self):
        self.write('a.jsonl', [meta(), model(), usage(), model('gpt-6-luna'), usage('response-b')])
        self.write('b.jsonl', [meta('thread-b', 'session-b'), model(),
                              usage('response-c', thread='thread-b', session='session-b')])
        rep = self.run_report()
        self.assertEqual(rep['summary']['requests'], 3)
        self.assertEqual({r['model'] for r in rep['rows']}, {'gpt-6.1-sol', 'gpt-6-luna'})
        self.assertEqual(len({r['agent'] for r in rep['rows']}), 2)

    def test_global_response_collision_across_sessions_is_not_summed(self):
        self.write('a.jsonl', [meta(), model(), usage()])
        self.write('b.jsonl', [meta('thread-b', 'session-b'), model(),
                              usage(thread='thread-b', session='session-b')])
        rep = self.run_report()
        self.assertIsNone(rep['summary']['tokens'])
        self.assertEqual(rep['skipped_unknown']['conflicting_responses'], 1)

    def test_inherited_thread_usage_is_not_counted(self):
        self.write('a.jsonl', [meta('child'), model(), usage(), usage('child-response', thread='child')])
        rep = self.run_report()
        self.assertEqual(rep['summary']['requests'], 1)
        self.assertEqual(rep['skipped_unknown']['inherited_records'], 1)

    def test_guardian_visible_without_charge_or_quota_weight(self):
        self.write('a.jsonl', [meta(guardian=True), model('codex-auto-review'), usage()])
        rep = self.run_report()
        self.assertEqual(rep['rows'][0]['role'], 'guardian')
        self.assertEqual(rep['guardian']['requests'], 1)
        self.assertEqual(rep['guardian']['total_tokens'], 120)
        self.assertIsNone(rep['summary']['cost_estimate'])
        self.assertIn('quota', rep['notice'])

    def test_invalid_cache_reasoning_and_total_are_skipped_conservatively(self):
        self.write('a.jsonl', [meta(), model(), usage('bad-cache', cached_input_tokens=101),
                              usage('bad-reasoning', reasoning_output_tokens=21),
                              usage('bad-total', total_tokens=132),
                              usage('bool', input_tokens=True), usage('negative', output_tokens=-1)])
        rep = self.run_report()
        self.assertIsNone(rep['summary']['tokens'])
        self.assertEqual(rep['skipped_unknown']['bad_usage'], 5)
        self.assertEqual(rep['coverage'], 'unavailable')

    def test_display_hash_collision_preserves_internal_row_components(self):
        self.write('a.jsonl', [meta(), model(), usage('a', reasoning_output_tokens=2,
                                                    cache_write_input_tokens=3)])
        self.write('b.jsonl', [meta('thread-b'), model(),
                              usage('b', thread='thread-b', reasoning_output_tokens=7,
                                    cache_write_input_tokens=11)])
        # Display hashes are lossy labels, never aggregation/join identities.
        with mock.patch.object(ur, 'hash_id', return_value='12345678'):
            rep = self.run_report()
        self.assertEqual([r['agent'] for r in rep['rows']], ['12345678', '12345678'])
        self.assertEqual(sorted(r['reasoning_output_tokens'] for r in rep['rows']), [2, 7])
        self.assertEqual(sorted(r['cache_write_input_tokens_informational'] for r in rep['rows']), [3, 11])

    def test_text_and_html_distinguish_uncached_and_cached_input(self):
        self.write('a.jsonl', [meta(), model(), usage()])
        for flags in ([], ['--html', str(self.root / 'input.html')]):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ur.main([str(self.root), '--codex', *flags]), 0)
            rendered = (self.root / 'input.html').read_text() if flags else out.getvalue()
            self.assertIn('uncached input 40, cached input 60, output 20', rendered)
            self.assertNotIn('cached subset 60', rendered)

    def test_cache_write_is_informational_without_dropping_known_usage(self):
        self.write('a.jsonl', [meta(), model(), usage(cache_write_input_tokens=25)])
        rep = self.run_report()
        self.assertEqual(rep['rows'][0]['total_tokens'], 120)
        self.assertEqual(rep['summary']['tokens'], dict(input=40, cache_read=60, output=20))
        self.assertEqual(rep['summary']['cache_write_input_tokens_informational'], 25)
        self.assertNotIn('cache_write', rep['rows'][0])

    def test_missing_identity_or_partial_usage_never_becomes_zero_usage(self):
        partial = usage('partial'); del partial['payload']['usage']['cached_input_tokens']
        missing = usage(); del missing['payload']['response_id']
        self.write('a.jsonl', [meta(), model(), missing, partial])
        rep = self.run_report()
        self.assertEqual(rep['skipped_unknown']['no_dedupe_key'], 1)
        self.assertEqual(rep['skipped_unknown']['bad_usage'], 1)
        self.assertIsNone(rep['summary']['tokens'])

    def test_malformed_truncated_records_leave_observed_subtotal_partial(self):
        self.write('a.jsonl', [meta(), model(), usage(), [], {'type': 'token_usage_record', 'payload': None}],
                   tail='{"type":"token_usage_record"')
        rep = self.run_report()
        self.assertEqual(rep['coverage'], 'partial')
        self.assertEqual(rep['summary']['requests'], 1)
        self.assertEqual(rep['skipped_unknown']['malformed_lines'], 2)
        self.assertEqual(rep['skipped_unknown']['bad_usage'], 1)

    def test_conflicting_duplicate_is_excluded_instead_of_fieldwise_max(self):
        self.write('a.jsonl', [meta(), model(), usage(), usage(input_tokens=110, total_tokens=130)])
        rep = self.run_report()
        self.assertIsNone(rep['summary']['tokens'])
        self.assertEqual(rep['skipped_unknown']['conflicting_responses'], 1)

    def test_missing_model_stays_unknown_and_identifiers_are_hashed(self):
        self.write('a.jsonl', [meta(), usage()])
        rep = self.run_report()
        self.assertEqual(rep['rows'][0]['model'], 'unknown')
        self.assertRegex(rep['rows'][0]['agent'], r'^[0-9a-f]{8}$')
        self.assertEqual(rep['skipped_unknown']['unknown_model'], 1)

    def test_privacy_all_renderings_and_errors(self):
        marker = 'PRIVATE_PROMPT_ACCOUNT_SECRET'
        records = [meta(marker, marker), model(marker), usage(thread=marker, session=marker)]
        records.append({'type': 'response_item', 'payload': {'type': 'message', 'content': marker}})
        self.write(marker + '.jsonl', records)
        for flags in (['--json'], [], ['--html', str(self.root / 'report.html')]):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(ur.main([str(self.root), '--codex', *flags]), 0)
            rendered = out.getvalue() + err.getvalue()
            if '--html' in flags:
                rendered += (self.root / 'report.html').read_text()
            self.assertNotIn(marker, rendered)
            self.assertNotIn(str(self.root), rendered)

    def test_cumulative_only_schema_is_explicitly_unavailable(self):
        self.write('a.jsonl', [meta(), model(), {'type': 'event_msg', 'payload': {
            'type': 'token_count', 'info': {'last_token_usage': {'total_tokens': 40}}}}])
        rep = self.run_report()
        self.assertEqual(rep['coverage'], 'unavailable')
        self.assertIsNone(rep['summary']['tokens'])
        self.assertEqual(rep['skipped_unknown']['cumulative_records_ignored'], 1)


if __name__ == '__main__':
    unittest.main()
