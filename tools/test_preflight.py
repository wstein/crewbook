"""Credential-free command evidence scenarios; no agent/runtime enforcement."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


def command(argv, **kwargs):
    return subprocess.run(argv, capture_output=True, text=True, **kwargs)


class PreflightScenarios(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='crewbook-preflight-')
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name).resolve(strict=True)
        self.parent.chmod(0o700)

    def python(self, source, *args):
        return command([sys.executable, '-B', '-c', source, *args])

    def test_unchanged_denial_and_explicit_read_recovery(self):
        # Synthetic transport: caller explicitly selects the approved read path.
        # No permission decision, credentials or network are implemented here.
        transport = ('import sys; approved = sys.argv[1:] == ["approved", "read"]; '
                     'print("read evidence" if approved else "sandbox DNS denied", '
                     'file=sys.stdout if approved else sys.stderr); '
                     'sys.exit(0 if approved else 77)')
        first = self.python(transport, 'sandbox', 'read')
        unchanged = self.python(transport, 'sandbox', 'read')
        recovered = self.python(transport, 'approved', 'read')
        write = self.python(transport, 'approved', 'write')
        self.assertEqual((first.returncode, first.stderr),
                         (unchanged.returncode, unchanged.stderr))
        self.assertEqual(first.returncode, 77)
        self.assertEqual((recovered.returncode, recovered.stdout), (0, 'read evidence\n'))
        self.assertEqual(write.returncode, 77)
        self.assertEqual(first.stderr, 'sandbox DNS denied\n')

    def test_independent_failure_survives_later_success(self):
        results = [self.python('import sys; print("failed prerequisite", file=sys.stderr); sys.exit(3)'),
                   self.python('print("independent success")')]
        self.assertEqual([r.returncode for r in results], [3, 0])
        self.assertEqual(results[0].stderr, 'failed prerequisite\n')
        self.assertEqual(results[1].stdout, 'independent success\n')

    def test_shell_endpoint_is_one_literal_argument(self):
        shell = shutil.which('zsh') or shutil.which('sh')
        if shell is None:
            self.skipTest('no POSIX shell available')
        stub = self.parent / 'argv.py'
        stub.write_text('import json, sys; print(json.dumps(sys.argv[1:]))\n')
        import shlex
        endpoint = 'repos/example/demo/issues?state=open&per_page=20'
        result = command([shell, '-c', '{} {} api {}'.format(
            shlex.quote(sys.executable), shlex.quote(str(stub)), shlex.quote(endpoint))],
            cwd=str(self.parent))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ['api', endpoint])

    def test_expected_search_negative_and_search_error(self):
        rg = shutil.which('rg')
        if rg is None:
            self.skipTest('rg unavailable; optional native search scenario')
        file = self.parent / 'input.txt'
        file.write_text('present\n')
        absent = command([rg, 'absent', str(file)])
        error = command([rg, 'absent', str(self.parent / 'missing')])
        self.assertEqual((absent.returncode, absent.stderr), (1, ''))
        self.assertEqual(error.returncode, 2)
        self.assertTrue(error.stderr)

    def test_unset_git_config_is_not_config_error(self):
        git = shutil.which('git')
        if git is None:
            self.skipTest('Git unavailable; optional native config scenario')
        config = self.parent / 'config'
        config.write_text('')
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        absent = command([git, 'config', '--file', str(config), '--get', 'fixture.absent'], env=env)
        config.write_text('[broken\n')
        error = command([git, 'config', '--file', str(config), '--get', 'fixture.absent'], env=env)
        self.assertEqual((absent.returncode, absent.stderr), (1, ''))
        self.assertNotEqual(error.returncode, 0)
        self.assertTrue(error.stderr)

    def test_missing_policy_and_real_export_boundaries(self):
        # Use the real CLI and current source inventory; never execute prompts.
        cli = [sys.executable, '-B', str(ROOT / 'tools/crewbook-package.py')]
        missing = command(cli + ['check', '--root', str(ROOT), '--policy',
                                 str(self.parent / 'missing-policy.json')])
        self.assertEqual(missing.returncode, 1)
        self.assertTrue(missing.stderr)
        shared = self.parent / 'shared'
        shared.mkdir(mode=0o777)
        shared.chmod(0o777)
        unsafe = command(cli + ['export', '--root', str(ROOT), '--dest', str(shared / 'child')])
        self.assertEqual(unsafe.returncode, 1)
        self.assertFalse((shared / 'child').exists())
        destination = self.parent / 'new-child'
        valid = command(cli + ['export', '--root', str(ROOT), '--dest', str(destination)])
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertTrue((destination / 'SKILL.md').is_file())
        existing = command(cli + ['export', '--root', str(ROOT), '--dest', str(destination)])
        self.assertEqual(existing.returncode, 1)
        alias = self.parent / 'alias'
        alias.symlink_to(destination, target_is_directory=True)
        symlink = command(cli + ['export', '--root', str(ROOT), '--dest', str(alias)])
        self.assertEqual(symlink.returncode, 1)
        self.assertTrue(alias.is_symlink())


if __name__ == '__main__':
    unittest.main()
