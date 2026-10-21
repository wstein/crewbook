import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PrWatchTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('bash') and shutil.which('jq'), 'needs bash and jq')
    def test_shell_suite_passes_against_fake_gh(self):
        r = subprocess.run(['bash', str(ROOT / 'tools/pr-watch/test_pr_watch.sh')],
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=600)
        self.assertEqual(r.returncode, 0, r.stdout[-3000:])
        self.assertNotIn('FAIL - ', r.stdout)


if __name__ == '__main__':
    unittest.main()
