import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts'))
import stray_processes as sp  # noqa: E402

D = '/var/folders/ab/xyz/T/TestSourceInstallUnpublishedMain123/003'
ORPHAN = ' 4242     1 18:03:11 99.2 /bin/sh %s/go env GOFLAGS\n' % D
BUSY = ' 5000  4900    42:10 97.0 /bin/sh %s/go test -race ./...\n' % D
YOUNG = ' 5001  4900     2:10 97.0 /bin/sh %s/go test ./...\n' % D
OTHER = ' 6000     1 3-04:05:06 99.0 /usr/bin/python3 /Users/x/job.py\n'


class StrayTests(unittest.TestCase):
    def test_orphan_reported_with_details(self):
        s, _ = sp.find_stray(ORPHAN)
        self.assertEqual([p['pid'] for p in s], [4242])
        self.assertTrue(s[0]['orphan'])
        self.assertEqual(s[0]['test'], 'TestSourceInstallUnpublishedMain')
        out = sp.render(s)
        self.assertIn('kill 4242', out)
        self.assertIn('kill -KILL 4242', out)
        self.assertIn('nothing was killed', out)

    def test_busy_old_child_with_live_parent_reported(self):
        s, _ = sp.find_stray(BUSY)
        self.assertEqual([p['pid'] for p in s], [5000])
        self.assertFalse(s[0]['orphan'])

    def test_young_busy_child_with_live_parent_not_stray(self):
        self.assertEqual(sp.find_stray(YOUNG)[0], [])

    def test_unrelated_process_ignored(self):
        self.assertEqual(sp.find_stray(OTHER)[0], [])

    def test_pytest_dir_matches(self):
        t = ' 7 1 10:00 1.0 python /tmp/pytest-of-bob/pytest-3/test_x0/run.py\n'
        self.assertEqual([p['pid'] for p in sp.find_stray(t)[0]], [7])

    def test_empty_output(self):
        self.assertEqual(sp.render(*sp.find_stray('')), 'no stray test processes\n')

    def test_etime_forms(self):
        self.assertEqual(sp.etime_seconds('05:07'), 307)
        self.assertEqual(sp.etime_seconds('1:02:03'), 3723)
        self.assertEqual(sp.etime_seconds('2-00:00:01'), 172801)
        self.assertIsNone(sp.etime_seconds('x'))

    def test_old_idle_non_orphan_not_reported(self):
        t = ' 8 4900 50:00 0.5 /bin/sh %s/go test\n' % D
        self.assertEqual(sp.find_stray(t)[0], [])

    def test_var_tmp_matches_and_unanchored_does_not(self):
        ok = ' 9 1 10:00 1.0 sh /var/tmp/TestA1/x\n'
        no = ' 10 1 10:00 1.0 sh /home/u/proj/tmp/TestData/x\n'
        self.assertEqual([p['pid'] for p in sp.find_stray(ok)[0]], [9])
        self.assertEqual(sp.find_stray(no)[0], [])

    def test_tmpdir_env_root(self):
        t = ' 11 1 10:00 1.0 sh /data/scratch/TestB1/x\n'
        self.assertEqual(sp.find_stray(t)[0], [])
        self.assertEqual(len(sp.find_stray(t, tmpdir='/data/scratch')[0]), 1)

    def test_u2028_cannot_fake_a_block(self):
        cmd = 'sh /tmp/TestX1/go\u2028 99 1 99:00 99.0 /tmp/TestEvil/x'
        t = ' 12 1 10:00 1.0 %s\n' % cmd
        s, bad = sp.find_stray(t)
        self.assertEqual([p['pid'] for p in s], [12])
        out = sp.render(s)
        self.assertNotIn('\u2028', out)
        self.assertNotIn('\npid 99', out)

    def test_verify_drops_changed_process(self):
        s, _ = sp.find_stray(ORPHAN, verify=lambda pid: None)
        self.assertEqual(s, [])
        s, _ = sp.find_stray(ORPHAN, verify=lambda pid: (1, '/bin/sh %s/go env GOFLAGS' % D))
        self.assertEqual(len(s), 1)

    def test_non_utf8_input_does_not_crash(self):
        raw = b' 13 1 10:00 1.0 sh /tmp/TestC1/\xff\xfe\n'
        s, _ = sp.find_stray(raw.decode('utf-8', errors='replace'))
        self.assertEqual(len(s), 1)

    def test_escapes_and_caps(self):
        t = ' 14 1 10:00 1.0 sh /tmp/TestD1/\x1b[31m\u202e%s\n' % ('a' * 500)
        out = sp.render(sp.find_stray(t)[0])
        self.assertNotIn('\x1b', out)
        self.assertNotIn('\u202e', out)
        self.assertTrue(all(len(l) < 260 for l in out.split('\n')))

    def test_comma_cpu_row_reported_unparsed(self):
        t = ' 15 1 10:00 99,1 sh /tmp/TestE1/x\n'
        s, bad = sp.find_stray(t)
        self.assertEqual((s, bad), ([], 1))
        self.assertIn('1 ps rows not parsed', sp.render(s, bad))

    def test_children_listed_and_no_literal_percent_pair(self):
        t = BUSY + ' 5002  5000     1:00 1.0 sleep 1\n'
        s, _ = sp.find_stray(t)
        self.assertEqual(s[0]['children'], [5002])
        self.assertNotIn('%%', sp.render(s))


if __name__ == '__main__':
    unittest.main()
