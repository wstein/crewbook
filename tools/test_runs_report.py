import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts'))
import runs_report as rr  # noqa: E402

HEAD = '# %s\n%s\n' % (rr.SCHEMA, '\t'.join(rr.COLUMNS))


def row(*v):
    return '\t'.join(map(str, v)) + '\n'


# Fixture from the #108 baseline table (indicative example, not real data).
BASELINE = HEAD + ''.join([
    row('2026-10-09', '#510', 'author', 'sonnet', 'medium', 70800, 11.6, 0, 0, 0, 0, '-', 'n'),
    row('2026-10-09', '#510', 'author', 'sonnet', 'medium', 19100, 10.8, 3, 0, 2, 0, 'n', 'y'),
    row('2026-10-09', '#507', 'author', 'sonnet', 'medium', 105900, 9.2, 2, 0, 0, 3, 'y', 'y'),
    row('2026-10-09', '#510', 'reviewer', 'opus', 'high', 92900, 6.3, 3, 0, 1, 0, '-', 'n'),
    row('2026-10-09', '#510', 'reviewer', 'opus', 'high', 87500, 5.6, 3, 0, 1, 0, '-', 'y'),
])


class RunsReport(unittest.TestCase):
    def write(self, text):
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'sub', 'RUNS.tsv')
        os.makedirs(os.path.dirname(p))
        Path(p).write_text(text, encoding='utf-8')
        return p

    def test_baseline_summary(self):
        p = self.write(BASELINE)
        rows, bad = rr.load(p)
        self.assertEqual(bad, 0)
        g = {(s['role'], s['model']): s for s in rr.summarise(rows)}
        a = g[('author', 'sonnet')]
        self.assertEqual((a['prs'], a['clear']), (2, 2))
        self.assertEqual(a['tokens_per_clear'], 97900)
        self.assertEqual(a['findings_per_pr'], {'high': 0.0, 'medium': 1.0, 'low': 1.5})
        self.assertEqual(a['minutes_per_clear'], 15.8)
        self.assertEqual(a['rounds_per_pr'], 2.5)
        self.assertEqual(a['ci_first_try_rate'], 0.5)
        self.assertFalse(a['enough_data'])
        r = g[('reviewer', 'opus')]
        self.assertEqual((r['prs'], r['clear']), (1, 1))
        self.assertEqual(r['tokens_per_clear'], 180400)
        self.assertEqual(r['findings_per_pr'], {'high': 0.0, 'medium': 2.0, 'low': 0.0})
        self.assertIsNone(r['ci_first_try_rate'])

    def test_enough_data_at_ten_prs(self):
        text = HEAD + ''.join(row('2026-10-09', '#%d' % i, 'author', 'sonnet', 'low', 1000,
                                  1, 1, 0, 0, 0, 'y', 'y') for i in range(100, 110))
        rows, _ = rr.load(self.write(text))
        s = rr.summarise(rows)[0]
        self.assertTrue(s['enough_data'])
        self.assertEqual(s['ci_first_try_rate'], 1.0)
        self.assertNotIn('not enough data', rr.render(rr.summarise(rows), 0))

    def test_not_enough_data_flag_rendered(self):
        rows, _ = rr.load(self.write(BASELINE))
        self.assertIn('not enough data', rr.render(rr.summarise(rows), 0))

    def test_invalid_rows_skipped_and_free_text_rejected(self):
        bad = [
            row('2026-10-09', '#1', 'author', 'sonnet token=sk-ant-SECRET', 'low', 1, 1, 0, 0, 0, 0, '-', 'n'),
            row('2026-10-09', '/Users/x/y', 'author', 'sonnet', 'low', 1, 1, 0, 0, 0, 0, '-', 'n'),
            row('2026-10-09', '#1', 'boss', 'sonnet', 'low', 1, 1, 0, 0, 0, 0, '-', 'n'),
            row('2026-10-09', '#1', 'author', 'sonnet', 'low', -1, 1, 0, 0, 0, 0, '-', 'n'),
            'too\tfew\n',
        ]
        rows, nbad = rr.load(self.write(HEAD + ''.join(bad) + BASELINE[len(HEAD):]))
        self.assertEqual((len(rows), nbad), (5, 5))

    def test_schema_and_header_required(self):
        for text in ('', 'x\n', '# %s\nwrong\n' % rr.SCHEMA):
            with self.assertRaises(ValueError):
                rr.load(self.write(text))

    def test_record_creates_file_and_roundtrips(self):
        d = tempfile.mkdtemp()
        f = os.path.join(d, 'new', 'RUNS.tsv')
        args = ['record', '--file', f, '--date', '2026-10-09', '--ref', '#510', '--role', 'author',
                '--model', 'sonnet', '--effort', 'medium', '--tokens', '70800', '--minutes', '11.6',
                '--rounds', '3', '--medium', '2', '--ci', 'n', '--clear', 'y']
        self.assertEqual(rr.main(args), 0)
        self.assertEqual(rr.main(args), 0)
        text = Path(f).read_text()
        self.assertEqual(text.count(rr.SCHEMA), 1)
        rows, bad = rr.load(f)
        self.assertEqual((len(rows), bad), (2, 0))
        with self.assertRaises(SystemExit):
            rr.main(['record', '--file', f, '--date', 'bad', '--ref', '1', '--role', 'author',
                     '--model', 'm', '--effort', 'e', '--tokens', '1', '--minutes', '1'])

    def test_uncleared_pr_denominator(self):
        text = HEAD + row('2026-10-09', '#1', 'author', 'sonnet', 'low', 1000, 2, 1, 0, 0, 0, 'y', 'y') \
            + row('2026-10-09', '#2', 'author', 'sonnet', 'low', 3000, 4, 0, 0, 0, 0, '-', 'n')
        s = rr.summarise(rr.load(self.write(text))[0])[0]
        self.assertEqual((s['prs'], s['clear'], s['tokens_per_clear']), (2, 1, 4000))
        none = HEAD + row('2026-10-09', '#2', 'author', 'sonnet', 'low', 3000, 4, 0, 0, 0, 0, '-', 'n')
        s = rr.summarise(rr.load(self.write(none))[0])[0]
        self.assertIsNone(s['tokens_per_clear'])
        self.assertIsNone(s['minutes_per_clear'])

    def test_zero_rounds_ignored_and_ref_forms_same_pr(self):
        text = HEAD + row('2026-10-09', '510', 'author', 'sonnet', 'low', 1, 1, 4, 0, 0, 0, 'y', 'y') \
            + row('2026-10-09', '#510', 'author', 'sonnet', 'low', 1, 1, 0, 0, 0, 0, '-', 'n')
        s = rr.summarise(rr.load(self.write(text))[0])[0]
        self.assertEqual((s['prs'], s['rounds_per_pr']), (1, 4.0))

    def test_field_ranges_flags_and_unicode(self):
        base = ['2026-10-09', '#1', 'author', 'sonnet', 'low', '1', '1', '0', '0', '0', '0', '-', 'n']

        def ok(**kw):
            v = list(base)
            for k, x in kw.items():
                v[rr.COLUMNS.index(k)] = x
            return rr.parse_row('\t'.join(v))[0] is not None
        self.assertTrue(ok())
        self.assertFalse(ok(minutes='100000'))
        self.assertFalse(ok(minutes='-1'))
        self.assertFalse(ok(minutes='nan'))
        self.assertTrue(ok(minutes='99999.9'))
        self.assertFalse(ok(ci_first_try='x'))
        self.assertFalse(ok(clear='-'))
        self.assertTrue(ok(ci_first_try='n', clear='y'))
        self.assertFalse(ok(tokens='\u00b2'))
        self.assertFalse(ok(model='sonnet\n'))
        self.assertFalse(ok(date='2026-10-09\n'))
        self.assertFalse(ok(ref='#1\n'))

    def test_record_rejects_trailing_newline(self):
        f = os.path.join(tempfile.mkdtemp(), 'R.tsv')
        with self.assertRaises(SystemExit):
            rr.main(['record', '--file', f, '--date', '2026-10-09', '--ref', '1', '--role', 'author',
                     '--model', 'sonnet\n', '--effort', 'low', '--tokens', '1', '--minutes', '1'])
        self.assertFalse(os.path.exists(f))

    def test_cli_report_and_missing_file(self):
        p = self.write(BASELINE)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(rr.main(['report', '--file', p, '--json']), 0)
        self.assertIn('"tokens_per_clear": 97900', out.getvalue())
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(rr.main(['report', '--file', p + '.none']), 1)


if __name__ == '__main__':
    unittest.main()
