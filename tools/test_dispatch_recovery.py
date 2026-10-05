"""Offline structured recovery replay, not an agent scheduler or prompt parser."""
import copy
import unittest


def replay(state, events):
    """Reference scenario model: inputs and observable actions stay credential-free."""
    state = copy.deepcopy(state)
    actions = []
    for event in events:
        key = event['task']
        task = state['tasks'][key]
        if event['id'] in state['seen']:
            continue
        state['seen'].append(event['id'])
        kind = event['kind']
        if kind == 'handback':
            if event['owner'] != task['owner']:
                actions.append(('ownership_conflict', key))
                continue
            state['empty_requested'] = False
            task['evidence'] = event['revision']
            task['phase'] = 'review_pending'
            actions.append(('preserve', key))
            state['completed'].append(task['thread'])
        elif kind == 'review':
            if task['phase'] != 'in_review':
                actions.append(('unexpected_review', key))
                continue
            state['reviews'] -= 1
            actions.append(('release_review', key))
            valid = (event['revision'] == task['evidence']
                     and event['reviewer'] != task['owner']
                     and event['model'] == task['review_model']
                     and not event['findings'])
            task['phase'] = 'approved' if valid else 'needs_attention'
            actions.append(('approved' if valid else 'hold', key))
            if valid and task['landed'] and task['checks']:
                actions.append(('board_ready', key))
        elif kind == 'failed_start':
            task['phase'] = 'retry' if event['known_absent'] else 'resolve_start'
        elif kind == 'tool':
            task['blocker'] = (event['operation'], event['context'], event['status'])
            actions.append(('record_result', key, event['status']))
            if event['status'] == 'network_denied' and event['approved_path']:
                actions.append(('approved_read', key))
        elif kind == 'stale_card':
            actions.append(('board_reconcile' if event['owner_confirmed']
                            else 'resolve_owner', key))
    # Drain all evidence before reclaiming slots and scheduling continuations.
    for thread in state['completed']:
        if thread in state['threads']:
            state['threads'].remove(thread)
            actions.append(('release', thread))
    state['completed'] = []
    for key, task in state['tasks'].items():
        if task['phase'] == 'review_pending' and state['reviews'] < 2:
            state['reviews'] += 1
            task['phase'] = 'in_review'
            actions.append(('review', key, task['evidence'], task['review_model']))
        if task['phase'] == 'retry' and len(state['threads']) < state['capacity']:
            task['phase'] = 'running'
            if task['thread'] not in state['threads']:
                state['threads'].append(task['thread'])
            actions.append(('retry_same_claim', key))
    pending = any(t['phase'] in ('running', 'in_review', 'review_pending',
                                'retry', 'resolve_start', 'needs_attention')
                  for t in state['tasks'].values())
    if pending or state['backlog']:
        state['empty_requested'] = False
    if not pending and not state['backlog'] and not state['empty_requested']:
        actions.append(('request_work',))
        state['empty_requested'] = True
    return state, actions


def fixture():
    task = dict(owner='author', thread='author-thread', phase='running',
                evidence=None, review_model=('gpt-6.1-sol', 'medium'),
                landed=True, checks=True)
    return dict(tasks={'generic': copy.deepcopy(task), 'managed': dict(task,
                owner='other-author', thread='other-thread')}, seen=[],
                threads=['author-thread', 'other-thread'], completed=[],
                reviews=0, capacity=2, backlog=False, empty_requested=False)


class RecoveryReplay(unittest.TestCase):
    def handback(self, key='generic', owner='author', revision='a' * 40):
        return dict(id=key + '-completion', kind='handback', task=key,
                    owner=owner, revision=revision)

    def test_idle_completion_and_two_independent_handbacks(self):
        initial = fixture()
        events = [self.handback(), self.handback('managed', 'other-author')]
        state, actions = replay(initial, events)
        self.assertEqual([a[1] for a in actions if a[0] == 'review'],
                         ['generic', 'managed'])
        self.assertEqual(state['threads'], [])
        self.assertEqual(len(state['seen']), 2)
        repeated, more = replay(state, events)
        self.assertEqual(repeated, state)
        self.assertEqual(more, [])
        self.assertEqual(initial['tasks']['generic']['phase'], 'running')

    def test_legacy_label_actual_substitution_and_exact_review(self):
        state, _ = replay(fixture(), [self.handback()])
        review = dict(id='review', kind='review', task='generic',
                      reviewer='independent', revision='a' * 40,
                      model=('gpt-6.1-sol', 'medium'), legacy_label='Opus', findings=[])
        result, actions = replay(state, [review])
        self.assertEqual(result['tasks']['generic']['phase'], 'approved')
        self.assertIn(('board_ready', 'generic'), actions)
        for change in ({'revision': 'b' * 40}, {'reviewer': 'author'},
                       {'findings': ['fix']}, {'model': ('other', 'low')}):
            bad = dict(review, **change)
            _, actions = replay(state, [bad])
            self.assertNotIn(('board_ready', 'generic'), actions)
        state['tasks']['generic']['landed'] = False
        _, actions = replay(state, [review])
        self.assertIn(('approved', 'generic'), actions)
        self.assertNotIn(('board_ready', 'generic'), actions)

    def test_frozen_generic_diff_and_managed_review_slot_wait(self):
        initial = fixture()
        initial['tasks']['generic']['landed'] = False
        initial['tasks']['third'] = dict(initial['tasks']['generic'],
                                          owner='third-author', thread='third-thread')
        snapshot = 'frozen-diff:sha256:' + 'c' * 64
        state, actions = replay(initial, [self.handback(revision=snapshot),
            self.handback('managed', 'other-author'),
            self.handback('third', 'third-author')])
        self.assertIn(('review', 'generic', snapshot,
                       ('gpt-6.1-sol', 'medium')), actions)
        self.assertEqual(state['tasks']['third']['phase'], 'review_pending')
        reviews = [dict(id=key + '-review', kind='review', task=key,
                        reviewer='independent-' + key, revision=revision,
                        model=('gpt-6.1-sol', 'medium'), findings=[])
                   for key, revision in [('generic', snapshot), ('managed', 'a' * 40)]]
        state, actions = replay(state, reviews)
        self.assertEqual(state['tasks']['third']['phase'], 'in_review')
        self.assertEqual(state['reviews'], 1)
        self.assertEqual(len([a for a in actions if a[0] == 'review']), 1)
        repeated, more = replay(state, reviews)
        self.assertEqual(repeated, state)
        self.assertEqual(more, [])
        third_review = dict(reviews[0], id='third-review', task='third',
                            revision='a' * 40)
        state, actions = replay(state, [third_review])
        self.assertEqual(state['reviews'], 0)
        self.assertIn(('request_work',), actions)

    def test_full_pool_failed_start_and_uncertain_start(self):
        state = fixture()
        events = [self.handback(), dict(id='failed', task='managed',
                  kind='failed_start', known_absent=True)]
        result, actions = replay(state, events)
        self.assertIn(('retry_same_claim', 'managed'), actions)
        self.assertEqual(len(result['threads']), len(set(result['threads'])))
        self.assertLess(actions.index(('release', 'author-thread')),
                        actions.index(('retry_same_claim', 'managed')))
        _, actions = replay(fixture(), [dict(events[1], known_absent=False)])
        self.assertNotIn(('retry_same_claim', 'managed'), actions)

    def test_stale_ownership_mixed_results_and_network_recovery(self):
        events = [self.handback(owner='unknown')]
        for number, status in enumerate(('expected_negative', 'network_denied',
                                         'success', 'implementation_failure')):
            events.append(dict(id=str(number), kind='tool', task='generic',
                          operation='lookup', context='sandbox', status=status,
                          approved_path=status == 'network_denied'))
        events.append(dict(id='card', kind='stale_card', task='generic',
                           owner_confirmed=False))
        state, actions = replay(fixture(), events)
        self.assertIn(('ownership_conflict', 'generic'), actions)
        self.assertIn(('resolve_owner', 'generic'), actions)
        self.assertEqual(len([a for a in actions if a[0] == 'record_result']), 4)
        self.assertIn(('approved_read', 'generic'), actions)
        self.assertNotIn(('request_work',), actions)
        self.assertIsNone(state['tasks']['generic']['evidence'])

    def test_empty_transition_once_and_blocked_backlog(self):
        state = fixture()
        state['tasks'] = {}
        _, actions = replay(dict(state, backlog=True), [])
        self.assertNotIn(('request_work',), actions)
        result, actions = replay(state, [])
        self.assertEqual(actions, [('request_work',)])
        result, actions = replay(result, [])
        self.assertEqual(actions, [])
        result, actions = replay(dict(result, backlog=True), [])
        self.assertFalse(result['empty_requested'])
        self.assertEqual(actions, [])
        result, actions = replay(dict(result, backlog=False), [])
        self.assertEqual(actions, [('request_work',)])
        _, actions = replay(result, [])
        self.assertEqual(actions, [])


if __name__ == '__main__':
    unittest.main()
