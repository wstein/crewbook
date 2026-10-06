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
            if key in state.get('pending_handbacks', []):
                state['pending_handbacks'].remove(key)
            if (task.get('landing_required')
                    and event['revision'] != task['evidence']):
                task['landed'] = False
                task.pop('cleared_revision', None)
                task.pop('landing_request', None)
                task.pop('integration_result', None)
            task['evidence'] = event['revision']
            task['phase'] = 'review_pending'
            actions.append(('preserve', key))
            state['completed'].append(task['thread'])
        elif kind == 'review':
            if task['phase'] != 'in_review':
                actions.append(('unexpected_review', key))
                continue
            state['reviews'] -= 1
            actions.append(('preserve_review', key))
            valid = (event['revision'] == task['evidence']
                     and event['reviewer'] != task['owner']
                     and event['model'] == task['review_model']
                     and not event['findings'])
            task['review_continuation'] = (event['revision'] == task['evidence']
                     and event['reviewer'] != task['owner']
                     and event['model'] == task['review_model']
                     and bool(event['findings']))
            task['phase'] = 'approved' if valid else 'needs_attention'
            actions.append(('approved' if valid else 'hold', key))
            if valid:
                task['cleared_revision'] = event['revision']
            if valid and task['landed'] and task['checks']:
                actions.append(('board_ready', key))
        elif kind == 'landing_result':
            valid = (task['phase'] == 'approved'
                     and task.get('landing_required') and task.get('landing_authorized')
                     and task.get('landing_request') == task.get('cleared_revision')
                     and event.get('owner') == task['owner']
                     and event.get('revision') == task.get('cleared_revision')
                     and event.get('revision') == task['evidence']
                     and task.get('integration_ref')
                     and event.get('integration_ref') == task['integration_ref']
                     and event.get('result') == 'success' and task['checks'])
            actions.append(('preserve_landing_result', key))
            if valid:
                task['integration_result'] = copy.deepcopy(event)
                task['landed'] = True
                actions.append(('board_ready', key))
            else:
                actions.append(('hold_landing', key))
        elif kind == 'route_fix':
            if task['phase'] == 'needs_attention' and event['owner'] == task['owner']:
                task['phase'] = 'running'
                if task['thread'] not in state['threads']:
                    state['threads'].append(task['thread'])
                actions.append(('resume_author_same', key, task['owner']))
            else:
                actions.append(('ownership_conflict', key))
        elif kind == 'failed_start':
            task['phase'] = 'retry' if event['known_absent'] else 'resolve_start'
            task['retry_after'] = state['host_capacity']['generation']
        elif kind == 'host_capacity':
            state['host_capacity'] = dict(available=event['available'],
                                           generation=event['generation'])
        elif kind == 'tool':
            task['blocker'] = (event['operation'], event['context'], event['status'])
            actions.append(('record_result', key, event['status']))
            if event['status'] == 'network_denied' and event['approved_path']:
                actions.append(('approved_read', key))
        elif kind == 'stale_card':
            actions.append(('board_reconcile' if event['owner_confirmed']
                            else 'resolve_owner', key))
    # Handback preservation does not close a handle or establish host capacity.
    state['completed'] = []
    for key, task in state['tasks'].items():
        if (task['phase'] == 'review_pending' and state['reviews'] < 2
                and (task.get('review_continuation') or
                     state['host_capacity']['available'] > 0)):
            state['reviews'] += 1
            continuation = task.get('review_continuation', False)
            if not continuation:
                state['host_capacity']['available'] -= 1
                task['review_starts'] = task.get('review_starts', 0) + 1
                task['review_thread'] = 'review-{}-{}'.format(key, task['review_starts'])
            task['phase'] = 'in_review'
            actions.append(('resume_review_same' if continuation else 'review',
                            key, task['evidence'], task['review_model']))
        if (task['phase'] == 'retry' and state['host_capacity']['available'] > 0
                and state['host_capacity']['generation'] > task['retry_after']):
            task['phase'] = 'running'
            state['host_capacity']['available'] -= 1
            if task['thread'] not in state['threads']:
                state['threads'].append(task['thread'])
            actions.append(('retry_same_claim', key))
        if (task['phase'] == 'approved' and task.get('landing_required')
                and not task['landed'] and task.get('landing_authorized')
                and task.get('integration_ref') and task['checks']
                and task.get('landing_request') != task.get('cleared_revision')):
            # Sending this request proves neither start nor successful integration.
            task['landing_request'] = task['cleared_revision']
            actions.append(('resume_landing_same', key, task['owner'],
                            task['thread'], task['cleared_revision']))
    pending = any(t['phase'] in ('running', 'in_review', 'review_pending',
                                'retry', 'resolve_start', 'needs_attention')
                  for t in state['tasks'].values())
    pending = pending or drain_gate(state)[0] != 'drained'
    if pending or state['backlog']:
        state['empty_requested'] = False
    if not pending and not state['backlog'] and not state['empty_requested']:
        actions.append(('request_work',))
        state['empty_requested'] = True
    return state, actions


def drain_gate(state):
    """Classify explicit scenario obligations, never assume empty means complete."""
    phases = {'running', 'in_review', 'review_pending', 'retry',
              'resolve_start', 'needs_attention', 'queued', 'integration',
              'status_write', 'handback_pending'}
    obligations = [(key, task['phase']) for key, task in state['tasks'].items()
                   if task['phase'] in phases or task['phase'] not in
                   ('approved', 'done', 'blocked')]
    obligations.extend((key, 'landing_result' if task.get('landing_request')
                        else 'required_landing')
                       for key, task in state['tasks'].items()
                       if task['phase'] == 'approved' and task.get('landing_required')
                       and not task.get('landed'))
    for queue in ('eligible_queue', 'pending_handbacks', 'fixes',
                  'required_reviews', 'integration', 'status_writes'):
        obligations.extend((queue, item) for item in state.get(queue, []))
    if state['reviews']:
        obligations.append(('review_slots', state['reviews']))
    obligations.extend(('unpreserved_handback', thread)
                       for thread in state['completed'])
    if state['backlog']:
        obligations.append(('backlog', 'classify queued work'))
    blocked = [(key, task.get('blocker'), task.get('next_action'))
               for key, task in state['tasks'].items() if task['phase'] == 'blocked']
    # Missing unblock evidence is unresolved work, not a concrete external stop.
    obligations.extend((key, 'resolve blocker') for key, blocker, action in blocked
                       if not blocker or not action)
    if obligations:
        return 'active', obligations
    if blocked:
        return 'blocked', blocked
    return 'drained', []


def parent_continuation(state, handles, wait_available=True):
    """Observable parent action for a supplied snapshot, without tool execution."""
    outcome, obligations = drain_gate(state)
    if outcome != 'active':
        return outcome, obligations
    actionable = [(key, artifact) for key, artifact in obligations
                  if artifact not in ('running', 'in_review', 'landing_result')
                  and key != 'review_slots'
                  and not (artifact == 'review_pending' and
                           (state['reviews'] >= 2 or
                            (state['host_capacity']['available'] == 0 and
                             not state['tasks'][key].get('review_continuation'))))
                  and not (artifact == 'retry' and
                           (state['host_capacity']['available'] == 0 or
                            state['host_capacity']['generation'] <=
                            state['tasks'][key]['retry_after']))]
    if actionable:
        return ('process', actionable)
    awaited = []
    for key, task in state['tasks'].items():
        phase = task['phase']
        if (phase == 'approved' and task.get('landing_required')
                and not task.get('landed') and task.get('landing_request')):
            awaited.append((key, task['thread'], 'landing_result'))
        if phase in ('running', 'in_review', 'review_pending', 'retry'):
            artifact = {'in_review': 'review', 'review_pending': 'review_slot',
                        'running': 'author_handback', 'retry': 'host_capacity'}[phase]
            if (phase == 'review_pending' and state['host_capacity']['available'] == 0
                    and not task.get('review_continuation')):
                artifact = 'host_capacity'
            awaited.append((key, handles.get(key), artifact))
    if awaited:
        return ('await' if wait_available else 'handoff', awaited)
    outcome, obligations = drain_gate(state)
    return ('process' if outcome == 'active' else outcome, obligations)


def desk_safety_net(state, dispatcher, unexpected_yield, resume_available=True,
                    mode='split'):
    """Desk's dispatcher-resume safety net exists only in split mode."""
    if mode != 'split':
        return ('not_applicable', None, [])
    outcome, obligations = drain_gate(state)
    if unexpected_yield and outcome == 'active':
        return ('resume_same' if dispatcher and resume_available else 'handoff',
                dispatcher, obligations)
    return (outcome, dispatcher, obligations)


def select_mode(policy, override=None):
    """Merged by default; split only for a usable gate configuration."""
    writer = policy.get('authorized_writer')
    gate = bool((policy.get('board_destination') and policy.get('status_mapping')
                 and writer) or policy.get('external_claim_required'))
    if override == 'separate_dispatcher':
        return 'split'
    if override == 'coordinate_yourself':
        return 'conflict' if gate and writer == 'dispatcher' else 'merged'
    return 'split' if gate else 'merged'


def start_dispatcher(state, mode):
    if mode != 'split':
        raise ValueError('dispatcher start is split-only')
    state.setdefault('dispatcher_starts', 0)
    state['dispatcher_starts'] += 1
    return state


def lifecycle_trace(mode):
    """Count starts for desk -> author -> review; merged has no dispatcher."""
    state = fixture()
    state['tasks'] = {'generic': state['tasks']['generic']}
    state['threads'] = ['author-thread']  # the one author start by the coordinator
    starters = {'crewbook/desk'}
    if mode == 'split':
        start_dispatcher(state, mode)
        starters.add('crewbook/dispatch')
    state, _ = replay(state, [dict(id='done', kind='handback', task='generic',
                                   owner='author', revision='a' * 40)])
    task = state['tasks']['generic']
    return dict(dispatcher_starts=state.get('dispatcher_starts', 0),
                author_starts=len(state['threads']),
                review_starts=task.get('review_starts', 0),
                phase=task['phase'], starters=starters)


def board_operations(policy, mode):
    """A configured but unavailable gate selects split and blocks board writes."""
    configured = bool(policy.get('board_destination') and policy.get('status_mapping')
                      and policy.get('authorized_writer'))
    if not configured:
        return 'none'
    return 'available' if policy.get('gate_available', True) else 'blocked'


def registry_writer(mode, header_written, actor):
    """Split: desk writes only the header/start record, then the dispatcher alone."""
    if mode == 'merged':
        return 'desk' if actor == 'desk' else None
    if actor == 'desk':
        return None if header_written else 'desk'
    return 'dispatcher' if actor == 'dispatcher' else None


def second_desk_action(reg, session):
    """A second desk reads an active record from another session, never writes."""
    foreign = [k for k, f in reg['tasks'].items()
               if f.get('handle_session') != session
               and f.get('phase') not in ('done', 'blocked')]
    return ('read_only', 'ask_human') if foreign else ('write', None)


def slot_count(mode, authors, reviewers, design, helpers):
    return authors + reviewers + design + helpers + (1 if mode == 'split' else 0)


REGISTRY_FIELDS = ('owner', 'handle', 'handle_session', 'phase', 'evidence',
                   'landing_required', 'landing_authorized', 'next_awaited')


FORBIDDEN_FIELDS = ('token', 'password', 'credential', 'secret', 'body',
                    'transcript', 'env')


def registry_dump(state, mode, session, updated, target='target'):
    """Keyed plain text; handles are valid only in their creating session."""
    lines = ['crewbook-registry: 1', 'mode: ' + mode,
             'coordinator: ' + ('crewbook/desk' if mode == 'merged'
                                else 'crewbook/dispatch'),
             'target: ' + target, 'updated: ' + updated, '']
    for key, task in state['tasks'].items():
        for field, value in task.items():
            if (any(f in field.lower() for f in FORBIDDEN_FIELDS)
                    or (isinstance(value, str) and value.startswith('ghp_'))):
                raise ValueError('refusing to serialize ' + field)
        lines.append('## ' + key)
        values = dict(owner=task['owner'], handle=task['thread'],
                      handle_session=session, phase=task['phase'],
                      evidence=task.get('evidence') or '',
                      landing_required=bool(task.get('landing_required')),
                      landing_authorized=bool(task.get('landing_authorized')),
                      next_awaited='author_handback' if task['phase'] == 'running'
                      else task['phase'])
        lines.extend('{}: {}'.format(f, values[f]) for f in REGISTRY_FIELDS)
        lines.append('')
    lines.append('Resume: drain completions, then await named artifacts.')
    return '\n'.join(lines) + '\n'


def registry_load(text, session):
    reg = dict(tasks={}, session=session)
    current = None
    for line in text.splitlines():
        if line.startswith('## '):
            current = reg['tasks'].setdefault(line[3:], {})
        elif ': ' in line and not line.startswith('Resume:'):
            name, value = line.split(': ', 1)
            (current if current is not None else reg)[name] = value
    return reg


def registry_state(reg, base):
    state = copy.deepcopy(base)
    for key, fields in reg['tasks'].items():
        task = state['tasks'][key]
        task['phase'] = fields['phase']
        task['landing_required'] = fields['landing_required'] == 'True'
        task['landing_authorized'] = fields['landing_authorized'] == 'True'
    return state


def registry_resume(reg, session):
    """Stale handles resolve ownership; they never trigger a fresh start."""
    actions = []
    for key, fields in reg['tasks'].items():
        if fields['phase'] in ('done', 'blocked'):
            continue
        if fields['handle_session'] == session:
            actions.append(('await', key, fields['handle']))
        else:
            actions.append(('resolve_owner', key))
    return actions


def merged_desk_turn(state, handles, wait_available, completion_reenters=False):
    """Desk as coordinator: never ends with obligations without a registry."""
    action, awaited = parent_continuation(state, handles, wait_available)
    if action == 'handoff':
        # Only observed re-entry counts; documentation alone does not.
        if completion_reenters == 'observed':
            return ('end_relying_on_reentry', awaited, 'write_registry')
        return ('handoff', awaited, 'write_registry')
    return (action, awaited, None)


def user_steering(state, ordered_tasks):
    state = copy.deepcopy(state)
    state['eligible_queue'] = list(ordered_tasks)
    state['empty_requested'] = False
    return state, ('route_queue', tuple(ordered_tasks))


def fixture():
    task = dict(owner='author', thread='author-thread', phase='running',
                evidence=None, review_model=('gpt-6.1-sol', 'medium'),
                landed=True, checks=True)
    return dict(tasks={'generic': copy.deepcopy(task), 'managed': dict(task,
                owner='other-author', thread='other-thread')}, seen=[],
                threads=['author-thread', 'other-thread'], completed=[],
                reviews=0, host_capacity=dict(available=2, generation=1),
                backlog=False, empty_requested=False)


class RecoveryReplay(unittest.TestCase):
    def handback(self, key='generic', owner='author', revision='a' * 40):
        return dict(id=key + '-completion', kind='handback', task=key,
                    owner=owner, revision=revision)

    def test_clean_review_retains_required_landing_without_seeded_queue(self):
        initial = fixture()
        initial['tasks'] = {'generic': initial['tasks']['generic']}
        initial['tasks']['generic'].update(landed=False, landing_required=True,
            landing_authorized=True, integration_ref='refs/heads/main')
        state, _ = replay(initial, [self.handback()])
        review = dict(id='clean', kind='review', task='generic',
                      reviewer='independent', revision='a' * 40,
                      model=('gpt-6.1-sol', 'medium'), findings=[])
        state, actions = replay(state, [review])
        self.assertEqual(drain_gate(state)[0], 'active')
        self.assertNotIn(('request_work',), actions)
        self.assertIn(('resume_landing_same', 'generic', 'author',
                       'author-thread', 'a' * 40), actions)
        self.assertFalse(state['tasks']['generic']['landed'])
        self.assertEqual(parent_continuation(state, {'generic': 'author-thread'}),
                         ('await', [('generic', 'author-thread', 'landing_result')]))
        self.assertEqual(desk_safety_net(state, 'dispatcher', True, mode='split')[0], 'resume_same')
        repeated, actions = replay(state, [])
        self.assertEqual(repeated, state)
        self.assertEqual(actions, [])

    def approved_candidate(self, required=True, authorized=True):
        initial = fixture()
        initial['tasks'] = {'generic': initial['tasks']['generic']}
        initial['tasks']['generic'].update(landed=False, landing_required=required,
            landing_authorized=authorized, integration_ref='refs/heads/main')
        state, _ = replay(initial, [self.handback()])
        return replay(state, [dict(id='clean', kind='review', task='generic',
            reviewer='independent', revision='a' * 40,
            model=('gpt-6.1-sol', 'medium'), findings=[])])

    def test_landing_requires_owner_cleared_revision_ref_and_success(self):
        state, _ = self.approved_candidate()
        result = dict(id='landed', kind='landing_result', task='generic',
            owner='author', revision='a' * 40, integration_ref='refs/heads/main',
            result='success')
        for change in ({'owner': 'other'}, {'revision': 'b' * 40},
                       {'integration_ref': 'refs/heads/other'},
                       {'integration_ref': None}, {'result': None}, {'result': 'failure'},
                       {'result': 'unknown'}):
            with self.subTest(change=change):
                pending, actions = replay(state, [dict(result, **change)])
                self.assertFalse(pending['tasks']['generic']['landed'])
                self.assertEqual(drain_gate(pending)[0], 'active')
                self.assertNotIn(('board_ready', 'generic'), actions)
                self.assertNotIn(('request_work',), actions)
        landed, actions = replay(state, [result])
        self.assertEqual(drain_gate(landed), ('drained', []))
        self.assertEqual(landed['tasks']['generic']['integration_result'], result)
        self.assertIn(('board_ready', 'generic'), actions)
        self.assertIn(('request_work',), actions)
        self.assertEqual(replay(landed, [result]), (landed, []))

    def test_same_revision_handback_preserves_unresolved_landing_request(self):
        state, _ = self.approved_candidate()
        handback = dict(self.handback(), id='same-revision-handback')
        state, _ = replay(state, [handback])
        state, actions = replay(state, [dict(id='same-revision-review', kind='review',
            task='generic', reviewer='independent', revision='a' * 40,
            model=('gpt-6.1-sol', 'medium'), findings=[])])
        self.assertFalse(any(a[0] == 'resume_landing_same' for a in actions))
        self.assertEqual(state['tasks']['generic']['landing_request'], 'a' * 40)
        self.assertEqual(parent_continuation(state, {}),
                         ('await', [('generic', 'author-thread', 'landing_result')]))
        result = dict(id='landed-after-repeat', kind='landing_result', task='generic',
            owner='author', revision='a' * 40, integration_ref='refs/heads/main',
            result='success')
        state, _ = replay(state, [result])
        state, _ = replay(state, [dict(handback, id='same-landed-handback')])
        self.assertTrue(state['tasks']['generic']['landed'])
        self.assertEqual(state['tasks']['generic']['integration_result'], result)

    def test_rewritten_candidate_invalidates_old_landing_clearance(self):
        state, _ = self.approved_candidate()
        state, _ = replay(state, [dict(self.handback(revision='b' * 40),
                                      id='new-candidate')])
        result = dict(id='stale-landing', kind='landing_result', task='generic',
            owner='author', revision='a' * 40, integration_ref='refs/heads/main',
            result='success')
        pending, actions = replay(state, [result])
        self.assertFalse(pending['tasks']['generic']['landed'])
        self.assertNotIn(('board_ready', 'generic'), actions)
        self.assertEqual(pending['tasks']['generic']['phase'], 'in_review')
        pending, actions = replay(pending, [dict(id='new-review', kind='review',
            task='generic', reviewer='independent', revision='b' * 40,
            model=('gpt-6.1-sol', 'medium'), findings=[])])
        self.assertIn(('resume_landing_same', 'generic', 'author',
                       'author-thread', 'b' * 40), actions)

    def test_review_only_finishes_and_required_unauthorized_landing_stays_pending(self):
        state, actions = self.approved_candidate(required=False)
        self.assertEqual(drain_gate(state), ('drained', []))
        self.assertIn(('request_work',), actions)
        self.assertFalse(any(a[0] == 'resume_landing_same' for a in actions))
        state, actions = self.approved_candidate(authorized=False)
        self.assertEqual(drain_gate(state)[0], 'active')
        self.assertEqual(parent_continuation(state, {})[0], 'process')
        self.assertFalse(any(a[0] == 'resume_landing_same' for a in actions))
        self.assertNotIn(('request_work',), actions)

    def test_completed_occupied_host_without_release_defers_fresh_review(self):
        initial = fixture()
        initial['host_capacity'] = dict(available=0, generation=1)
        state, actions = replay(initial, [self.handback()])
        self.assertEqual(state['tasks']['generic']['phase'], 'review_pending')
        self.assertIn('author-thread', state['threads'])
        self.assertNotIn(('release', 'author-thread'), actions)
        self.assertFalse(any(a[0] == 'review' for a in actions))
        repeated, actions = replay(state, [])
        self.assertEqual(repeated, state)
        self.assertEqual(actions, [])

    def test_confirmed_inactive_host_allows_fresh_review_without_close(self):
        initial = fixture()
        initial['host_capacity'] = dict(available=1, generation=2)
        state, actions = replay(initial, [self.handback()])
        self.assertIn('author-thread', state['threads'])
        self.assertNotIn(('release', 'author-thread'), actions)
        self.assertEqual(state['tasks']['generic']['phase'], 'in_review')
        self.assertEqual(len([a for a in actions if a[0] == 'review']), 1)

    def test_finding_corrections_resume_same_review_without_fresh_slot(self):
        state, _ = replay(fixture(), [self.handback()])
        retained_reviewer = state['tasks']['generic']['review_thread']
        review = dict(id='finding', kind='review', task='generic',
                      reviewer='independent', revision='a' * 40,
                      model=('gpt-6.1-sol', 'medium'), findings=['fix'])
        state, _ = replay(state, [review])
        state['host_capacity']['available'] = 0
        state, _ = replay(state, [dict(id='fix', kind='route_fix', task='generic',
                                       owner='author')])
        state, actions = replay(state, [dict(self.handback(revision='b' * 40),
                                             id='corrected')])
        self.assertIn(('resume_review_same', 'generic', 'b' * 40,
                       ('gpt-6.1-sol', 'medium')), actions)
        self.assertEqual(state['tasks']['generic']['phase'], 'in_review')
        self.assertEqual(state['tasks']['generic']['review_thread'], retained_reviewer)

    def test_unchanged_host_capacity_does_not_retry_known_absent_start(self):
        initial = fixture()
        failed = dict(id='failed', kind='failed_start', task='generic',
                      known_absent=True)
        state, actions = replay(initial, [failed])
        self.assertNotIn(('retry_same_claim', 'generic'), actions)
        state, actions = replay(state, [])
        self.assertEqual(actions, [])
        action, artifacts = parent_continuation(state, {'managed': 'existing-other'})
        self.assertEqual(action, 'await')
        self.assertIn(('generic', None, 'host_capacity'), artifacts)
        changed = dict(id='new-capacity', kind='host_capacity', task='generic',
                       available=1, generation=2)
        state, actions = replay(state, [changed])
        self.assertIn(('retry_same_claim', 'generic'), actions)

    def test_unrelated_work_has_fresh_independent_review_assignment(self):
        state, _ = replay(fixture(), [self.handback()])
        state, _ = replay(state, [dict(id='finding', kind='review', task='generic',
                         reviewer='independent', revision='a' * 40,
                         model=('gpt-6.1-sol', 'medium'), findings=['fix'])])
        # A separate work item carries its own assignment, not the prior history.
        state['tasks']['unrelated'] = dict(owner='new-author', thread='new-thread',
            phase='running', evidence=None, review_model=('gpt-6.1-sol', 'medium'),
            landed=False, checks=True)
        state, actions = replay(state, [self.handback('unrelated', 'new-author')])
        self.assertIn(('review', 'unrelated', 'a' * 40,
                       ('gpt-6.1-sol', 'medium')), actions)
        self.assertFalse(any(a[0] == 'resume_review_same' for a in actions))
        self.assertEqual(state['tasks']['generic']['phase'], 'needs_attention')
        self.assertNotEqual(state['tasks']['unrelated']['review_thread'],
                            state['tasks']['generic']['review_thread'])

    def test_idle_completion_and_two_independent_handbacks(self):
        initial = fixture()
        events = [self.handback(), self.handback('managed', 'other-author')]
        state, actions = replay(initial, events)
        self.assertEqual([a[1] for a in actions if a[0] == 'review'],
                         ['generic', 'managed'])
        self.assertEqual(state['threads'], ['author-thread', 'other-thread'])
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
        capacity = dict(id='inactive-reviews', kind='host_capacity', task='generic',
                        available=2, generation=2)
        state, actions = replay(state, reviews + [capacity])
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
                  kind='failed_start', known_absent=True),
                  dict(id='capacity', task='managed', kind='host_capacity',
                       available=2, generation=2)]
        result, actions = replay(state, events)
        self.assertIn(('retry_same_claim', 'managed'), actions)
        self.assertEqual(len(result['threads']), len(set(result['threads'])))
        self.assertFalse(any(a[0] == 'release' for a in actions))
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

    def test_parent_awaits_handback_and_review_using_retained_handles(self):
        state = fixture()
        handles = {'generic': 'existing-author', 'managed': 'existing-other'}
        action, artifacts = parent_continuation(state, handles)
        self.assertEqual(action, 'await')
        self.assertIn(('generic', 'existing-author', 'author_handback'), artifacts)
        state, actions = replay(state, [self.handback()])
        handles['generic'] = 'assigned-reviewer'
        action, artifacts = parent_continuation(state, handles)
        self.assertEqual(action, 'await')
        self.assertIn(('generic', 'assigned-reviewer', 'review'), artifacts)
        handoff, retained = parent_continuation(state, handles, wait_available=False)
        self.assertEqual(handoff, 'handoff')
        self.assertEqual(retained, artifacts)
        # Explicit owner resume processes the artifact; completion alone is data.
        review = dict(id='parent-review', kind='review', task='generic',
                      reviewer='independent', revision='a' * 40,
                      model=('gpt-6.1-sol', 'medium'), findings=[])
        resumed, actions = replay(state, [review])
        self.assertEqual(state['tasks']['generic']['phase'], 'in_review')
        self.assertEqual(resumed['tasks']['generic']['phase'], 'approved')
        action, artifacts = parent_continuation(resumed, handles)
        self.assertEqual(action, 'await')
        self.assertEqual(artifacts, [('managed', 'existing-other', 'author_handback')])
        self.assertFalse(any(a[0] in ('review', 'retry_same_claim') for a in actions))

    def test_complete_drain_gate_and_blocked_dependencies(self):
        state = fixture()
        state['tasks'] = {}
        self.assertEqual(drain_gate(state), ('drained', []))
        for queue in ('eligible_queue', 'pending_handbacks', 'fixes',
                      'required_reviews', 'integration', 'status_writes'):
            busy = dict(state, **{queue: ['named artifact']})
            self.assertEqual(drain_gate(busy)[0], 'active', queue)
            self.assertEqual(parent_continuation(busy, {})[0], 'process')
            _, actions = replay(busy, [])
            self.assertNotIn(('request_work',), actions)
        state['tasks']['blocked'] = dict(phase='blocked', owner='retained-owner',
                                         blocker='external approval',
                                         next_action='owner requests approved adapter')
        self.assertEqual(drain_gate(state)[0], 'blocked')
        outcome, obligations = parent_continuation(state, {'blocked': 'retained-handle'})
        self.assertEqual(outcome, 'blocked')
        self.assertEqual(obligations, [('blocked', 'external approval',
                                       'owner requests approved adapter')])
        self.assertEqual(state['tasks']['blocked']['owner'], 'retained-owner')
        self.assertEqual(desk_safety_net(state, 'same-dispatch', True, mode='split')[0], 'blocked')
        del state['tasks']['blocked']['next_action']
        self.assertEqual(drain_gate(state)[0], 'active')
        state['tasks']['blocked']['phase'] = 'unknown'
        self.assertEqual(drain_gate(state)[0], 'active')

    def test_actionable_handbacks_and_other_obligations_precede_wait(self):
        state = fixture()
        handles = {'generic': 'same-author', 'managed': 'other-author'}
        state['pending_handbacks'] = ['generic']
        action, obligations = parent_continuation(state, handles)
        self.assertEqual(action, 'process')
        self.assertIn(('pending_handbacks', 'generic'), obligations)
        resumed, actions = replay(state, [self.handback()])
        self.assertEqual(resumed['pending_handbacks'], [])
        self.assertIn(('review', 'generic', 'a' * 40,
                       ('gpt-6.1-sol', 'medium')), actions)
        handles['generic'] = 'reviewer'
        self.assertEqual(parent_continuation(resumed, handles)[0], 'await')
        for queue in ('fixes', 'integration', 'status_writes'):
            busy = dict(resumed, **{queue: ['confirmed obligation']})
            self.assertEqual(parent_continuation(busy, handles)[0], 'process', queue)
        ready = fixture()
        ready['tasks']['generic']['phase'] = 'review_pending'
        self.assertEqual(parent_continuation(ready, handles)[0], 'process')
        ready['reviews'] = 2
        self.assertEqual(parent_continuation(ready, handles)[0], 'await')

    def test_child_after_would_yield_and_desk_resumes_same_handle(self):
        state = fixture()
        dispatcher = 'retained-dispatch'
        action, handle, obligations = desk_safety_net(state, dispatcher, True, mode='split')
        self.assertEqual((action, handle), ('resume_same', dispatcher))
        self.assertTrue(obligations)
        resumed, actions = replay(state, [self.handback()])
        self.assertEqual(resumed['tasks']['generic']['phase'], 'in_review')
        self.assertEqual(len([a for a in actions if a[0] == 'review']), 1)
        _, repeated = replay(resumed, [self.handback()])
        self.assertEqual(repeated, [])
        self.assertEqual(desk_safety_net(resumed, dispatcher, True, False, 'split')[0],
                         'handoff')
        self.assertEqual(state['tasks']['generic']['phase'], 'running')

    def test_findings_fix_same_review_and_user_steering_preserve_owners(self):
        state, _ = replay(fixture(), [self.handback()])
        review = dict(id='finding', kind='review', task='generic',
                      reviewer='independent', revision='a' * 40,
                      model=('gpt-6.1-sol', 'medium'), findings=['fix'])
        state, actions = replay(state, [review])
        self.assertIn(('hold', 'generic'), actions)
        self.assertEqual(parent_continuation(state, {'managed': 'retained'})[0], 'process')
        state, actions = replay(state, [dict(id='route-fix', kind='route_fix',
                                  task='generic', owner='author')])
        self.assertIn(('resume_author_same', 'generic', 'author'), actions)
        self.assertEqual(state['tasks']['generic']['phase'], 'running')
        self.assertEqual(parent_continuation(state, {'generic': 'same-author',
                         'managed': 'retained'})[0], 'await')
        steered, action = user_steering(state, ['new-P1', 'later-task'])
        self.assertEqual(action, ('route_queue', ('new-P1', 'later-task')))
        self.assertEqual(steered['tasks'], state['tasks'])
        self.assertEqual(drain_gate(steered)[0], 'active')
        fix = dict(self.handback(revision='b' * 40), id='fix-handback')
        state, actions = replay(steered, [fix])
        self.assertIn(('resume_review_same', 'generic', 'b' * 40,
                       ('gpt-6.1-sol', 'medium')), actions)
        self.assertEqual(state['tasks']['generic']['owner'], 'author')
        self.assertEqual(state['reviews'], 1)
        review = dict(review, id='fixed-review', revision='b' * 40, findings=[])
        state, actions = replay(state, [review])
        self.assertIn(('approved', 'generic'), actions)
        self.assertEqual(state['reviews'], 0)
        self.assertEqual(state['eligible_queue'], ['new-P1', 'later-task'])

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

class CoordinatorModes(unittest.TestCase):
    """Synthetic model of merged/split mode selection and registry handoff."""

    def policy(self, **gate):
        return dict(gate)

    def test_mode_selection_gates(self):
        self.assertEqual(select_mode(self.policy()), 'merged')
        # Not gates: remote, issue number, existing forge/project, board none,
        # authorization text naming no destination.
        for ignored in ('git_remote', 'issue_number', 'forge_exists',
                        'board_mode_none', 'authorization_names_no_destination'):
            self.assertEqual(select_mode(self.policy(**{ignored: True})), 'merged')
        mapped = self.policy(board_destination=True, status_mapping=True,
                             authorized_writer='dispatcher')
        self.assertEqual(select_mode(mapped), 'split')
        # A configured but unavailable gate still selects split.
        self.assertEqual(select_mode(dict(mapped, gate_available=False)), 'split')
        self.assertEqual(board_operations(dict(mapped, gate_available=False),
                                          'split'), 'blocked')
        self.assertEqual(board_operations(mapped, 'split'), 'available')
        self.assertEqual(board_operations(self.policy(board_mode_none=True),
                                          'merged'), 'none')
        # Non-gates never change a gated selection.
        self.assertEqual(select_mode(dict(mapped, git_remote=True,
                                          issue_number=True)), 'split')
        self.assertEqual(select_mode(self.policy(external_claim_required=True)),
                         'split')
        # Destination without mapping or authorized writer is not a gate.
        self.assertEqual(select_mode(self.policy(board_destination=True)), 'merged')

    def test_user_override_both_ways(self):
        mapped = self.policy(board_destination=True, status_mapping=True,
                             authorized_writer='dispatcher')
        self.assertEqual(select_mode(self.policy(), override='separate_dispatcher'),
                         'split')
        self.assertEqual(select_mode(self.policy(), override='coordinate_yourself'),
                         'merged')
        self.assertEqual(select_mode(dict(mapped, authorized_writer='coordinator'),
                                     override='coordinate_yourself'), 'merged')
        # Policy's authorized card writer is specifically the dispatcher.
        self.assertEqual(select_mode(mapped, override='coordinate_yourself'),
                         'conflict')

    def test_merged_lifecycle_has_zero_dispatcher_starts(self):
        trace = lifecycle_trace('merged')
        self.assertEqual(trace['dispatcher_starts'], 0)
        # Counts derive from replaying handback/review events, not constants.
        self.assertEqual((trace['author_starts'], trace['review_starts']), (1, 1))
        self.assertEqual(trace['phase'], 'in_review')
        self.assertEqual(trace['starters'], {'crewbook/desk'})
        self.assertEqual(lifecycle_trace('split')['dispatcher_starts'], 1)
        self.assertEqual(lifecycle_trace('split')['starters'],
                         {'crewbook/desk', 'crewbook/dispatch'})
        with self.assertRaises(ValueError):
            start_dispatcher(fixture(), 'merged')
        self.assertEqual(slot_count('merged', authors=2, reviewers=2, design=1,
                                    helpers=2), 7)
        self.assertEqual(slot_count('split', authors=2, reviewers=2, design=1,
                                    helpers=2), 8)

    def test_registry_round_trip_and_stale_handles(self):
        state, _ = replay(fixture(), [])
        state['tasks']['generic'].update(landing_required=True,
                                         landing_authorized=True)
        text = registry_dump(state, mode='merged', session='s1',
                             updated='2026-01-01T00:00:00Z', target='repo')
        self.assertTrue(text.startswith('crewbook-registry: 1\n'))
        self.assertTrue(text.rstrip().splitlines()[-1].startswith('Resume:'))
        self.assertIn('target: repo', text)
        for forbidden in ('token', 'password', 'credential', 'body'):
            dirty = copy.deepcopy(state)
            dirty['tasks']['generic'][forbidden] = 'x'
            with self.assertRaises(ValueError):
                registry_dump(dirty, mode='merged', session='s1',
                              updated='2026-01-01T00:00:00Z', target='repo')
        dirty = copy.deepcopy(state)
        dirty['tasks']['generic']['evidence'] = 'ghp_' + 'a' * 20
        with self.assertRaises(ValueError):
            registry_dump(dirty, mode='merged', session='s1',
                          updated='2026-01-01T00:00:00Z', target='repo')
        same = registry_load(text, session='s1')
        self.assertEqual(same['mode'], 'merged')
        self.assertEqual(same['target'], 'repo')
        self.assertEqual(drain_gate(registry_state(same, state))[1],
                         drain_gate(state)[1])
        self.assertEqual(registry_resume(same, 's1'),
                         [('await', 'generic', 'author-thread'),
                          ('await', 'managed', 'other-thread')])
        # A fresh session never reuses handles; it resolves ownership first.
        actions = registry_resume(registry_load(text, session='s2'), 's2')
        self.assertEqual(actions, [('resolve_owner', 'generic'),
                                   ('resolve_owner', 'managed')])
        self.assertFalse(any(a[0] == 'fresh_start' for a in actions))

    def test_split_registry_has_sole_writer_after_start(self):
        state, _ = replay(fixture(), [])
        stamp = '2026-01-01T00:00:00Z'
        # Desk writes the header and the dispatcher start record, then only reads.
        header = registry_dump(dict(state, tasks={}), 'split', 's1', stamp, 'repo')
        self.assertEqual(registry_writer('split', header_written=False,
                                         actor='desk'), 'desk')
        self.assertEqual(registry_writer('split', header_written=True,
                                         actor='desk'), None)
        self.assertEqual(registry_writer('split', header_written=True,
                                         actor='dispatcher'), 'dispatcher')
        self.assertEqual(registry_writer('merged', header_written=True,
                                         actor='desk'), 'desk')
        self.assertIn('mode: split', header)

    def test_concurrent_second_desk_does_not_write(self):
        state, _ = replay(fixture(), [])
        text = registry_dump(state, 'merged', 's1', '2026-01-01T00:00:00Z', 'repo')
        self.assertEqual(second_desk_action(registry_load(text, 's2'), 's2'),
                         ('read_only', 'ask_human'))
        self.assertEqual(second_desk_action(dict(tasks={}, session='s2'), 's2'),
                         ('write', None))

    def test_merged_desk_without_wait_tool_writes_registry_and_hands_off(self):
        state, _ = replay(fixture(), [])
        handles = {'generic': 'author-thread', 'managed': 'other-thread'}
        action, awaited, side = merged_desk_turn(state, handles, wait_available=True)
        self.assertEqual((action, side), ('await', None))
        action, awaited, side = merged_desk_turn(state, handles,
                                                 wait_available=False)
        self.assertEqual((action, side), ('handoff', 'write_registry'))
        self.assertTrue(awaited)
        # Documented-only re-entry never permits ending with open obligations.
        action, _, side = merged_desk_turn(state, handles, wait_available=False,
                                           completion_reenters='documented')
        self.assertEqual((action, side), ('handoff', 'write_registry'))
        action, _, side = merged_desk_turn(state, handles, wait_available=False,
                                           completion_reenters='observed')
        self.assertEqual((action, side), ('end_relying_on_reentry',
                                          'write_registry'))
        # Safety net is split-only.
        self.assertEqual(desk_safety_net(state, 'd', True, mode='merged')[0],
                         'not_applicable')


if __name__ == '__main__':
    unittest.main()
