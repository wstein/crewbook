#!/usr/bin/env python3
"""Board helper: `move` one card with read-back, `sync` to reconcile all cards.

Maintenance tool, not exported. Standard library and `gh` only. Option ids are
read from the project's Status field, never hardcoded. Exit 0 ok, 1 failure.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dispatch_snapshot as snap  # noqa: E402

PROJECT_ID = 'PVT_kwHNjWrOAZaiCg'  # crewbook board, project 10
REPO = 'wstein/crewbook'
STATUSES = ('Todo', 'In progress', 'In review', 'Ready to push', 'Blocked')

QUERY = '''query($id: ID!, $after: String) {
  node(id: $id) { ... on ProjectV2 {
    field(name: "Status") { ... on ProjectV2SingleSelectField {
      id options { id name } } }
    items(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes { id
        status: fieldValueByName(name: "Status") {
          ... on ProjectV2ItemFieldSingleSelectValue { name } }
        content { ... on Issue { number state
          repository { nameWithOwner } } } } } } } }'''

MUTATION = '''mutation($p: ID!, $i: ID!, $f: ID!, $o: String!) {
  updateProjectV2ItemFieldValue(input: {projectId: $p, itemId: $i,
    fieldId: $f, value: {singleSelectOptionId: $o}}) { projectV2Item { id } } }'''


# Registry phase (first word, lowercase) -> wanted status; docs/team.md.
PHASES = {'start requested': 'In progress', 'blocked': 'Blocked'}
ISSUE = re.compile(r'#?(\d+)\b')
BRANCH = re.compile(r'(?:[A-Za-z0-9._-]+/)?(\d+)-')


class BoardError(Exception):
    pass


def run_gh(args):
    try:
        p = subprocess.run(['gh'] + args, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                           timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise BoardError('gh failed: %s' % type(exc).__name__)
    if p.returncode != 0:
        raise BoardError('gh exit %d: %s' % (
            p.returncode, p.stderr.decode('utf-8', 'replace').strip()[:200]))
    return p.stdout.decode('utf-8', 'replace')


def graphql(query, **variables):
    args = ['api', 'graphql', '-f', 'query=' + query]
    for key, value in variables.items():
        if value is not None:
            args += ['-f', '%s=%s' % (key, value)]
    try:
        return json.loads(run_gh(args))['data']
    except (ValueError, KeyError, TypeError):
        raise BoardError('unexpected gh response')


def load(project_id=PROJECT_ID, repo=REPO):
    """Return (field_id, {status name: option id}, {issue number: card})."""
    field, cards, after = None, {}, None
    while True:
        node = graphql(QUERY, id=project_id, after=after)['node']
        try:
            field = node['field']
            page = node['items']
            for item in page['nodes']:
                content = item.get('content') or {}
                if (content.get('repository') or {}).get(
                        'nameWithOwner') != repo:
                    continue
                cards[content['number']] = {
                    'item': item['id'], 'state': content['state'],
                    'status': (item.get('status') or {}).get('name')}
            if not page['pageInfo']['hasNextPage']:
                break
            after = page['pageInfo']['endCursor']
        except (KeyError, TypeError):
            raise BoardError('unexpected board shape')
    try:
        options = {o['name']: o['id'] for o in field['options']}
        return field['id'], options, cards
    except (KeyError, TypeError):
        raise BoardError('Status field not found')


def move(number, status, project_id=PROJECT_ID, repo=REPO):
    """Move one card, read it back, raise BoardError on any mismatch.
    Returns the previous status (equal to status when nothing changed)."""
    if status == 'Done':
        raise BoardError('refusing Done: project automation or the human')
    field_id, options, cards = load(project_id, repo)
    if status not in options:
        raise BoardError('unknown status %r' % status)
    card = cards.get(number)
    if card is None:
        raise BoardError('no card for #%d' % number)
    old = card['status']
    if old == status:
        return old
    graphql(MUTATION, p=project_id, i=card['item'], f=field_id,
            o=options[status])
    now = load(project_id, repo)[2].get(number, {}).get('status')
    if now != status:
        raise BoardError('read-back mismatch for #%d: wanted %r, found %r'
                         % (number, status, now))
    return old


def read_registry(root, path=None):
    """Parse the registry; free-form log lines after `Resume:` are ignored."""
    if path is None:
        common = snap.git(root, 'rev-parse', '--git-common-dir').strip()
        path = os.path.join(os.path.realpath(os.path.join(root, common)),
                            'crewbook', 'registry.md')
    try:
        with open(path, 'rb') as handle:
            text = handle.read(262145).decode('ascii', 'replace')
    except OSError:
        raise snap.Unavailable('no registry file')
    kept = []
    for line in text.split('\n'):
        kept.append(line)
        if line.startswith('Resume: '):
            break
    reg = snap.registry_parse('\n'.join(kept)) if len(text) <= 262144 else None
    if reg is None:
        raise snap.Unavailable('damaged or foreign registry')
    return reg


def wanted(root, registry_path=None):
    """{issue number: (status, reason)} for every card with positive evidence."""
    try:
        reg = read_registry(root, registry_path)
        rows = snap.git(root, 'worktree', 'list', '--porcelain')
    except snap.Unavailable as exc:
        raise BoardError('cannot read registry/worktrees: %s' % exc)
    out = {}
    for name, fields in reg['tasks'].items():
        m = ISSUE.match(name)
        phase = (fields.get('phase') or '').strip().lower()
        if m and phase in PHASES:
            out.setdefault(int(m.group(1)),
                           (PHASES[phase], 'registry phase %s' % phase))
    for line in rows.splitlines():
        if line.startswith('branch '):
            m = BRANCH.match(line[7:].replace('refs/heads/', '', 1))
            if m:
                out.setdefault(int(m.group(1)),
                               ('In progress', 'worktree branch'))
    return out


def target(current, signal):
    """(status, reason) to move to, or None. Never lowers without evidence."""
    if signal is None:
        return ('Todo', 'no worktree or registry signal') \
            if current == 'In progress' else None
    status, reason = signal
    if status == current:
        return None
    if status == 'In progress' and current not in (None, 'Todo'):
        return None  # In review / Ready to push / Blocked are never lowered
    return status, reason


def sync(root, dry_run=False, registry_path=None, project_id=PROJECT_ID,
         repo=REPO):
    """Reconcile open cards, printing each change; return the diff lines."""
    signals = wanted(root, registry_path)
    cards = load(project_id, repo)[2]
    lines = []
    for number, card in sorted(cards.items()):
        if card['state'] != 'OPEN' or card['status'] == 'Done':
            continue
        change = target(card['status'], signals.get(number))
        if change is None:
            continue
        if not dry_run:
            move(number, change[0], project_id, repo)
        lines.append('#%d %s -> %s (%s)' % (
            number, card['status'] or '(none)', change[0], change[1]))
        print(lines[-1], flush=True)
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    mv = sub.add_parser('move', help='move one card and verify it')
    mv.add_argument('issue', type=int)
    mv.add_argument('status')
    sy = sub.add_parser('sync', help='reconcile all open cards')
    sy.add_argument('--dry-run', action='store_true')
    sy.add_argument('--root', default=os.getcwd())
    sy.add_argument('--registry')
    args = ap.parse_args(argv)
    try:
        if args.cmd == 'move':
            old = move(args.issue, args.status)
            print('#%d %s -> %s' % (args.issue, old or '(none)', args.status)
                  if old != args.status else
                  '#%d already %s' % (args.issue, old))
        else:
            sync(args.root, args.dry_run, args.registry)
    except BoardError as exc:
        print('board: %s' % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
