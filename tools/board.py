#!/usr/bin/env python3
"""Board helper: `move` one card with read-back, `sync` (added separately).

Maintenance tool, not exported. Standard library and `gh` only. Option ids are
read from the project's Status field, never hardcoded. Exit 0 ok, 1 failure.
"""
import argparse
import json
import subprocess
import sys

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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    mv = sub.add_parser('move', help='move one card and verify it')
    mv.add_argument('issue', type=int)
    mv.add_argument('status')
    args = ap.parse_args(argv)
    try:
        if args.cmd == 'move':
            old = move(args.issue, args.status)
            print('#%d %s -> %s' % (args.issue, old or '(none)', args.status)
                  if old != args.status else
                  '#%d already %s' % (args.issue, old))
    except BoardError as exc:
        print('board: %s' % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
