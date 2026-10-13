"""Observe supplied GitHub REST PR evidence; no network or mutation operations."""
import argparse
import json
from pathlib import Path
import re
import sys

from source_linear_history import git as source_git

METHODS = ('rebase', 'merge', 'squash')
SHA = re.compile(r'[0-9a-f]{40}|[0-9a-f]{64}')


def observe(pr, configured_method, method, head, base):
    """Readiness concerns the selected merge method only, not checks/review/consent."""
    result = {'state': 'pending', 'method': method, 'head': head, 'base': base}

    def finish(state, reason):
        return dict(result, state=state, reason=reason)

    if configured_method not in METHODS or method not in METHODS:
        return finish('pending', 'explicit integration method required')
    if configured_method != method:
        return finish('blocked', 'method differs from configured integration method')
    if not all(isinstance(value, str) and SHA.fullmatch(value) for value in (head, base)):
        return finish('pending', 'full expected head and base required')
    if not isinstance(pr, dict):
        return finish('pending', 'REST pull request object required')
    for key, expected in (('head', head), ('base', base)):
        observed = pr.get(key)
        if not isinstance(observed, dict) or observed.get('sha') != expected:
            return finish('pending', 'REST ' + key + ' differs from expected revision')
    field = 'rebaseable' if method == 'rebase' else 'mergeable'
    value = pr.get(field)
    if value is False:
        return finish('blocked', field + ' is false')
    if value is not True:
        return finish('pending', field + ' is unknown')
    return finish('ready', field + ' is true for expected head and base')


def read_local_git(*args, **kwargs):
    # Read-looking object queries may fetch and write in a partial clone.
    # Older Git that lacks this option fails closed as unavailable evidence.
    return source_git('--no-lazy-fetch', '--no-optional-locks', *args, **kwargs)


def local_history(root, head, base):
    """Physical, complete local history only; ownership remains caller evidence."""
    if not all(isinstance(value, str) and SHA.fullmatch(value) for value in (head, base)):
        return {'state': 'pending', 'reason': 'full head and base required'}
    try:
        for revision in (head, base):
            if read_local_git('cat-file', '-t', revision, root=root).stdout.strip() != b'commit':
                return {'state': 'pending', 'reason': 'local revision is not a commit'}
        if read_local_git('rev-parse', '--is-shallow-repository', root=root).stdout.strip() != b'false':
            return {'state': 'pending', 'reason': 'shallow local history'}
        graft_path = read_local_git('rev-parse', '--git-path', 'info/grafts', root=root).stdout.decode().strip()
        grafts = Path(graft_path)
        if not grafts.is_absolute():
            grafts = Path(root) / grafts
        if grafts.exists() or grafts.is_symlink():
            return {'state': 'pending', 'reason': 'local grafts present'}
        ancestry = read_local_git('merge-base', '--is-ancestor', base, head, root=root, allow_failure=True)
        if ancestry.returncode == 1:
            return {'state': 'blocked', 'reason': 'head does not descend from expected base'}
        if ancestry.returncode:
            return {'state': 'pending', 'reason': 'local ancestry unavailable'}
        count = int(read_local_git('rev-list', '--count', '--min-parents=2', base + '..' + head,
                        root=root).stdout)
        return {'state': 'ready' if count == 0 else 'blocked', 'topic_merge_count': count}
    except (OSError, ValueError):
        return {'state': 'pending', 'reason': 'local history unavailable'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configured-method', required=True, choices=METHODS)
    parser.add_argument('--method', required=True, choices=METHODS)
    parser.add_argument('--head', required=True)
    parser.add_argument('--base', required=True)
    parser.add_argument('--root', help='optional local checkout for separate linear-history proof')
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError('REST observation exceeds 1 MiB')
        pr = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        parser.exit(1, 'merge-readiness: invalid REST observation: ' + str(error) + '\n')
    result = observe(pr, args.configured_method, args.method, args.head, args.base)
    result['local_history'] = (local_history(args.root, args.head, args.base) if args.root else
                               {'state': 'pending', 'reason': 'local checkout not supplied'})
    print(json.dumps(result, sort_keys=True))
    # The local result is separate: a merge-permitting target need not be linear.
    return {'ready': 0, 'blocked': 1, 'pending': 2}[result['state']]


if __name__ == '__main__':
    sys.exit(main())
