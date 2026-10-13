"""Offline exact-revision merge-method observations, never forge mutations."""
import copy
import shutil
import shlex
import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from git_test_environment import isolated_git_environment
from merge_readiness import local_history, observe

HEAD = 'a' * 40
BASE = 'b' * 40


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.pr = {'head': {'sha': HEAD}, 'base': {'sha': BASE},
                   'mergeable': True, 'mergeable_state': 'clean', 'rebaseable': True}

    def result(self, **kwargs):
        return observe(self.pr, configured_method='rebase', method='rebase',
                       head=HEAD, base=BASE, **kwargs)

    def test_rebase_false_despite_clean_mergeable_and_green_ci(self):
        self.pr.update(rebaseable=False, checks='SUCCESS')
        self.assertEqual(self.result()['state'], 'blocked')

    def test_rebase_unknown_pending(self):
        for value in (None, 'true', 1):
            with self.subTest(value=value):
                self.pr['rebaseable'] = value
                self.assertEqual(self.result()['state'], 'pending')
        del self.pr['rebaseable']
        self.assertEqual(self.result()['state'], 'pending')

    def test_stale_head_or_base_pending(self):
        for key in ('head', 'base'):
            with self.subTest(key=key):
                pr = copy.deepcopy(self.pr)
                pr[key]['sha'] = 'c' * 40
                self.assertEqual(observe(pr, 'rebase', 'rebase', HEAD, BASE)['state'], 'pending')

    def test_wrong_configured_method_blocked(self):
        self.assertEqual(observe(self.pr, 'rebase', 'merge', HEAD, BASE)['state'], 'blocked')

    def test_positive_and_other_explicit_method(self):
        self.assertEqual(self.result()['state'], 'ready')
        self.pr['rebaseable'] = False
        self.assertEqual(observe(self.pr, 'merge', 'merge', HEAD, BASE)['state'], 'ready')

    def test_missing_policy_and_invalid_sha_pending(self):
        self.assertEqual(observe(self.pr, None, 'rebase', HEAD, BASE)['state'], 'pending')
        self.assertEqual(observe(self.pr, 'rebase', 'rebase', 'a', BASE)['state'], 'pending')


@unittest.skipUnless(shutil.which('git'), 'Git unavailable')
class LocalHistoryTests(unittest.TestCase):
    def test_missing_promisor_objects_never_fetch_or_write(self):
        with tempfile.TemporaryDirectory() as directory:
            origin = Path(directory) / 'origin'
            local = Path(directory) / 'local'
            origin.mkdir()
            local.mkdir()
            env = isolated_git_environment()

            def run(root, *args):
                return subprocess.run(['git', '-C', str(root), *args], env=env,
                                      check=True, capture_output=True, text=True).stdout.strip()

            run(origin, 'init', '-q')
            run(origin, 'commit', '-q', '--allow-empty', '-m', 'base')
            base = run(origin, 'rev-parse', 'HEAD')
            run(origin, 'commit', '-q', '--allow-empty', '-m', 'topic')
            head = run(origin, 'rev-parse', 'HEAD')
            run(local, 'init', '-q')
            run(local, 'remote', 'add', 'origin', origin.as_uri())
            run(local, 'config', 'remote.origin.promisor', 'true')
            marker = Path(directory) / 'transport-started'
            uploadpack = Path(directory) / 'uploadpack'
            uploadpack.write_text('#!/bin/sh\nprintf touched > ' + shlex.quote(str(marker)) +
                                  '\nexec git-upload-pack "$@"\n')
            uploadpack.chmod(0o700)
            run(local, 'config', 'remote.origin.uploadpack', str(uploadpack))
            objects = local / '.git' / 'objects'
            before = sorted(str(path.relative_to(objects)) for path in objects.rglob('*'))
            result = local_history(str(local), head, base)
            after = sorted(str(path.relative_to(objects)) for path in objects.rglob('*'))
            self.assertEqual(result['state'], 'pending')
            self.assertEqual(after, before, 'observation must not materialize promisor objects')
            self.assertFalse(marker.exists(), 'observation must not start transport')

    def test_complete_linear_and_topic_merge_histories(self):
        with tempfile.TemporaryDirectory() as directory:
            env = isolated_git_environment()

            def run(*args):
                return subprocess.run(['git', '-C', directory, *args], env=env,
                                      check=True, capture_output=True, text=True).stdout.strip()

            run('init', '-q')
            run('commit', '-q', '--allow-empty', '-m', 'base')
            base = run('rev-parse', 'HEAD')
            run('checkout', '-q', '-b', 'topic')
            run('commit', '-q', '--allow-empty', '-m', 'topic')
            head = run('rev-parse', 'HEAD')
            self.assertEqual(local_history(directory, head, base),
                             {'state': 'ready', 'topic_merge_count': 0})
            run('checkout', '-q', '-b', 'other', base)
            run('commit', '-q', '--allow-empty', '-m', 'other')
            other = run('rev-parse', 'HEAD')
            self.assertEqual(local_history(directory, head, other)['state'], 'blocked')
            run('checkout', '-q', 'topic')
            run('merge', '-q', '--no-ff', 'other', '-m', 'merge')
            merged = run('rev-parse', 'HEAD')
            self.assertEqual(local_history(directory, merged, base),
                             {'state': 'blocked', 'topic_merge_count': 1})
            self.assertEqual(local_history(directory, 'c' * 40, base)['state'], 'pending')
            self.assertEqual(run('rev-parse', 'HEAD'), merged)
            self.assertEqual(run('status', '--porcelain'), '')


class CliTests(unittest.TestCase):
    def test_cli_exit_states_and_malformed_input(self):
        command = [sys.executable, '-B', str(Path(__file__).with_name('merge_readiness.py')),
                   '--configured-method', 'rebase', '--method', 'rebase',
                   '--head', HEAD, '--base', BASE]
        for value, code, state in ((True, 0, 'ready'), (False, 1, 'blocked'), (None, 2, 'pending')):
            with self.subTest(value=value):
                pr = {'head': {'sha': HEAD}, 'base': {'sha': BASE}, 'rebaseable': value}
                result = subprocess.run(command, input=json.dumps(pr), text=True, capture_output=True)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(json.loads(result.stdout)['state'], state)
        result = subprocess.run(command, input='{', text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
