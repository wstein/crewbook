#!/usr/bin/env python3
"""Read-only dispatcher snapshot: one compact deterministic block, no model tokens.

Maintenance tool, not exported. Git is read through plumbing only. Board and CI
data are supplied by the caller as JSON files (or '-' for stdin, at most one);
this repository has no board script and the tool never calls a forge or GraphQL.
Each section degrades to 'unavailable: <reason>' on its own.

Board JSON: {"cards": [{"column": str, "number": int, "own": bool}, ...]}
Registry: <git-common-dir>/crewbook/registry.md unless --registry PATH is given
(a supplied path wins); parsed with the strict grammar of docs/project-config.md,
anything else prints 'unavailable: damaged or foreign'. Each section prints a bounded share of the global 79-line budget, including a '... N more' line.
CI JSON:    {"runs": [{"workflow": str, "status": str, "conclusion": str|null,
             "sha": str, "id": int}, ...]}  (latest run per workflow = highest id)
"""
import argparse
import json
import os
import stat
import re
import subprocess
import sys

LIMIT = 12  # Six headers + six 12-line bodies + optional stamp = 79 lines.
TOKEN = re.compile(r'[A-Za-z0-9._/@+:-]{1,100}\Z')
LABEL = re.compile(r'[A-Za-z0-9._/@+:-][A-Za-z0-9._/@+: -]{0,99}\Z')
PATH_TOKEN = re.compile(r'[A-Za-z0-9._/@+:-]{1,400}\Z')
HEADER_LINE = re.compile(
    r'(crewbook-registry|mode|coordinator|target|model|session|updated): '
    r'([\x20-\x7e]+)')
BLOCK_LINE = re.compile(r'## ([\x20-\x7e]+)')
TASK_LINE = re.compile(r'(owner|handle|handle_session|phase|evidence|'
                       r'landing_required|landing_authorized|next_awaited): '
                       r'([\x20-\x7e]*)')
RESUME_LINE = re.compile(r'Resume: ([\x20-\x7e]+)')
NOTES_REF = 'refs/notes/review'


class Unavailable(Exception):
    pass


def git(root, *args):
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
           'GIT_CONFIG_SYSTEM': '/dev/null', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0',
           'LC_ALL': 'C'}
    try:
        p = subprocess.run(['git', '-C', root] + list(args), env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           stdin=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Unavailable('git failed: %s' % type(exc).__name__)
    if p.returncode != 0:
        if b'dubious ownership' in p.stderr or b'safe.directory' in p.stderr:
            raise Unavailable('git %s refused: repository owned by another '
                              'user (safe.directory)' % args[0])
        raise Unavailable('git %s exit %d' % (args[0], p.returncode))
    return p.stdout.decode('utf-8', 'replace')


def clean(value, pattern=TOKEN):
    """Return a short safe token or '?' so unexpected text never reaches output."""
    value = value if isinstance(value, str) else str(value)
    return value if pattern.match(value) else '?'


def branches(root, main):
    base = git(root, 'rev-parse', '--verify', '--quiet',
               main + '^{commit}').strip()
    out = git(root, 'for-each-ref', '--format=%(refname:lstrip=2) %(objectname)',
              'refs/heads')
    rows = []
    for line in out.splitlines():
        name, sha = line.rsplit(' ', 1)
        if name == main:
            continue
        n = int(git(root, 'rev-list', '--count', '%s..%s' % (base, sha)))
        if n:
            rows.append((name, n, sha))
    rows.sort()
    return rows, ['%s ahead=%d %s' % (clean(a), b, c) for a, b, c in rows]


def notes(root, rows):
    """Only refs/notes/review is read; other notes refs are ignored."""
    have = set()
    if git(root, 'for-each-ref', '--format=%(refname)', NOTES_REF).split():
        for line in git(root, 'notes', '--ref', NOTES_REF, 'list').splitlines():
            parts = line.split(' ')
            if len(parts) == 2:
                have.add(parts[1])
    return ['%s %s review-notes=%s' % (clean(name), sha[:12],
                                       'review' if sha in have else 'none')
            for name, _n, sha in rows]


def registry_parse(text):
    """Strict registry grammar (docs/project-config.md); None when damaged or
    foreign. Mirrors registry_parse in test_dispatch_recovery.py."""
    lines = [line[:-1] if line.endswith('\r') else line
             for line in text.split('\n')]
    while lines and not lines[-1]:
        lines.pop()
    reg = {'tasks': {}}
    i = 0
    while i < len(lines) and lines[i] and not lines[i].startswith('## '):
        m = HEADER_LINE.fullmatch(lines[i])
        if not m or m.group(1) in reg:
            return None
        reg[m.group(1)] = m.group(2)
        i += 1
    if reg.get('crewbook-registry') != '1' or 'session' not in reg:
        return None
    resume = False
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line:
            continue
        if resume:
            return None
        if RESUME_LINE.fullmatch(line):
            resume = True
            continue
        m = BLOCK_LINE.fullmatch(line)
        if not m or m.group(1) in reg['tasks']:
            return None
        fields = reg['tasks'][m.group(1)] = {}
        while i < len(lines) and lines[i]:
            f = TASK_LINE.fullmatch(lines[i])
            if not f or f.group(1) in fields:
                return None
            fields[f.group(1)] = f.group(2)
            i += 1
    return reg if resume else None


def registry_data(root, path=None):
    if path is None:
        common = git(root, 'rev-parse', '--git-common-dir').strip()
        path = os.path.join(os.path.realpath(os.path.join(root, common)),
                            'crewbook', 'registry.md')
    try:
        if not stat.S_ISREG(os.stat(path).st_mode):
            raise Unavailable('registry path is not a regular file')
        with open(path, 'rb') as handle:
            raw = handle.read(262145)
    except OSError:
        raise Unavailable('no registry file')
    if not raw.strip(b' \t\r\n'):
        raise Unavailable('no registry file')
    try:
        reg = registry_parse(raw.decode('ascii')) if len(raw) <= 262144 else None
    except UnicodeDecodeError:
        reg = None
    if reg is None:
        raise Unavailable('damaged or foreign')
    return reg


def registry(root, path=None):
    reg = registry_data(root, path)
    line = 'mode=%s coordinator=%s target=%s' % tuple(
        clean(reg.get(k, '-')) for k in ('mode', 'coordinator', 'target'))
    phases = {}
    for fields in reg['tasks'].values():
        ph = clean(fields.get('phase') or '-')
        phases[ph] = phases.get(ph, 0) + 1
    out = [line, 'assignments=%d %s' % (len(reg['tasks']), ' '.join(
        '%s=%d' % (k, v) for k, v in sorted(phases.items())))]
    for name, fields in sorted(reg['tasks'].items()):
        out.append('%s owner=%s phase=%s' % (
            clean(name), clean(fields.get('owner') or '-'),
            clean(fields.get('phase') or '-')))
    return out


def worktrees(root):
    out = git(root, 'worktree', 'list', '--porcelain')
    rows = []
    for block in out.strip().split('\n\n'):
        f = dict(l.split(' ', 1) if ' ' in l else (l, '')
                 for l in block.splitlines())
        if 'bare' in f:
            br = 'bare'
        else:
            br = f.get('branch', 'detached').replace('refs/heads/', '')
        # The registry grammar has no exact path/branch ownership link.
        # Never infer one from assignment names, handles or evidence text.
        rows.append('%s %s %s owner=unknown' % (
            clean(os.path.realpath(f.get('worktree', '?')), PATH_TOKEN),
            clean(br), clean(f.get('HEAD', '?')[:12])))
    return sorted(rows)


def load_json(path, label):
    try:
        if path == '-':
            return json.loads(sys.stdin.read(1048576))
        with open(path, encoding='utf-8') as handle:
            return json.loads(handle.read(1048576))
    except (OSError, ValueError) as exc:
        raise Unavailable('%s input unreadable: %s' % (label, type(exc).__name__))


def board(path):
    if path is None:
        raise Unavailable('no board input supplied')
    data = load_json(path, 'board')
    try:
        cols = {}
        for card in data['cards']:
            if card.get('own') is True:
                column = card['column']
                if not isinstance(column, str) or not LABEL.fullmatch(column):
                    raise Unavailable('board label unsupported')
                number = card['number']
                if type(number) is not int or number <= 0:
                    raise ValueError('invalid card number')
                cols.setdefault(column, []).append(number)
    except (KeyError, TypeError, ValueError, AttributeError):
        raise Unavailable('board input malformed')
    if not cols:
        return ['no own cards']
    return ['%s: %s' % (c, ' '.join('#%d' % n for n in sorted(v)))
            for c, v in sorted(cols.items())]


def ci(path):
    if path is None:
        raise Unavailable('no ci input supplied')
    data = load_json(path, 'ci')
    try:
        latest = {}
        for run in data['runs']:
            wf = run['workflow']
            if not isinstance(wf, str) or not LABEL.fullmatch(wf):
                raise Unavailable('ci label unsupported')
            if wf not in latest or int(run['id']) > int(latest[wf]['id']):
                latest[wf] = run
        return ['%s %s/%s %s' % (wf, clean(r['status']),
                                 clean(r.get('conclusion') or '-'),
                                 clean(r['sha'])[:12])
                for wf, r in sorted(latest.items())]
    except (KeyError, TypeError, ValueError, AttributeError):
        raise Unavailable('ci input malformed')


def cap(lines):
    if len(lines) > LIMIT:
        return lines[:LIMIT - 1] + ['... %d more' % (len(lines) - LIMIT + 1)]
    return lines or ['none']


def section(name, fn, *args):
    try:
        lines = fn(*args)
        if isinstance(lines, tuple):
            lines = lines[1]
    except Unavailable as exc:
        lines = ['unavailable: %s' % exc]
    except Exception as exc:  # a failing source never aborts the block
        lines = ['unavailable: %s' % type(exc).__name__]
    return ['[%s]' % name] + cap(lines)


def render(root, main, board_path, ci_path, stamp=None, registry_path=None):
    out = []
    if stamp:
        out.append('generated: %s' % clean(stamp))
    out += section('board', board, board_path)
    failed = False
    try:
        rows, blines = branches(root, main)
    except Exception as exc:
        failed = True
        rows, blines = [], ['unavailable: %s' % (
            exc if isinstance(exc, Unavailable) else type(exc).__name__)]
    out += ['[branches]'] + cap(blines)
    if failed:
        out += ['[notes]', blines[0]]
    else:
        out += section('notes', notes, root, rows)
    out += section('worktrees', worktrees, root)
    out += section('ci', ci, ci_path)
    out += section('registry', registry, root, registry_path)
    return '\n'.join(out) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', required=True, help='absolute repository root')
    ap.add_argument('--main', default='main')
    ap.add_argument('--board', help='board JSON path or - for stdin')
    ap.add_argument('--ci', help='CI JSON path or - for stdin')
    ap.add_argument('--registry', help='registry file path (wins over the default)')
    ap.add_argument('--stamp', help='optional label printed as the one time line')
    a = ap.parse_args(argv)
    if a.board == '-' and a.ci == '-':
        ap.error('only one input may be stdin')
    sys.stdout.write(render(a.root, a.main, a.board, a.ci, a.stamp, a.registry))
    return 0


if __name__ == '__main__':
    sys.exit(main())
