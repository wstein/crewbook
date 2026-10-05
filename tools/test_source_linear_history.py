"""Native isolated Git acceptance tests for the source-only main guard."""
import pathlib
import subprocess
import tempfile
import sys
import unittest
from git_test_environment import isolated_git_environment

ROOT = pathlib.Path(__file__).resolve().parent


class MainGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name).resolve() / 'repo'
        self.repo.mkdir()
        self.env = isolated_git_environment()
        self.serial = 0
        self.git('init', '-b', 'main')
        (self.repo / 'tools/git-hooks').mkdir(parents=True)
        (self.repo / 'tools/source_linear_history.py').write_bytes((ROOT / 'source_linear_history.py').read_bytes())
        (self.repo / 'tools/git-hooks/reference-transaction').write_bytes((ROOT / 'git-hooks/reference-transaction').read_bytes())
        self.git('add', 'tools')
        self.git('commit', '-m', 'base')
        self.base = self.git('rev-parse', 'HEAD').stdout.strip()
        result = subprocess.run([sys.executable, '-I', str(ROOT / 'source_linear_history.py'),
            'install', '--root', str(self.repo), '--reviewed-sha', self.base,
            '--confirm-effective-hook-routing'], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.hook = self.repo / '.git/crewbook-source-guards' / self.base / 'reference-transaction'

    def git(self, *args, ok=True):
        result = subprocess.run(['git', '-C', str(self.repo), *args], env=self.env,
                                text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def commit(self, parent, *extra):
        self.serial += 1
        tree = self.git('rev-parse', self.base + '^{tree}').stdout.strip()
        return self.git('commit-tree', tree, '-p', parent, *extra, '-m', 'candidate ' + str(self.serial)).stdout.strip()

    def reject(self, new):
        result = self.git('update-ref', 'refs/heads/main', new, ok=False)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('rev-parse', 'main').stdout.strip(), self.base)

    def test_rejects_merge_in_fast_forward_range(self):
        side = self.commit(self.base)
        other = self.commit(self.base)
        self.reject(self.commit(side, '-p', other))

    def test_rejects_non_fast_forward(self):
        linear = self.commit(self.base)
        self.git('update-ref', 'refs/heads/main', linear)
        result = self.git('update-ref', 'refs/heads/main', self.base, ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git('rev-parse', 'main').stdout.strip(), linear)

    def test_allows_linear_and_other_refs(self):
        linear = self.commit(self.base)
        self.git('update-ref', 'refs/heads/main', linear)
        self.git('update-ref', 'refs/heads/topic', self.base)

    def test_explicit_old_and_historical_merge(self):
        side = self.commit(self.base)
        merge = self.commit(side, '-p', self.commit(self.base))
        hook = self.hook
        hook.rename(hook.with_suffix('.disabled'))
        self.git('update-ref', 'refs/heads/main', merge)
        hook.with_suffix('.disabled').rename(hook)
        linear = self.commit(merge)
        self.git('update-ref', 'refs/heads/main', linear, merge)
        result = self.git('update-ref', 'refs/heads/main', merge, linear, ok=False)
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_missing_main_creation(self):
        hook = self.hook
        hook.rename(hook.with_suffix('.disabled'))
        self.git('update-ref', '-d', 'refs/heads/main')
        hook.with_suffix('.disabled').rename(hook)
        result = self.git('update-ref', 'refs/heads/main', self.base, ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(self.git('show-ref', '--verify', 'refs/heads/main', ok=False).returncode, 0)

    def test_rejects_deletion_and_creation(self):
        result = self.git('update-ref', '-d', 'refs/heads/main', ok=False)
        self.assertNotEqual(result.returncode, 0)
        result = self.git('update-ref', 'refs/heads/main', self.base, '0' * 40, ok=False)
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_entire_multi_ref_transaction(self):
        side = self.commit(self.base)
        merge = self.commit(side, '-p', self.commit(self.base))
        result = subprocess.run(['git', '-C', str(self.repo), 'update-ref', '--stdin'],
            input='start\nupdate refs/heads/main ' + merge + '\ncreate refs/heads/topic ' + side + '\nprepare\ncommit\n',
            env=self.env, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(self.git('show-ref', '--verify', 'refs/heads/topic', ok=False).returncode, 0)

    def test_replacement_cannot_hide_introduced_merge(self):
        side = self.commit(self.base)
        merge = self.commit(side, '-p', self.commit(self.base))
        self.git('replace', merge, self.commit(self.base))
        self.reject(merge)

    def test_symbolic_main_refused(self):
        hook = self.hook
        hook.rename(hook.with_suffix('.disabled'))
        self.git('update-ref', 'refs/heads/topic', self.base)
        self.git('symbolic-ref', 'refs/heads/main', 'refs/heads/topic')
        hook.with_suffix('.disabled').rename(hook)
        result = self.git('update-ref', '--no-deref', 'refs/heads/main', self.commit(self.base), ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git('symbolic-ref', 'refs/heads/main').stdout.strip(), 'refs/heads/topic')


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name).resolve() / 'repo'
        self.repo.mkdir()
        self.env = isolated_git_environment()
        self.git('init', '-b', 'main')
        (self.repo / 'tools/git-hooks').mkdir(parents=True)
        for name in ('source_linear_history.py', 'git_test_environment.py'):
            (self.repo / 'tools' / name).write_bytes((ROOT / name).read_bytes())
        (self.repo / 'tools/git-hooks/reference-transaction').write_bytes((ROOT / 'git-hooks/reference-transaction').read_bytes())
        self.git('add', 'tools')
        self.git('commit', '-m', 'reviewed source fixture')
        self.sha = self.git('rev-parse', 'HEAD').stdout.strip()
        self.destination = self.repo / '.git/crewbook-source-guards' / self.sha

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.repo), *args], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def invoke(self, command='install', ok=True, root=None, confirm=True, script=None):
        args = [sys.executable, '-I', str(script or ROOT / 'source_linear_history.py'), command,
                '--root', str(root or self.repo), '--reviewed-sha', self.sha]
        if confirm:
            args.append('--confirm-effective-hook-routing')
        result = subprocess.run(args, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        return result

    def test_install_verify_and_linked_older_checkout(self):
        self.invoke()
        self.invoke('verify')
        linked = self.repo.parent / 'linked'
        self.git('worktree', 'add', '--detach', str(linked), self.sha)
        self.git('config', 'source.unrelated', 'keep')
        self.invoke('verify', root=linked)
        tree = self.git('rev-parse', 'HEAD^{tree}').stdout.strip()
        linear = self.git('commit-tree', tree, '-p', self.sha, '-m', 'linear').stdout.strip()
        result = subprocess.run(['git', '-C', str(linked), 'update-ref', 'refs/heads/main', linear],
            env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('config', '--get', 'source.unrelated').stdout.strip(), 'keep')
        # Installation has no dependency on checked-out source files.
        (linked / 'tools/source_linear_history.py').unlink()
        self.invoke('verify', root=linked)
        self.assertNotEqual(subprocess.run(['git', '-C', str(linked), 'update-ref', 'refs/heads/main', self.sha],
            env=self.env, capture_output=True).returncode, 0)

    def test_hook_binds_target_repository_despite_alternate_worktree(self):
        self.invoke()
        tree = self.git('rev-parse', 'HEAD^{tree}').stdout.strip()
        linear = self.git('commit-tree', tree, '-p', self.sha, '-m', 'target linear').stdout.strip()
        self.git('update-ref', 'refs/heads/main', linear)
        alternate = self.repo.parent / 'alternate'
        self.git('clone', '--no-hardlinks', str(self.repo), str(alternate))
        result = subprocess.run(['git', '-C', str(alternate), 'update-ref', 'refs/heads/main', self.sha],
            env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(['git', '--git-dir=' + str(self.repo / '.git'),
            '--work-tree=' + str(alternate), 'update-ref', 'refs/heads/main', self.sha],
            cwd=alternate, env=self.env, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('rev-parse', 'main').stdout.strip(), linear)
        next_linear = self.git('commit-tree', tree, '-p', linear, '-m', 'target-only object').stdout.strip()
        command = ['git', '-C', str(alternate), '--git-dir=' + str(self.repo / '.git'),
                   '--work-tree=' + str(alternate), 'update-ref', 'refs/heads/main']
        result = subprocess.run(command + [next_linear], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        side = self.git('commit-tree', tree, '-p', self.sha, '-m', 'side').stdout.strip()
        merge = self.git('commit-tree', tree, '-p', next_linear, '-p', side, '-m', 'merge').stdout.strip()
        result = subprocess.run(command + [merge], env=self.env, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('rev-parse', 'main').stdout.strip(), next_linear)
        self.assertEqual(subprocess.run(['git', '-C', str(alternate), 'rev-parse', 'main'],
            env=self.env, text=True, capture_output=True).stdout.strip(), self.sha)

    def test_existing_hooks_and_config_preserved(self):
        hook = self.repo / '.git/hooks/pre-commit'
        hook.write_text('existing user bytes\n')
        self.invoke(ok=False)
        self.assertEqual(hook.read_text(), 'existing user bytes\n')
        hook.unlink()
        self.git('config', 'core.hooksPath', 'user-hooks')
        self.invoke(ok=False)
        self.assertEqual(self.git('config', '--get', 'core.hooksPath').stdout.strip(), 'user-hooks')

    def test_confirmation_pins_and_tampering(self):
        self.invoke(ok=False, confirm=False)
        self.invoke()
        guard = self.destination / 'source_linear_history.py'
        guard.chmod(0o600)
        guard.write_text('changed\n')
        self.invoke('verify', ok=False)
        self.invoke(ok=False)
        self.assertEqual(guard.read_text(), 'changed\n')

    def test_isolated_environment_matches_shared_security_contract(self):
        from source_linear_history import isolated_git_environment as guard_environment
        expected = isolated_git_environment()
        actual = guard_environment()
        for key, value in expected.items():
            if not key.startswith(('GIT_AUTHOR_', 'GIT_COMMITTER_')):
                self.assertEqual(actual[key], value, key)
        self.assertNotIn('HOME', actual)
        self.assertNotIn('PYTHONPATH', actual)

    def test_unreviewed_siblings_and_pythonpath_cannot_execute(self):
        marker = self.repo / 'executed'
        malicious = 'from pathlib import Path\nPath(' + repr(str(marker)) + ').touch()\nraise RuntimeError("unreviewed import")\n'
        (self.repo / 'tools/git_test_environment.py').write_text(malicious)
        (self.repo / 'tools/subprocess.py').write_text(malicious)
        self.env['PYTHONPATH'] = str(self.repo / 'tools')
        self.invoke(script=self.repo / 'tools/source_linear_history.py')
        self.invoke('verify', script=self.repo / 'tools/source_linear_history.py')
        self.assertFalse(marker.exists())
        self.assertEqual(set(p.name for p in self.destination.iterdir()),
                         {'source_linear_history.py', 'reference-transaction'})

    def test_exact_reviewed_installer_required(self):
        installer = self.repo / 'tools/source_linear_history.py'
        installer.write_bytes(installer.read_bytes() + b'\n# different revision\n')
        self.git('add', 'tools/source_linear_history.py')
        self.git('commit', '-m', 'different installer')
        self.sha = self.git('rev-parse', 'HEAD').stdout.strip()
        self.invoke(ok=False)
        self.assertFalse((self.repo / '.git/crewbook-source-guards').exists())

    def test_symlink_destination_refused(self):
        parent = self.repo / '.git/crewbook-source-guards'
        parent.symlink_to(self.repo / 'tools', target_is_directory=True)
        self.invoke(ok=False)
        self.assertTrue(parent.is_symlink())


if __name__ == '__main__':
    unittest.main()
