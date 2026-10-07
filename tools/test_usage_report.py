import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_report as ur  # noqa: E402

SECRET = 'sk-ant-PLANTED-SECRET-0123456789'
PATHSEC = '/Users/planted/private-code/src/main.rs'
PROMPT = 'PLANTED_PROMPT_TEXT'
RESP = 'PLANTED_RESPONSE_TEXT'
PLANTED = (SECRET, PATHSEC, PROMPT, RESP, 'planted', '/Users')


def asst(mid, rid, model='claude-sonnet-5', ts='2026-01-01T00:00:00.000Z', usage=None, agent=None):
    u = {'input_tokens': 10, 'output_tokens': 20, 'cache_read_input_tokens': 1000,
         'cache_creation_input_tokens': 100} if usage is None else usage
    o = {'type': 'assistant', 'requestId': rid, 'timestamp': ts, 'cwd': PATHSEC,
         'message': {'id': mid, 'model': model, 'usage': u,
                     'content': [{'type': 'text', 'text': RESP + SECRET}]}}
    if agent:
        o['agentId'] = agent
    return o


def user(text):
    return {'type': 'user', 'message': {'role': 'user', 'content': text + ' ' + SECRET + ' ' + PATHSEC}}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name) / 'planted'
        (self.dir / 's' / 'subagents').mkdir(parents=True)
        self.prices = Path(self.tmp.name) / 'prices.json'
        self.prices.write_text(json.dumps({'label': 'test estimate', 'models': {
            'sonnet': {'input': 1, 'output': 2, 'cache_read': 3, 'cache_write': 4}}}))

    def write(self, rel, lines, raw=None):
        p = self.dir / rel
        p.write_text('\n'.join(json.dumps(x) for x in lines) + ('\n' + raw if raw else '') + '\n')

    def run_rc(self, *args, path=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = ur.main([str(path or self.dir)] + list(args))
        return rc, out.getvalue(), err.getvalue()

    def run_cli(self, *args):
        rc, out, _err = self.run_rc(*args)
        self.assertEqual(rc, 0)
        return out

    def report(self, *args):
        return json.loads(self.run_cli('--json', *args))


class UsageTests(Fixture):
    def test_dedupe_by_message_and_request_id(self):
        self.write('s/main.jsonl', [asst('m1', 'r1'), asst('m1', 'r1'), asst('m1', 'r2'),
                                    asst('m2', 'r1')])
        rep = self.report()
        self.assertEqual(rep['summary']['requests'], 3)
        self.assertEqual(rep['skipped_unknown']['duplicates'], 1)

    def test_duplicate_keeps_max_streamed_output(self):
        a = asst('m1', 'r1', usage={'input_tokens': 5, 'output_tokens': 1})
        b = asst('m1', 'r1', usage={'input_tokens': 1, 'output_tokens': 50})
        self.write('s/main.jsonl', [a, b])
        t = self.report()['summary']['tokens']
        self.assertEqual((t['input'], t['output']), (5, 50))

    def test_dedupe_across_files(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        self.write('s/subagents/agent-abc.jsonl', [asst('m1', 'r1')])
        self.assertEqual(self.report()['summary']['requests'], 1)

    def test_roles_models_and_grouping(self):
        self.write('s/main.jsonl', [user('You are the desk'), asst('m0', 'r0')])
        self.write('s/subagents/agent-a1.jsonl', [user('Please review this'), asst('m1', 'r1', 'claude-opus-5')])
        self.write('s/subagents/agent-a1.meta.json', [])
        self.write('s/subagents/agent-a2.jsonl', [user('hello'), asst('m2', 'r2')])
        (self.dir / 's/subagents/agent-a3.jsonl').write_text(json.dumps(asst('m3', 'r3')) + '\n')
        (self.dir / 's/subagents/agent-a3.meta.json').write_text(
            json.dumps({'agentType': 'crewbook-dispatch', 'description': 'x'}))
        roles = {(r['role'], r['model']) for r in self.report()['rows']}
        self.assertEqual(roles, {('unknown', 'claude-opus-5'),
                                 ('unknown', 'claude-sonnet-5'), ('dispatch', 'claude-sonnet-5')})

    def test_prompt_content_never_assigns_role(self):
        for content in ('reviewer desk author dispatch design',
                        [{'type': 'text', 'text': 'reviewer'}]):
            self.write('s/main.jsonl', [{'type': 'user', 'message': {'content': content}},
                                       asst('m1', 'r1')])
            self.assertEqual(self.report()['rows'][0]['role'], 'unknown')

    def test_metadata_role_wins_and_follows_agent_id(self):
        self.write('s/subagents/agent-a.jsonl', [user('reviewer'), asst('m1', 'r1', agent='other')])
        (self.dir / 's/subagents/agent-a.meta.json').write_text(json.dumps({'agentType': 'crewbook-dispatch'}))
        self.assertEqual(self.report()['rows'][0]['role'], 'dispatch')

    def test_cost_from_price_table_and_na_without(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        rep = self.report('--prices', str(self.prices))
        self.assertAlmostEqual(rep['rows'][0]['cost_estimate'], (10 + 40 + 3000 + 400) / 1e6)
        self.assertEqual(rep['share_basis'], 'cost_estimate')
        self.assertEqual(rep['rows'][0]['share'], 1.0)
        rep = self.report()
        self.assertIsNone(rep['rows'][0]['cost_estimate'])
        self.assertEqual(rep['cost'], 'n/a')
        self.assertIn('n/a', self.run_cli())

    def test_top_n_context_and_resumes(self):
        lines = [asst('m%d' % i, 'r%d' % i, ts='2026-01-01T0%d:00:00Z' % i,
                      usage={'input_tokens': i, 'cache_read_input_tokens': 100 * i,
                             'cache_creation_input_tokens': 0, 'output_tokens': 1})
                 for i in range(1, 4)]
        self.write('s/main.jsonl', lines)
        self.write('s/subagents/agent-x.jsonl', [asst('z', 'z')])
        self.assertEqual(len(self.report('--top', '1')['rows']), 1)
        rep = self.report()
        self.assertEqual(rep['rows_total'], 2)
        row = [r for r in rep['rows'] if r['requests'] == 3][0]
        self.assertEqual(row['context_last_request'], 303)
        self.assertEqual(row['resumes_estimate'], 2)

    def test_loop_heuristic_regular_bursts(self):
        lines = [asst('m%d' % i, 'r%d' % i, ts='2026-01-01T00:%02d:00Z' % (i * 5)) for i in range(8)]
        self.write('s/main.jsonl', lines)
        loop = self.report()['rows'][0]['loop_estimate_unverified']
        self.assertEqual((loop['bursts'], loop['interval_s']), (8, 300))

    def test_model_switch_does_not_invent_resumes(self):
        self.write('s/main.jsonl', [asst('a', 'a', ts='2026-01-01T00:00:00Z'),
            asst('b', 'b', model='claude-opus-5', ts='2026-01-01T00:20:00Z'),
            asst('c', 'c', ts='2026-01-01T00:40:00Z')])
        self.assertEqual(sum(r['resumes_estimate'] for r in self.report()['rows']), 0)

    def test_resume_at_model_switch_is_attributed_once(self):
        self.write('s/main.jsonl', [asst('a', 'a', ts='2026-01-01T00:00:00Z'),
            asst('b', 'b', model='claude-opus-5', ts='2026-01-01T01:00:00Z')])
        rows = {r['model']: r for r in self.report()['rows']}
        self.assertEqual(rows['claude-sonnet-5']['resumes_estimate'], 0)
        self.assertEqual(rows['claude-opus-5']['resumes_estimate'], 1)

    def test_loop_uses_full_agent_timeline_once_across_models(self):
        self.write('s/main.jsonl', [asst(str(i), str(i),
            model='claude-opus-5' if i % 2 else 'claude-sonnet-5',
            ts='2026-01-01T00:%02d:00Z' % (i * 5)) for i in range(8)])
        loops = [r['loop_estimate_unverified'] for r in self.report()['rows']
                 if 'loop_estimate_unverified' in r]
        self.assertEqual(len(loops), 1)
        self.assertEqual((loops[0]['bursts'], loops[0]['interval_s']), (8, 300))

    def test_missing_fields_fail_closed(self):
        bad = [asst('m1', None), asst(None, 'r1'),
               {'type': 'assistant', 'message': 'nope'},
               {'type': 'assistant', 'requestId': 'r', 'message': {'id': 'q', 'usage': {
                   'input_tokens': 'x', 'output_tokens': -3, 'cache_read_input_tokens': True}}},
               asst('m5', 'r5', model='<bad model>', ts='garbage'), [1, 2], 'str']
        self.write('s/main.jsonl', bad, raw='{not json ' + SECRET)
        rep = self.report()
        k = rep['skipped_unknown']
        self.assertEqual(k['no_dedupe_key'], 2)
        self.assertGreaterEqual(k['bad_usage'], 4)
        self.assertEqual(k['malformed_lines'], 3)
        self.assertEqual(rep['summary']['requests'], 2)
        self.assertEqual({r['model'] for r in rep['rows']}, {'unknown'})
        self.assertIn('skipped/unknown', self.run_cli())

    def test_empty_file_ok_but_no_files_fails(self):
        self.write('s/main.jsonl', [])
        self.assertEqual(self.report()['summary']['requests'], 0)
        empty = Path(self.tmp.name) / 'empty'
        empty.mkdir()
        rc, _o, err = self.run_rc(path=empty)
        self.assertEqual(rc, 2)
        self.assertIn('no readable session files', err)
        rc, _o, err = self.run_rc(path=Path(self.tmp.name) / 'missing')
        self.assertEqual(rc, 2)
        self.assertIn('not found', err)
        self.assertNotIn('missing', err)

    def test_unparsable_prices_fail_closed(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        bad = Path(self.tmp.name) / 'prices-bad.json'
        bad.write_text('{')
        rc, out, err = self.run_rc('--json', '--prices', str(bad))
        self.assertEqual((rc, out), (2, ''))
        self.assertIn('price table', err)

    def test_deeply_nested_sidecar_is_ignored(self):
        self.write('s/subagents/agent-a.jsonl', [asst('m1', 'r1')])
        (self.dir / 's/subagents/agent-a.meta.json').write_text('[' * 2000 + '0' + ']' * 2000)
        self.assertEqual(self.report()['rows'][0]['role'], 'unknown')

    def test_deeply_nested_malformed_prices_fail_with_generic_diagnostic(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        # This is malformed JSON even when a decoder supports this nesting depth.
        # Older decoders may raise RecursionError before reaching the missing ']'.
        self.prices.write_text('[' * 2000 + '0' + ']' * 1999)
        rc, out, err = self.run_rc('--json', '--prices', str(self.prices))
        self.assertEqual((rc, out), (2, ''))
        self.assertIn('price table cannot be read', err)
        self.assertNotIn('Traceback', err)

    def test_sidecar_decoder_recursion_failure_is_ignored(self):
        meta = self.dir / 's/subagents/agent-a.meta.json'
        meta.write_text('{}')
        with mock.patch.object(ur.json, 'load', side_effect=RecursionError('private detail')):
            self.assertEqual(ur.label_text(str(meta)), '')

    def test_price_decoder_recursion_failure_has_generic_diagnostic(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        with mock.patch.object(ur.json, 'load', side_effect=RecursionError('private detail')):
            rc, out, err = self.run_rc('--json', '--prices', str(self.prices))
        self.assertEqual((rc, out), (2, ''))
        self.assertIn('price table cannot be read', err)
        self.assertNotIn('private detail', err)
        self.assertNotIn('Traceback', err)

    def test_invalid_price_values_reject_table(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        good = {'input': 1, 'output': 2, 'cache_read': 3, 'cache_write': 4}
        for bad in ('NaN', 'Infinity', '-1', 'true', '"1.0"', 'null', '1e999'):
            raw = json.dumps({'models': {'sonnet': good}}).replace('"output": 2', '"output": ' + bad)
            p = Path(self.tmp.name) / 'p.json'
            p.write_text(raw)
            rc, out, err = self.run_rc('--json', '--prices', str(p))
            self.assertEqual(rc, 0, bad)
            self.assertNotIn('NaN', out)
            rep = json.loads(out)
            self.assertEqual(rep['cost'], 'n/a', bad)
            self.assertIn('warning', err)
        p.write_text(json.dumps({'models': {'sonnet': dict(good, input=0.5, output=0)}}))
        self.assertEqual(self.report('--prices', str(p))['cost'], 'estimate')

    def test_partial_pricing_marks_totals_and_uses_token_share(self):
        self.write('s/main.jsonl', [asst('m1', 'r1', usage={'input_tokens': 5}),
                                    asst('m2', 'r2', model='claude-opus-5',
                                         usage={'input_tokens': 900}, agent='b'),
                                    asst('m3', 'r3', model='claude-opus-5',
                                         usage={'input_tokens': 90}, agent='c')])
        rep = self.report('--prices', str(self.prices))
        self.assertEqual(rep['summary']['unpriced_requests'], 2)
        self.assertEqual(rep['cost'], 'partial')
        self.assertEqual(rep['share_basis'], 'total_tokens')
        self.assertEqual([r['total_tokens'] for r in rep['rows']], [900, 90, 5])
        self.assertAlmostEqual(rep['rows'][0]['share'], 900 / 995, 3)
        text = self.run_cli('--prices', str(self.prices))
        self.assertIn('partial: 2 unpriced requests', text)
        h = Path(self.tmp.name) / 'p.html'
        self.run_cli('--prices', str(self.prices), '--html', str(h))
        self.assertIn('partial: 2 unpriced requests', h.read_text())

    def test_top_reports_hidden_rows(self):
        self.write('s/main.jsonl', [asst('m1', 'r1', usage={'input_tokens': 5}),
                                    asst('m2', 'r2', model='claude-opus-5', agent='b',
                                         usage={'input_tokens': 900})])
        rep = self.report('--prices', str(self.prices), '--top', '1')
        self.assertEqual((rep['rows_hidden'], rep['rows_hidden_unpriced']), (1, 0))
        self.assertIn('1 rows hidden', self.run_cli('--prices', str(self.prices), '--top', '1'))
        self.write('s/main.jsonl', [asst('m1', 'r1', usage={'input_tokens': 900}),
                                    asst('m2', 'r2', model='claude-opus-5', agent='b',
                                         usage={'input_tokens': 5})])
        text = self.run_cli('--prices', str(self.prices), '--top', '1')
        self.assertIn('1 rows hidden, 1 of them unpriced', text)

    def test_html_refuses_existing_destination_and_negative_args(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        h = Path(self.tmp.name) / 'keep.html'
        h.write_text('keep')
        rc, _o, err = self.run_rc('--html', str(h))
        self.assertEqual(rc, 2)
        self.assertEqual(h.read_text(), 'keep')
        self.assertNotIn('Traceback', err)
        rc, _o, err = self.run_rc('--html', str(Path(self.tmp.name) / 'nodir' / 'x.html'))
        self.assertEqual(rc, 2)
        for flag in ('--top', '--resume-gap'):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                ur.main([str(self.dir), flag, '-1'])

    def test_redaction_all_formats(self):
        self.write('s/main.jsonl', [user('desk ' + PROMPT), asst('m1', 'r1', agent='agent-' + SECRET),
                                    asst('m2', 'r2', model=PATHSEC)])
        self.write('s/subagents/agent-' + 'ab12.jsonl', [user(PROMPT), asst('m3', 'r3', agent=PATHSEC)])
        html_path = Path(self.tmp.name) / 'out.html'
        outs = [self.run_cli(), self.run_cli('--prices', str(self.prices)),
                self.run_cli('--json'), self.run_cli('--json', '--prices', str(self.prices))]
        self.run_cli('--html', str(html_path))
        outs.append(html_path.read_text())
        for out in outs:
            for bad in PLANTED:
                self.assertNotIn(bad, out)

    def test_html_is_self_contained(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        p = Path(self.tmp.name) / 'o.html'
        self.run_cli('--html', str(p))
        text = p.read_text().lower()
        for needle in ('<script', 'http://', 'https://', '<link', 'src=', '@import', 'url('):
            self.assertNotIn(needle, text)

    def test_read_only_and_example_prices_labelled(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        before = sorted((str(p), p.stat().st_mtime_ns) for p in self.dir.rglob('*'))
        self.run_cli()
        self.assertEqual(before, sorted((str(p), p.stat().st_mtime_ns) for p in self.dir.rglob('*')))
        ex = json.loads((ROOT / 'scripts/usage_prices.example.json').read_text())
        self.assertIn('NOT VENDOR-VERIFIED', ex['label'])

    def test_rollups_cost_partial_and_share(self):
        self.write('s/main.jsonl', [
            asst('m1', 'r1', usage={'input_tokens': 1000000}),
            asst('m2', 'r2', model='claude-opus-5', usage={'input_tokens': 1000}, agent='b')])
        rep = self.report('--prices', str(self.prices))
        self.assertEqual(rep['cost'], 'partial')
        by_model = {a['model']: a for a in rep['by_model']}
        self.assertEqual(by_model['claude-sonnet-5']['cost_estimate'], 1.0)
        self.assertFalse(by_model['claude-sonnet-5']['cost_partial'])
        self.assertFalse(by_model['claude-opus-5']['cost_partial'])  # nothing priced: n/a, not partial
        self.assertEqual(by_model['claude-opus-5']['unpriced_requests'], 1)
        self.assertIsNone(by_model['claude-opus-5']['cost_estimate'])
        self.assertAlmostEqual(sum(a['share'] for a in rep['by_model']), 1.0, 3)
        self.assertEqual(len(rep['by_role']), 1)  # both models share the unknown role
        self.assertTrue(rep['by_role'][0]['cost_partial'])
        self.assertEqual(rep['by_role'][0]['unpriced_requests'], 1)
        self.assertEqual(rep['by_role'][0]['cost_estimate'], 1.0)
        full = self.report()
        self.assertTrue(all(a['cost_partial'] is False for a in full['by_model']))

    def test_rollup_full_cost_share(self):
        self.write('s/main.jsonl', [
            asst('m1', 'r1', usage={'input_tokens': 3000000}),
            asst('m2', 'r2', usage={'input_tokens': 1000000}, agent='b')])
        rep = self.report('--prices', str(self.prices))
        self.assertEqual(rep['cost'], 'estimate')
        self.assertEqual(rep['by_model'][0]['cost_estimate'], 4.0)
        self.assertEqual(rep['by_model'][0]['share'], 1.0)
        self.assertFalse(rep['by_model'][0]['cost_partial'])

    def test_bad_lines_skip_safely(self):
        deep = '[' * 100000 + ']' * 100000
        huge = '{"type":"assistant","requestId":"r","message":{"id":"m","usage":{"input_tokens":%s}}}' % ('9' * 5000)
        over = json.dumps(asst('o', 'o', usage={'input_tokens': 10 ** 16}))
        self.write('s/main.jsonl', [asst('ok', 'ok')], raw=deep + '\n' + huge + '\n' + over)
        rep = self.report('--prices', str(self.prices))
        # Python >= 3.11 rejects the 5000-digit int at parse time; 3.9 parses it.
        self.assertIn(rep['summary']['requests'], (2, 3))
        self.assertGreaterEqual(rep['skipped_unknown']['malformed_lines'], 1)
        self.assertGreaterEqual(rep['skipped_unknown']['bad_usage'], 1)
        self.assertNotIn('Infinity', json.dumps(rep))

    def test_non_finite_cost_is_bad_usage(self):
        big = Path(self.tmp.name) / 'big.json'
        big.write_text(json.dumps({'models': {'sonnet': {
            'input': 1e12, 'output': 1e12, 'cache_read': 1e12, 'cache_write': 1e12}}}))
        self.write('s/main.jsonl', [asst('m1', 'r1', usage={'input_tokens': 10 ** 15})])
        rep = self.report('--prices', str(big))
        self.assertEqual(rep['summary']['requests'], 1)

    def test_unreadable_files_and_walk_errors_reported(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        bad = self.dir / 's' / 'locked.jsonl'
        bad.write_text('{}\n')
        bad.chmod(0)
        self.addCleanup(bad.chmod, 0o600)
        if os.access(bad, os.R_OK):
            self.skipTest('permissions not enforced')
        rep = self.report()
        self.assertEqual(rep['skipped_unknown']['unreadable_files'], 1)
        self.assertEqual(rep['skipped_unknown']['walk_errors'], 0)
        self.assertIn('unreadable_files=1', self.run_cli())
        locked = self.dir / 's' / 'subagents'
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o700)
        self.assertEqual(self.report()['skipped_unknown']['walk_errors'], 1)

    def test_key_like_model_names_become_unknown(self):
        for m in ('sk-ant-api03-abcdef', 'SK-upper', 'a' * 30, 'claude-sonnet-4-5-20250929'):
            self.write('s/main.jsonl', [asst('m1', 'r1', model=m)])
            row = self.report()['rows'][0]
            self.assertEqual(row['model'], 'claude-sonnet-4-5-20250929' if m.startswith('claude') else 'unknown', m)

    def test_arbitrary_model_values_are_not_rendered_or_priced(self):
        for planted in ('PRIVATE_SECRET_123', 'AKIA' + 'Q' * 16):
            self.write('s/main.jsonl', [asst('m1', 'r1', model=planted)])
            self.prices.write_text(json.dumps({'models': {planted: {
                'input': 1, 'output': 2, 'cache_read': 3, 'cache_write': 4}}}))
            rc, out, err = self.run_rc('--json', '--prices', str(self.prices))
            self.assertEqual(rc, 0)
            rep = json.loads(out)
            self.assertEqual(rep['rows'][0]['model'], 'unknown')
            self.assertEqual(rep['skipped_unknown']['unknown_model'], 1)
            self.assertIsNone(rep['rows'][0]['cost_estimate'])
            outputs = [out, err]
            for flags in ((), ('--json',)):
                _rc, rendered, diagnostic = self.run_rc(*flags)
                outputs.extend((rendered, diagnostic))
            dest = Path(self.tmp.name) / (str(len(planted)) + '.html')
            _rc, rendered, diagnostic = self.run_rc('--html', str(dest))
            outputs.extend((rendered, diagnostic, dest.read_text()))
            for rendered in outputs:
                self.assertNotIn(planted, rendered)

    def test_price_entry_missing_field_rejects_table(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        p = Path(self.tmp.name) / 'missing.json'
        p.write_text(json.dumps({'models': {'sonnet': {'input': 1, 'output': 2, 'cache_read': 3}}}))
        rc, out, err = self.run_rc('--json', '--prices', str(p))
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)['cost'], 'n/a')
        self.assertIn('warning', err)
        self.assertIn('cache_write', err)

    def test_env_prices_bad_or_missing_file_exit_2(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        bad = Path(self.tmp.name) / 'bad.json'
        bad.write_text('{')
        for val in (str(bad), str(Path(self.tmp.name) / 'absent.json')):
            old = os.environ.get('CREWBOOK_USAGE_PRICES')
            os.environ['CREWBOOK_USAGE_PRICES'] = val
            try:
                rc, out, err = self.run_rc_env()
            finally:
                if old is None:
                    os.environ.pop('CREWBOOK_USAGE_PRICES')
                else:
                    os.environ['CREWBOOK_USAGE_PRICES'] = old
            self.assertEqual((rc, out), (2, ''))
            self.assertIn('price table', err)

    def run_rc_env(self):
        # The --prices default is read when main() builds its parser, so env is honoured.
        return self.run_rc('--json')

    def test_json_and_html_mutually_exclusive(self):
        self.write('s/main.jsonl', [asst('m1', 'r1')])
        h = Path(self.tmp.name) / 'x.html'
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            ur.main([str(self.dir), '--json', '--html', str(h)])
        self.assertEqual(cm.exception.code, 2)
        self.assertFalse(h.exists())

    def test_resume_gap_boundary(self):
        self.write('s/main.jsonl', [asst('m1', 'r1', ts='2026-01-01T00:00:00Z'),
                                    asst('m2', 'r2', ts='2026-01-01T00:30:00Z')])
        self.assertEqual(self.report()['rows'][0]['resumes_estimate'], 0)
        self.assertEqual(self.report('--resume-gap', '1799')['rows'][0]['resumes_estimate'], 1)

    def test_loop_needs_five_bursts_and_regular_spacing(self):
        four = [asst('m%d' % i, 'r%d' % i, ts='2026-01-01T00:%02d:00Z' % (i * 5)) for i in range(4)]
        self.write('s/main.jsonl', four)
        self.assertNotIn('loop_estimate_unverified', self.report()['rows'][0])
        minutes = [0, 5, 10, 11, 40, 41, 90]
        self.write('s/main.jsonl', [asst('m%d' % i, 'r%d' % i, ts='2026-01-01T%02d:%02d:00Z' % divmod(m, 60))
                                    for i, m in enumerate(minutes)])
        self.assertNotIn('loop_estimate_unverified', self.report()['rows'][0])
        five = [asst('m%d' % i, 'r%d' % i, ts='2026-01-01T00:%02d:00Z' % (i * 5)) for i in range(5)]
        self.write('s/main.jsonl', five)
        self.assertEqual(self.report()['rows'][0]['loop_estimate_unverified']['bursts'], 5)


if __name__ == '__main__':
    unittest.main()
