"""Optional offline fixtures for the separately installed pinned secret scanner."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SCANNER = os.environ.get('GITLEAKS_TEST_BINARY')


@unittest.skipUnless(SCANNER, 'set GITLEAKS_TEST_BINARY for pinned scanner fixtures')
class ScannerTests(unittest.TestCase):
    def test_clean_empty_history_tree_message_and_redaction(self):
        environment = {
            'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
            'TMPDIR': tempfile.gettempdir(),
            'GIT_CONFIG_SYSTEM': '/dev/null', 'GIT_CONFIG_GLOBAL': '/dev/null',
            'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_COUNT': '1',
            'GIT_CONFIG_KEY_0': 'credential.helper', 'GIT_CONFIG_VALUE_0': '',
            'SSH_AUTH_SOCK': '', 'GIT_SSH_COMMAND': 'ssh -oBatchMode=yes -oIdentityAgent=none',
            'GIT_AUTHOR_NAME': 'Scanner Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
            'GIT_COMMITTER_NAME': 'Scanner Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
        }
        marker = 'gh' + 'p_' + 'aK9mQ2vB8cR5' + 'xT1nL7pD4sF6' + 'jH3wZ0uE9yG2'
        for variant in ('clean', 'empty', 'history', 'tree', 'message'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as temp:
                base = Path(temp).resolve()
                root = base / 'repo'
                root.mkdir()
                def git(*args):
                    result = subprocess.run(['git'] + list(args), cwd=str(root), env=environment,
                                            capture_output=True, timeout=30)
                    self.assertEqual(result.returncode, 0, 'isolated fixture Git failed')
                git('init', '--quiet')
                (root / 'tools').mkdir()
                (root / 'tools/gitleaks.toml').write_bytes((ROOT / 'tools/gitleaks.toml').read_bytes())
                (root / 'clean.txt').write_text('offline scanner fixture\n')
                if variant == 'history':
                    (root / 'history.txt').write_text(marker + '\n')
                if variant != 'empty':
                    git('add', '.')
                    message = base / 'message'
                    message.write_text('offline fixture\n' + (marker + '\n' if variant == 'message' else ''))
                    message.chmod(0o600)
                    git('commit', '--quiet', '-F', str(message))
                if variant == 'history':
                    git('rm', '--quiet', 'history.txt')
                    git('commit', '--quiet', '-m', 'remove fixture marker')
                if variant == 'tree':
                    (root / 'untracked.txt').write_text(marker + '\n')
                result = subprocess.run(['bash', str(ROOT / 'tools/scan-secrets.sh'), str(root), SCANNER],
                                        env=environment, capture_output=True, text=True, timeout=60)
                self.assertNotIn(marker, result.stdout + result.stderr, 'synthetic marker was not redacted')
                self.assertEqual(result.returncode, 0 if variant == 'clean' else 1)
                if variant == 'clean':
                    self.assertIn('nonempty full history', result.stderr)


if __name__ == '__main__':
    unittest.main()
