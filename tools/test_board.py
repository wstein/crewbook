"""Offline tests for board.py with a fake gh (no network)."""
import contextlib
import importlib.util
import io
import os
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


if __name__ == '__main__':
    unittest.main()
