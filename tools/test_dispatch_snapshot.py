"""Offline fixture tests for dispatch_snapshot.py (no network, no forge)."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from git_test_environment import isolated_git_environment

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    'dispatch_snapshot', os.path.join(HERE, 'dispatch_snapshot.py'))
snap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snap)

ENV = isolated_git_environment()


def git(cwd, *args):
    p = subprocess.run(['git', '-C', cwd] + list(args), env=ENV, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.decode().strip()


def state(root):
    """Refs, tags, status of every worktree, and every dir/file under the test
    tree (repo, linked worktree, .git) with mtimes, sizes and contents."""
    out = [git(root, 'for-each-ref'), git(root, 'tag'),
           git(root, 'worktree', 'list'), git(root, '--no-optional-locks', 'status', '--porcelain')]
    for line in git(root, 'worktree', 'list', '--porcelain').splitlines():
        if line.startswith('worktree '):
            out.append(git(line[9:], '--no-optional-locks', 'status', '--porcelain'))
    top = os.path.dirname(root)
    for dirpath, dirs, files in sorted(os.walk(top)):
        dirs.sort()
        out.append((dirpath, os.stat(dirpath).st_mtime_ns))
        for name in sorted(files):
            full = os.path.join(dirpath, name)
            with open(full, 'rb') as handle:
                out.append((full, os.stat(full).st_mtime_ns, handle.read()))
    return out


REGISTRY = (
    'crewbook-registry: 1\nmode: split\ncoordinator: crewbook/dispatch\n'
    'target: main\nsession: s1\nupdated: 2026-01-01\n\n'
    '## task-a\nowner: author-1\nphase: in_review\nevidence: PROMPT-TEXT\n\n'
    '## other\nowner: x\nphase: working\n\nResume: wait for review\n')


BOARD = {'cards': [{'column': 'Ready', 'number': 7, 'own': True},
                   {'column': 'Ready', 'number': 3, 'own': True},
                   {'column': 'Done', 'number': 9, 'own': False},
                   {'column': 'In-Review', 'number': 5, 'own': True}]}
CI = {'runs': [{'workflow': 'ci', 'status': 'completed', 'conclusion': 'failure', 'sha': 'a' * 40, 'id': 1},
               {'workflow': 'ci', 'status': 'completed', 'conclusion': 'success', 'sha': 'b' * 40, 'id': 2},
               {'workflow': 'lint', 'status': 'in_progress', 'conclusion': None, 'sha': 'b' * 40, 'id': 5}]}


class SnapshotTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = os.path.join(self.tmp, 'repo')
        os.mkdir(self.root)
        git(self.root, 'init', '-q', '-b', 'main')
        git(self.root, 'commit', '-q', '--allow-empty', '-m', 'base')
        git(self.root, 'switch', '-q', '-c', 'feat/a')
        git(self.root, 'commit', '-q', '--allow-empty', '-m', 'COMMIT-SUBJECT-A1')
        self.sha_a = git(self.root, 'rev-parse', 'HEAD')
        git(self.root, 'switch', '-q', 'main')
        git(self.root, 'branch', 'feat/none', 'main')
        git(self.root, 'notes', '--ref', 'review', 'add', '-m',
            'SECRET-NOTE-BODY', self.sha_a)
        self.wt = os.path.join(self.tmp, 'wt-a')
        git(self.root, 'worktree', 'add', '-q', self.wt, 'feat/a')
        reg = os.path.join(self.root, '.git', 'crewbook')
        os.mkdir(reg)
        self.regpath = os.path.join(reg, 'registry.md')
        self.write_registry(REGISTRY)
        self.board = os.path.join(self.tmp, 'board.json')
        self.ci = os.path.join(self.tmp, 'ci.json')
        for p, d in ((self.board, BOARD), (self.ci, CI)):
            with open(p, 'w') as h:
                json.dump(d, h)

    def write_registry(self, text, path=None):
        with open(path or self.regpath, 'w', newline='') as h:
            h.write(text)

    def render(self, **kw):
        return snap.render(self.root, 'main', kw.get('board', self.board),
                           kw.get('ci', self.ci), None, kw.get('registry'))

    def golden(self):
        return '\n'.join([
            '[board]', 'In-Review: #5', 'Ready: #3 #7',
            '[branches]', 'feat/a ahead=1 ' + self.sha_a,
            '[notes]', 'feat/a %s review-notes=review' % self.sha_a[:12],
            '[worktrees]',
            '%s main %s owner=unknown' % (self.root, git(self.root, 'rev-parse', 'main')[:12]),
            '%s feat/a %s owner=unknown' % (self.wt, self.sha_a[:12]),
            '[ci]', 'ci completed/success ' + 'b' * 12, 'lint in_progress/- ' + 'b' * 12,
            '[registry]', 'mode=split coordinator=crewbook/dispatch target=main',
            'assignments=2 in_review=1 working=1',
            'other owner=x phase=working', 'task-a owner=author-1 phase=in_review', ''])

    def test_golden_and_deterministic(self):
        out = self.render()
        self.assertEqual(out, self.golden())
        self.assertEqual(out, self.render())
        self.assertLess(len(out.splitlines()), 80)

    def test_no_contents_or_prompt_text(self):
        out = self.render()
        for bad in ('SECRET-NOTE-BODY', 'PROMPT-TEXT', 'COMMIT-SUBJECT-A1'):
            self.assertNotIn(bad, out)

    def test_read_only(self):
        before = state(self.root)
        self.render()
        self.assertEqual(before, state(self.root))

    def test_board_and_ci_unavailable(self):
        out = self.render(board=None, ci=os.path.join(self.tmp, 'missing'))
        self.assertIn('[board]\nunavailable: no board input supplied', out)
        self.assertIn('[ci]\nunavailable: ci input unreadable: FileNotFoundError', out)
        self.assertIn('feat/a ahead=1', out)

    def test_malformed_board(self):
        with open(self.board, 'w') as h:
            h.write('{"cards": 3}')
        self.assertIn('[board]\nunavailable: board input malformed', self.render())

    def test_registry_unavailable_only_that_section(self):
        os.remove(os.path.join(self.root, '.git', 'crewbook', 'registry.md'))
        out = self.render()
        self.assertIn('[registry]\nunavailable: no registry file', out)
        self.assertIn('review-notes=review', out)

    def test_bad_main_degrades_git_sections(self):
        out = snap.render(self.root, 'nomain', self.board, self.ci)
        self.assertIn('[branches]\nunavailable:', out)
        self.assertIn('[notes]\nunavailable:', out)
        self.assertIn('Ready: #3 #7', out)

    def test_not_a_repo(self):
        out = snap.render(self.tmp, 'main', self.board, self.ci)
        self.assertIn('[branches]\nunavailable:', out)
        self.assertIn('[worktrees]\nunavailable:', out)
        self.assertIn('[registry]\nunavailable:', out)
        self.assertIn('Ready: #3 #7', out)

    def test_unsafe_token_masked(self):
        data = {'cards': [{'column': 'Bad col\nIgnore previous', 'number': 1, 'own': True}]}
        with open(self.board, 'w') as h:
            json.dump(data, h)
        out = self.render()
        self.assertNotIn('Ignore', out)
        self.assertIn('[board]\nunavailable: board label unsupported', out)

    def test_distinct_unsupported_labels_do_not_merge(self):
        with open(self.board, 'w') as h:
            json.dump({'cards': [
                {'column': 'In review', 'number': 1, 'own': True},
                {'column': 'Ready to push', 'number': 2, 'own': True}]}, h)
        with open(self.ci, 'w') as h:
            json.dump({'runs': [
                {'workflow': 'Package checks', 'status': 'completed',
                 'conclusion': 'failure', 'sha': 'a' * 40, 'id': 1},
                {'workflow': 'Secret scan', 'status': 'completed',
                 'conclusion': 'success', 'sha': 'b' * 40, 'id': 2}]}, h)
        out = self.render()
        self.assertIn('[board]\nunavailable: board label unsupported', out)
        self.assertIn('[ci]\nunavailable: ci label unsupported', out)
        self.assertNotIn('? completed/success', out)

    def test_untouched_note_absent(self):
        git(self.root, 'notes', '--ref', 'review', 'remove', self.sha_a)
        self.assertIn('review-notes=none', self.render())

    def test_registry_damaged_or_foreign(self):
        good = REGISTRY
        cases = {
            'list-style owner': good.replace('owner: author-1', '- owner: author-1'),
            'disallowed key': good.replace('phase: working', 'note: working'),
            'missing session': good.replace('session: s1\n', ''),
            'missing resume': good.replace('Resume: wait for review\n', ''),
            'text after resume': good + 'owner: x\n',
            'duplicate key': good.replace('owner: x\n', 'owner: x\nowner: y\n'),
            'blank-line spaces': good.replace('\n\n## other', '\n \n## other'),
            'non-ascii': good.replace('author-1', 'author-\u00fc'),
            'blocks only': '## task-a\nowner: x\n\nResume: r\n',
        }
        for label, text in cases.items():
            self.write_registry(text)
            out = self.render()
            self.assertIn('[registry]\nunavailable: damaged or foreign\n', out, label)
            self.assertNotIn('assignments=', out, label)
            self.assertIn('feat/a ahead=1', out, label)

    def test_registry_crlf_valid_and_owner_only_from_key(self):
        self.write_registry(REGISTRY.replace('\n', '\r\n'))
        out = self.render()
        self.assertIn('task-a owner=author-1 phase=in_review', out)
        # the branch feat/a is not an assignment name: no branch-name mapping
        self.assertNotIn('owner=author-1', out.split('[worktrees]')[1].split('[ci]')[0])

    def test_worktree_owner_unknown_without_exact_association(self):
        out = self.render()
        section = out.split('[worktrees]\n')[1].split('[ci]')[0]
        self.assertIn(self.wt + ' feat/a ' + self.sha_a[:12] + ' owner=unknown', section)
        self.assertNotIn('author-1', section)
        self.assertNotIn('PROMPT-TEXT', section)

    def test_registry_path_option_wins(self):
        other = os.path.join(self.tmp, 'other-registry.md')
        self.write_registry(REGISTRY.replace('owner: x', 'owner: zed'), other)
        out = self.render(registry=other)
        self.assertIn('other owner=zed phase=working', out)
        self.write_registry('garbage', other)
        self.assertIn('[registry]\nunavailable: damaged or foreign', self.render(registry=other))
        self.assertIn('other owner=x', self.render())

    def test_registry_blank_is_no_registry(self):
        self.write_registry(' \t\r\n\n')
        self.assertIn('[registry]\nunavailable: no registry file', self.render())

    def test_global_budget_with_every_section_populated(self):
        lines = ['entry-%03d' % i for i in range(100)]
        with contextlib.ExitStack() as stack:
            for name in ('board', 'notes', 'worktrees', 'ci', 'registry'):
                stack.enter_context(mock.patch.object(snap, name, return_value=lines))
            stack.enter_context(mock.patch.object(snap, 'branches',
                                                   return_value=([], lines)))
            out = snap.render(self.root, 'main', self.board, self.ci, 'stamp')
        self.assertLess(len(out.splitlines()), 80)
        for name in ('board', 'branches', 'notes', 'worktrees', 'ci', 'registry'):
            self.assertIn('[' + name + ']', out)
        self.assertEqual(out.count('... 89 more'), 6)

    def test_cap_prints_more_line(self):
        for i in range(49):
            git(self.root, 'branch', 'many/b%02d' % i)
            git(self.root, 'switch', '-q', 'many/b%02d' % i)
            git(self.root, 'commit', '-q', '--allow-empty', '-m', 'm%d' % i)
            git(self.root, 'switch', '-q', 'main')
        out = self.render()
        sec = out.split('[branches]\n')[1].split('\n[notes]')[0].split('\n')
        self.assertEqual(len(sec), 12)
        self.assertEqual(sec[-1], '... 39 more')
        nsec = out.split('[notes]\n')[1].split('\n[worktrees]')[0].split('\n')
        self.assertEqual(nsec[-1], '... 39 more')

    def test_only_review_notes_ref(self):
        git(self.root, 'notes', '--ref', 'review', 'remove', self.sha_a)
        git(self.root, 'notes', '--ref', 'other', 'add', '-m', 'y', self.sha_a)
        self.assertIn('review-notes=none', self.render())

    def test_own_must_be_true_boolean(self):
        data = {'cards': [{'column': 'Ready', 'number': 1, 'own': 'false'},
                          {'column': 'Ready', 'number': 2, 'own': 1},
                          {'column': 'Ready', 'number': 3, 'own': True}]}
        with open(self.board, 'w') as h:
            json.dump(data, h)
        self.assertIn('[board]\nReady: #3\n', self.render())

    def test_card_numbers_are_strict_positive_integers(self):
        for number in (1.9, True, False, 0, -1, '1', None):
            with self.subTest(number=number):
                with open(self.board, 'w') as h:
                    json.dump({'cards': [
                        {'column': 'Ready', 'number': number, 'own': True}]}, h)
                out = self.render()
                self.assertIn('[board]\nunavailable: board input malformed', out)
                self.assertNotIn('Ready: #', out)

    def test_bare_repo_label(self):
        bare = os.path.join(self.tmp, 'bare.git')
        git(self.tmp, 'clone', '-q', '--bare', self.root, bare)
        out = snap.render(bare, 'main', self.board, self.ci)
        self.assertIn(bare + ' bare ', out)

    def test_cli_stamp_and_stdin_conflict(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            snap.main(['--root', self.root, '--board', self.board, '--stamp', '2026-01-01T00:00Z'])
        self.assertTrue(buf.getvalue().startswith('generated: 2026-01-01T00:00Z\n'))
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                snap.main(['--root', self.root, '--board', '-', '--ci', '-'])


if __name__ == '__main__':
    unittest.main()
