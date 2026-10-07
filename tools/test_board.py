"""Offline tests for board.py with a fake gh (no network)."""
import contextlib
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    'board', os.path.join(HERE, 'board.py'))
board = importlib.util.module_from_spec(spec)
spec.loader.exec_module(board)

OPTIONS = ['Todo', 'In progress', 'In review', 'Ready to push', 'Blocked',
           'Done']


class FakeGh:
    """Answers the two GraphQL calls of board.py from an in-memory project."""

    def __init__(self, cards, drop_writes=False):
        # cards: {number: [status, issue state]}
        self.cards = cards
        self.drop_writes = drop_writes
        self.writes = []

    def __call__(self, args):
        import json
        query = args[3]
        vars_ = dict(a.split('=', 1) for a in args[4:] if '=' in a)
        if 'mutation' in query:
            item = vars_['i']
            name = [n for n in OPTIONS if 'opt-' + n == vars_['o']][0]
            self.writes.append((item, name))
            if not self.drop_writes:
                self.cards[int(item[5:])][0] = name
            return json.dumps({'data': {}})
        nodes = [{'id': 'item-%d' % n,
                  'status': {'name': s} if s else None,
                  'content': {'number': n, 'state': st,
                              'repository': {'nameWithOwner': board.REPO}}}
                 for n, (s, st) in sorted(self.cards.items())]
        nodes.append({'id': 'item-x', 'status': None,
                      'content': {'number': 1, 'state': 'OPEN',
                                  'repository': {'nameWithOwner': 'o/other'}}})
        return json.dumps({'data': {'node': {
            'field': {'id': 'F', 'options': [
                {'id': 'opt-' + n, 'name': n} for n in OPTIONS]},
            'items': {'pageInfo': {'hasNextPage': False, 'endCursor': None},
                      'nodes': nodes}}}})


class MoveTests(unittest.TestCase):
    def run_move(self, fake, number, status):
        with mock.patch.object(board, 'run_gh', fake):
            return board.move(number, status)

    def test_moves_one_card_and_reads_back(self):
        fake = FakeGh({5: ['Todo', 'OPEN'], 6: ['Todo', 'OPEN']})
        self.assertEqual(self.run_move(fake, 5, 'In progress'), 'Todo')
        self.assertEqual(fake.writes, [('item-5', 'In progress')])
        self.assertEqual(fake.cards[6][0], 'Todo')

    def test_idempotent(self):
        fake = FakeGh({5: ['In review', 'OPEN']})
        self.assertEqual(self.run_move(fake, 5, 'In review'), 'In review')
        self.assertEqual(fake.writes, [])

    def test_read_back_mismatch_fails(self):
        fake = FakeGh({5: ['Todo', 'OPEN']}, drop_writes=True)
        with self.assertRaisesRegex(board.BoardError, 'read-back mismatch'):
            self.run_move(fake, 5, 'Blocked')

    def test_done_refused_without_writing(self):
        fake = FakeGh({5: ['Todo', 'OPEN']})
        with self.assertRaisesRegex(board.BoardError, 'Done'):
            self.run_move(fake, 5, 'Done')
        self.assertEqual(fake.writes, [])

    def test_unknown_status_and_missing_card(self):
        fake = FakeGh({5: ['Todo', 'OPEN']})
        with self.assertRaises(board.BoardError):
            self.run_move(fake, 5, 'Nope')
        with self.assertRaises(board.BoardError):
            self.run_move(fake, 9, 'Todo')

    def test_cli_exit_codes(self):
        fake = FakeGh({5: ['Todo', 'OPEN']}, drop_writes=True)
        with mock.patch.object(board, 'run_gh', fake), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(board.main(['move', '5', 'Blocked']), 1)
            self.assertEqual(board.main(['move', '5', 'Done']), 1)
            self.assertEqual(board.main(['move', '5', 'Todo']), 0)


REGISTRY = """crewbook-registry: 1
session: s1

## 10-first
phase: blocked

## #11
phase: start requested

## 12
phase: blocked

## 13
phase: done

## 22
phase: start requested

## no-issue-number
phase: blocked

Resume: summary
- free-form log line after Resume: not part of the grammar
"""


class SyncTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = os.path.join(tmp.name, 'repo')
        env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null',
                   GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@e',
                   GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@e')
        for cmd in (['init', '-q', self.root],
                    ['-C', self.root, 'commit', '-q', '--allow-empty', '-m', 'x'],
                    ['-C', self.root, 'worktree', 'add', '-q', '-b',
                     'feat/14-thing', os.path.join(tmp.name, 'wt')]):
            subprocess.run(['git'] + cmd, env=env, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.registry = os.path.join(tmp.name, 'registry.md')
        with open(self.registry, 'w') as handle:
            handle.write(REGISTRY)

    def cards(self):
        return {10: ['In review', 'OPEN'], 11: ['Todo', 'OPEN'],
                12: ['Blocked', 'OPEN'], 13: ['In progress', 'OPEN'],
                14: ['Todo', 'OPEN'], 15: ['Ready to push', 'OPEN'],
                16: ['Done', 'OPEN'], 17: ['In review', 'CLOSED'],
                18: ['In review', 'OPEN'], 20: ['Blocked', 'OPEN'],
                21: [None, 'OPEN'], 22: ['Ready to push', 'OPEN']}

    def run_sync(self, fake, dry_run=False):
        with mock.patch.object(board, 'run_gh', fake):
            return board.sync(self.root, dry_run, self.registry)

    def test_diff_and_idempotent(self):
        fake = FakeGh(self.cards())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            lines = self.run_sync(fake)
        self.assertEqual(lines, [
            '#10 In review -> Blocked (registry phase blocked)',
            '#11 Todo -> In progress (registry phase start requested)',
            '#13 In progress -> Todo (no worktree or registry signal)',
            '#14 Todo -> In progress (worktree branch)'])
        self.assertEqual(out.getvalue(), '\n'.join(lines) + '\n')
        self.assertEqual(len(fake.writes), 4)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.run_sync(fake), [])
        self.assertEqual(len(fake.writes), 4)

    def test_never_lowers_without_evidence(self):
        fake = FakeGh(self.cards())
        with contextlib.redirect_stdout(io.StringIO()):
            self.run_sync(fake)
        self.assertEqual(fake.cards[12][0], 'Blocked')
        self.assertEqual(fake.cards[15][0], 'Ready to push')
        self.assertEqual(fake.cards[18][0], 'In review')
        self.assertEqual(fake.cards[20][0], 'Blocked')
        self.assertIsNone(fake.cards[21][0])
        self.assertEqual(fake.cards[22][0], 'Ready to push')
        self.assertEqual(fake.cards[16][0], 'Done')
        self.assertEqual(fake.cards[17][0], 'In review')

    def test_missing_status_rendered(self):
        fake = FakeGh({14: [None, 'OPEN']})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.run_sync(fake), [
                '#14 (none) -> In progress (worktree branch)'])

    def test_dry_run_writes_nothing(self):
        fake = FakeGh(self.cards())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(len(self.run_sync(fake, dry_run=True)), 4)
        self.assertEqual(fake.writes, [])

    def test_missing_registry_changes_nothing(self):
        fake = FakeGh(self.cards())
        os.remove(self.registry)
        with self.assertRaises(board.BoardError):
            self.run_sync(fake)
        self.assertEqual(fake.writes, [])

    def test_cli_prints_diff(self):
        fake = FakeGh({11: ['Todo', 'OPEN']})
        out = io.StringIO()
        with mock.patch.object(board, 'run_gh', fake), \
                contextlib.redirect_stdout(out):
            code = board.main(['sync', '--dry-run', '--root', self.root,
                               '--registry', self.registry])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(),
                         '#11 Todo -> In progress (registry phase start requested)\n')


if __name__ == '__main__':
    unittest.main()
