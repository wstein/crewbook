"""Bounded property tests for the text parsers (issue #110).

Standard library only: a seeded `random.Random` drives small generators, so a
failure reproduces from the printed seed and iteration. Properties:

* no uncaught exception on arbitrary text (only the documented error class);
* malformed input is rejected (fail closed), never accepted as valid;
* valid input round-trips;
* documented limits hold.

Parsers covered: review lines (`review_lines.py`), confirmation records
(`confirmrecord.py`) and the dispatcher recovery state (`registry_parse` and
`registry_data` in `dispatch_snapshot.py`). Fixed seed and iteration counts
keep the whole module well under a few seconds.
"""
import json
import os
import random
import re
import tempfile
import unittest

import confirmrecord as cr
import dispatch_snapshot as ds
import review_lines as rl

SEED = 110
N = 300  # iterations per property

HEX = '0123456789abcdef'
ALPHABET = ('abcXYZ019 \t\r\n;:=#_-./@!"\\{}[],'
            'é€\U0001f600\x00\x7f\ud800')
# characters that matter to the grammars, biased toward near-valid input
TOKENS = ('CLEAR', 'NOT CLEAR', 'review started', 'model=', 'role=', ' ',
          '; ', 'opus', 'claude-opus-5-5', 'not_clear', '## ', 'Resume: ',
          'owner: ', 'phase: ', 'session: ', 'crewbook-registry: 1', '\n',
          '\r\n', '{', '}', '"', ':', ',', 'v', '1')


def rng_for(name):
    return random.Random('%d:%s' % (SEED, name))


def rand_text(r, maxlen=60):
    parts = []
    for _ in range(r.randint(0, 12)):
        if r.random() < 0.5:
            parts.append(r.choice(TOKENS))
        else:
            parts.append(''.join(r.choice(ALPHABET)
                                 for _ in range(r.randint(0, 6))))
    return ''.join(parts)[:maxlen * 4]


def rand_sha(r):
    return ''.join(r.choice(HEX) for _ in range(40))


def mutate(r, s):
    """One random edit of a str or bytes value (delete, insert, replace, cut)."""
    if not s:
        return s
    i = r.randrange(len(s))
    op = r.randrange(4)
    one = (lambda x: bytes([x])) if isinstance(s, bytes) else chr
    if op == 0:
        return s[:i] + s[i + 1:]
    if op == 1:
        return s[:i] + one(r.randrange(32, 127)) + s[i:]
    if op == 2:
        return s[:i] + one(r.randrange(32, 127)) + s[i + 1:]
    return s[:i]


MODEL_CHARS = [chr(c) for c in range(0x21, 0x7f) if chr(c) != ';']


def rand_model(r):
    while True:
        m = ''.join(r.choice(MODEL_CHARS) for _ in range(r.randint(1, 20)))
        if not m.startswith('model='):
            return m


def fmt_line(kind, sha, model, role=None):
    return '%s %s%s model=%s' % (
        kind, sha, ' role=%s' % role if role else '', model)


def rand_role(r):
    if r.random() < 0.5:
        return None
    return r.choice('abcxyz') + ''.join(
        r.choice('abc019-') for _ in range(r.randint(0, 6)))


class ReviewLineProperties(unittest.TestCase):
    def test_arbitrary_text_never_raises(self):
        r = rng_for('review-arbitrary')
        sha = 'a' * 40
        for i in range(N):
            text = rand_text(r)
            with self.subTest(i=i, text=text):
                p = rl.parse(text)
                self.assertTrue(p is None or len(p) == 3)
                lines = rl.split_note(text)
                self.assertTrue(all(l.strip() for l in lines))
                rl.split_evidence(text)
                self.assertIsInstance(rl.gate(lines, sha, 'opus'), list)
                rl.canonical(text)

    def test_valid_lines_round_trip(self):
        r = rng_for('review-roundtrip')
        for i in range(N):
            kind = r.choice(['review started', 'CLEAR', 'NOT CLEAR'])
            sha, model = rand_sha(r), rand_model(r)
            line = fmt_line(kind, sha, model, rand_role(r))
            with self.subTest(i=i, line=line):
                self.assertEqual(rl.parse(line), (kind, sha, model))
            lines = [line, fmt_line('CLEAR', sha, rand_model(r))]
            # models never contain ';', so a joined value splits back exactly
            self.assertEqual(rl.split_evidence(rl.join_evidence(lines)), lines)
            self.assertEqual(rl.split_note('\n\n'.join(lines) + '\n'), lines)

    def test_malformed_lines_are_rejected(self):
        r = rng_for('review-malformed')
        for i in range(N):
            sha, model = rand_sha(r), rand_model(r)
            kind = r.choice(['review started', 'CLEAR', 'NOT CLEAR'])
            good = fmt_line(kind, sha, model)
            bads = [
                fmt_line(kind, sha[:-1], model),               # short sha
                fmt_line(kind, sha + r.choice(HEX), model),    # long sha
                fmt_line(kind, sha.upper().replace('0', 'A'), model)
                if any(c.isalpha() for c in sha) else good + ' ',
                '%s %s model=' % (kind, sha),                  # empty model
                '%s %s' % (kind, sha),                         # no model
                good + ' ',                                    # trailing blank
                ' ' + good,                                    # leading blank
                good + r.choice(' ;\t\n'),                     # junk suffix
                good.replace('model=', 'model=model='),        # doubled key
                good.replace(' model=', ' model= '),           # blank model
                kind.lower() + good[len(kind):]
                if kind.lower() != kind else good + '\n',      # wrong case
            ]
            for bad in bads:
                if bad == good:
                    continue
                with self.subTest(i=i, bad=bad):
                    self.assertIsNone(rl.parse(bad))

    def test_random_edits_never_widen_acceptance(self):
        """Whatever parse accepts must re-parse to its own canonical form."""
        r = rng_for('review-edits')
        for i in range(N):
            line = fmt_line(r.choice(['CLEAR', 'NOT CLEAR', 'review started']),
                            rand_sha(r), rand_model(r), rand_role(r))
            for _ in range(r.randint(1, 3)):
                line = mutate(r, line)
            p = rl.parse(line)
            if p is not None:
                with self.subTest(i=i, line=line):
                    kind, sha, model = p
                    self.assertRegex(sha, r'[0-9a-f]{40}\Z')
                    self.assertTrue(model and ';' not in model
                                    and ' ' not in model)
                    self.assertIn(' model=' + model, line)

    def test_gate_fails_closed_without_a_valid_clear(self):
        r = rng_for('review-gate-garbage')
        sha = rand_sha(r)
        for i in range(N):
            lines = [rand_text(r) for _ in range(r.randint(0, 6))]
            lines += [mutate(r, fmt_line('CLEAR', sha, 'opus'))
                      for _ in range(r.randint(0, 3))]
            # a mutated line may still be a valid CLEAR for sha; drop those
            lines = [l for l in lines if rl.parse(l) is None]
            with self.subTest(i=i, lines=lines):
                self.assertNotEqual(rl.gate(lines, sha, 'opus'), [])

    def test_gate_not_clear_always_blocks(self):
        r = rng_for('review-gate-notclear')
        for i in range(N):
            sha = rand_sha(r)
            other = rand_sha(r)
            nc = r.choice([
                fmt_line('NOT CLEAR', sha, rand_model(r), rand_role(r)),
                'not clear %s anything' % sha,
                'NOT_CLEAR: %s' % sha.upper(),
                ' Not-Clear  %s ' % sha,
                'not clear without any sha',
                'not clear',
            ])
            lines = [fmt_line('CLEAR', sha, 'opus'), nc]
            r.shuffle(lines)
            with self.subTest(i=i, nc=nc):
                self.assertNotEqual(rl.gate(lines, sha, 'opus'), [])
            # documented exception: a malformed NOT CLEAR that names only a
            # different full sha does not block this one
            other_nc = 'not clear on %s' % other
            if other != sha:
                self.assertEqual(rl.gate([lines[0], other_nc], sha, 'opus')
                                 if lines[0].startswith('CLEAR') else [], [])

    def test_gate_required_count_and_tiers(self):
        r = rng_for('review-gate-count')
        sha = rand_sha(r)
        pool = ['opus', 'sonnet', 'haiku', 'gpt-6.1-sol/medium', 'x/y']
        for i in range(N):
            k = r.randint(0, len(pool))
            models = r.sample(pool, k)
            noise = [fmt_line('review started', sha, 'opus'),
                     fmt_line('CLEAR', rand_sha(r), 'opus')]
            lines = noise + [fmt_line('CLEAR', sha, m) for m in models]
            if models and r.random() < 0.5:  # alias of the same stamp
                lines.append(fmt_line('CLEAR', sha, models[0]))
            required = r.randint(1, 5)
            tiers = set(pool[:r.randint(1, len(pool))])
            gaps = rl.gate(lines, sha, tiers, required)
            expect_ok = k >= required and set(models) <= tiers
            with self.subTest(i=i, models=models, required=required,
                              tiers=sorted(tiers)):
                self.assertEqual(gaps == [], expect_ok)

    def test_gate_rejects_bad_arguments(self):
        r = rng_for('review-gate-args')
        for i in range(N):
            bad_sha = r.choice([rand_sha(r)[:r.randint(0, 39)],
                                'A' * 40, None, 5, rand_text(r)])
            if isinstance(bad_sha, str) and re.fullmatch('[0-9a-f]{40}', bad_sha):
                continue
            with self.subTest(sha=bad_sha), self.assertRaises(ValueError):
                rl.gate([], bad_sha, 'opus')
        sha = 'a' * 40
        for bad in (0, -1, True, 1.0, '1', None):
            with self.subTest(required=bad), self.assertRaises(ValueError):
                rl.gate([], sha, 'opus', bad)
        with self.assertRaises(ValueError):
            rl.gate([], sha, None)


# ------------------------------------------------------------ confirmation

def rand_str(r, maxlen=12):
    pool = 'abcxyz019 -_./:' + 'é€\U0001f600"\\\n\t'
    return ''.join(r.choice(pool) for _ in range(r.randint(1, maxlen)))


def rand_record(r):
    commit = rand_sha(r) if r.random() < 0.5 else ''.join(
        r.choice(HEX) for _ in range(64))
    action = r.choice(cr.ACTIONS)
    subject = cr.Subject(commit=commit)
    if r.random() < 0.4:
        subject.issue = 'o%d/r.x-y#%d' % (r.randint(0, 9), r.randint(1, 999))
    if r.random() < 0.3:
        subject.branch = rand_str(r)
    mode = r.choice(['yn', 'typed_sha', 'option', 'deny'])
    answer = {'yn': lambda: cr.Answer('yn', r.choice(['yes', 'no'])),
              'typed_sha': lambda: cr.Answer('typed_sha',
                                             commit[:r.randint(7, 40)]),
              'option': lambda: cr.Answer('option', rand_str(r)),
              'deny': lambda: cr.Answer('deny', '')}[mode]()
    rec = cr.Record(
        v=1, schema=cr.SCHEMA, action=action, subject=subject,
        question=rand_str(r) if r.random() < 0.5 else '',
        answer=answer,
        at='%04d-%02d-%02dT%02d:%02d:%02dZ' % (
            r.randint(0, 9999), r.randint(1, 12), r.randint(1, 28),
            r.randint(0, 23), r.randint(0, 59), r.randint(0, 59)),
        channel=r.choice(cr.CHANNELS), by=r.choice(['werner', 'a-b', 'x_1']),
        assurance=r.choice(cr.ASSURANCES))
    ev = []
    for _ in range(r.randint(0, 3)):
        ev.append(cr.Evidence(
            kind=r.choice(cr.EVIDENCE_KINDS), name=rand_str(r),
            result=r.choice(['', 'pass'])))
    ev.sort(key=cr._encode_evidence)
    # drop duplicates: equal entries violate the strict ordering rule
    rec.evidence = [e for i, e in enumerate(ev)
                    if i == 0 or cr._encode_evidence(ev[i - 1])
                    != cr._encode_evidence(e)]
    if r.random() < 0.3:
        rec.ext = {'x.%s' % r.choice('abc'): r.choice(
            [rand_str(r), r.randint(-5, 5), True, [1, 'a'], {'k': 'v'}])}
    return rec


def accepts(data):
    try:
        return cr.decode(data)
    except cr.ConfirmError:
        return None


def with_ext_value(rec, payload):
    """Canonical bytes of rec with ext {"a.b": <payload>}; payload is raw JSON
    text spliced in place of a 0, so the key order stays canonical and the
    payload is the only thing that can make the record invalid."""
    rec = rec.copy()
    rec.ext = {'a.b': 0}
    data = cr.encode(rec)
    assert b'"a.b":0' in data
    return data.replace(b'"a.b":0', b'"a.b":' + payload, 1)


def swap_in(data, old, new):
    """Return data with the first old replaced by new, or None if absent."""
    return data.replace(old, new, 1) if old in data else None


class ConfirmRecordProperties(unittest.TestCase):
    def test_arbitrary_bytes_never_raise_other_errors(self):
        r = rng_for('confirm-arbitrary')
        base = cr.encode(rand_record(rng_for('confirm-base')))
        for i in range(N):
            kind = i % 3
            if kind == 0:
                data = bytes(r.randrange(256) for _ in range(r.randint(0, 80)))
            elif kind == 1:
                data = rand_text(r).encode('utf-8', 'surrogatepass')
            else:
                data = mutate(r, mutate(r, base))
            with self.subTest(i=i, data=data):
                rec = accepts(data)  # anything but ConfirmError fails the test
                if rec is not None:  # accepted => it is the canonical form
                    self.assertEqual(cr.encode(rec), data)
                    rec.validate()

    def test_valid_records_round_trip(self):
        r = rng_for('confirm-roundtrip')
        for i in range(N):
            rec = rand_record(r)
            data = cr.encode(rec)
            with self.subTest(i=i, data=data):
                got = cr.decode(data)
                self.assertEqual(got, rec)
                self.assertEqual(cr.encode(got), data)
                self.assertEqual(got.digest(), rec.digest())
                self.assertRegex(rec.digest(), r'[0-9a-f]{64}\Z')
                data.decode('ascii')

    def test_every_single_edit_is_canonical_or_rejected(self):
        r = rng_for('confirm-edits')
        for i in range(N):
            data = cr.encode(rand_record(r))
            edited = mutate(r, data)
            rec = accepts(edited)
            with self.subTest(i=i, edited=edited):
                if rec is not None:
                    self.assertEqual(cr.encode(rec), edited)

    def test_structural_malformations_are_rejected(self):
        r = rng_for('confirm-malformed')
        for i in range(N // 3):
            rec = rand_record(r)
            data = cr.encode(rec)
            text = data.decode('ascii')
            body = text[1:-1]
            cases = {
                'whitespace': text.replace(',', ', ', 1),
                'newline': text + '\n',
                'bom': '﻿' + text,
                'unknown field': '{"zz":1,' + body + '}',
                'duplicate key': '{' + body + ',"v":1}',
                'float': text.replace('"v":1', '"v":1.0', 1),
                'exp': text.replace('"v":1', '"v":1e0', 1),
                'nan': text.replace('"v":1', '"v":NaN', 1),
                'null ext': with_ext_value(rec, b'null').decode(),
                'bool v': text.replace('"v":1', '"v":true', 1),
                'big int': text.replace('"v":1', '"v":%d' % (1 << 70), 1),
                'neg zero': text.replace('"v":1', '"v":-0', 1),
                'version': text.replace('"v":1', '"v":2', 1),
                'truncated': text[:r.randint(0, len(text) - 1)],
                'deep': with_ext_value(rec, b'[' * 40 + b']' * 40).decode(),
                'trailing': text + '{}',
                'array': '[' + text + ']',
                'empty': '',
                'upper escape': swap_in(text, '\\u00e9', '\\u00E9'),
                'literal utf8': swap_in(text, '\\u00e9', 'é'),
                'lone surrogate': with_ext_value(rec, b'"\\ud800"').decode(),
            }
            for name, case in cases.items():
                if case is None or case == text:
                    continue
                raw = case.encode('utf-8', 'surrogatepass')
                with self.subTest(i=i, case=name, data=raw):
                    self.assertIsNone(accepts(raw))
            bad_utf8 = data[:-1] + b'\xff}'
            self.assertIsNone(accepts(bad_utf8))
            self.assertIsNone(accepts(text.encode('utf-16')))

    def test_semantic_violations_are_rejected(self):
        r = rng_for('confirm-semantic')
        for i in range(N // 3):
            rec = rand_record(r)
            cr.encode(rec)  # valid baseline
            variants = []

            def vary(label, fn):
                c = rec.copy()
                fn(c)
                variants.append((label, c))
            vary('schema', lambda c: setattr(c, 'schema', c.schema + 'x'))
            vary('action', lambda c: setattr(c, 'action', 'merge'))
            vary('channel', lambda c: setattr(c, 'channel', 'sms'))
            vary('assurance', lambda c: setattr(c, 'assurance', 'strong'))
            vary('email by', lambda c: setattr(c, 'by', 'a@b'))
            vary('empty by', lambda c: setattr(c, 'by', ''))
            vary('space by', lambda c: setattr(c, 'by', 'a b'))
            vary('empty subject', lambda c: setattr(c, 'subject', cr.Subject()))
            vary('upper commit', lambda c: setattr(c.subject, 'commit', 'A' * 40))
            vary('short commit', lambda c: setattr(c.subject, 'commit', 'a' * 39))
            vary('bad issue', lambda c: setattr(c.subject, 'issue', 'o/r#0'))
            vary('mode', lambda c: setattr(c.answer, 'mode', 'maybe'))
            vary('yn', lambda c: (setattr(c.answer, 'mode', 'yn'),
                                  setattr(c.answer, 'value', 'maybe')))
            vary('deny value', lambda c: (setattr(c.answer, 'mode', 'deny'),
                                          setattr(c.answer, 'value', 'x')))
            vary('typed_sha short', lambda c: (
                setattr(c.answer, 'mode', 'typed_sha'),
                setattr(c.answer, 'value', c.subject.commit[:6])))
            vary('typed_sha foreign', lambda c: (
                setattr(c.answer, 'mode', 'typed_sha'),
                setattr(c.answer, 'value', ('0' if c.subject.commit[0] != '0'
                                            else '1') * 7)))
            for bad_at in ('2026-02-30T00:00:00Z', '2026-01-01T24:00:00Z',
                           '2026-01-01T00:00:00+00:00', '2026-01-01 00:00:00Z',
                           '2026-01-01T00:00:00.5Z', '', '2026-13-01T00:00:00Z'):
                vary('at ' + bad_at, lambda c, a=bad_at: setattr(c, 'at', a))
            vary('ai evidence', lambda c: c.evidence.insert(
                0, cr.Evidence(kind='ai-review', name='x')))
            vary('unknown kind', lambda c: c.evidence.append(
                cr.Evidence(kind='zzz', name='x')))
            vary('empty evidence', lambda c: c.evidence.append(
                cr.Evidence(kind='zzzz')))
            vary('bare ext', lambda c: setattr(c, 'ext', {'plain': 1}))
            vary('dot ext', lambda c: setattr(c, 'ext', {'a.': 1}))
            if len(rec.evidence) > 1:
                vary('unsorted', lambda c: c.evidence.reverse())
                vary('duplicate', lambda c: c.evidence.append(
                    cr.dataclasses.replace(c.evidence[-1])))
            for label, c in variants:
                with self.subTest(i=i, case=label):
                    with self.assertRaises(cr.ConfirmError):
                        c.validate()
                    # the codec does not validate on encode; decode must
                    # still refuse the well-formed bytes of an invalid record
                    try:
                        data = cr.encode(c)
                    except cr.ConfirmError:
                        continue
                    self.assertIsNone(accepts(data))

    def test_depth_limit(self):
        base = rand_record(rng_for('confirm-depth'))
        for depth in range(1, 25):
            data = with_ext_value(base, b'[' * depth + b']' * depth)
            with self.subTest(depth=depth):
                # ext object is depth 1 and the value sits at depth 2
                if depth + 2 > cr.MAX_DEPTH + 1:
                    self.assertIsNone(accepts(data))
                else:
                    self.assertIsNotNone(accepts(data))

    def test_int64_limit(self):
        base = rand_record(rng_for('confirm-int'))
        for n, ok in ((cr._INT64_MAX, True), (cr._INT64_MIN, True),
                      (cr._INT64_MAX + 1, False), (cr._INT64_MIN - 1, False),
                      (10 ** 400, False)):
            data = with_ext_value(base, b'%d' % n)
            with self.subTest(n=n):
                if ok:
                    self.assertEqual(accepts(data).ext, {'a.b': n})
                else:
                    self.assertIsNone(accepts(data))

    def test_decode_requires_bytes(self):
        for bad in ('{}', None, 5, [b'{}']):
            with self.assertRaises(TypeError):
                cr.decode(bad)


# --------------------------------------------------------------- registry

NAMEPOOL = 'abcxyz019-_./ #:'
FIELDS = ('owner', 'handle', 'handle_session', 'phase', 'evidence',
          'landing_required', 'landing_authorized', 'next_awaited')
HEADERS = ('mode', 'coordinator', 'target', 'model', 'updated')


def pr(r, lo=1, hi=12):
    return ''.join(r.choice(NAMEPOOL) for _ in range(r.randint(lo, hi)))


def rand_registry(r):
    """Return (text, expected parse result)."""
    reg = {'crewbook-registry': '1', 'session': pr(r), 'tasks': {}}
    lines = ['crewbook-registry: 1', 'session: ' + reg['session']]
    for k in r.sample(HEADERS, r.randint(0, len(HEADERS))):
        reg[k] = pr(r)
        lines.append('%s: %s' % (k, reg[k]))
    r.shuffle(lines)
    lines.append('')
    for _ in range(r.randint(0, 5)):
        name = 't' + pr(r)
        if name in reg['tasks']:
            continue
        fields = reg['tasks'][name] = {}
        lines.append('## ' + name)
        for f in r.sample(FIELDS, r.randint(0, len(FIELDS))):
            fields[f] = pr(r, 0)
            lines.append('%s: %s' % (f, fields[f]))
        lines.append('')
    lines.append('Resume: ' + pr(r))
    return '\n'.join(lines) + r.choice(['', '\n', '\n\n']), reg


class RecoveryStateProperties(unittest.TestCase):
    def test_arbitrary_text_never_raises(self):
        r = rng_for('registry-arbitrary')
        valid = rand_registry(rng_for('registry-base'))[0]
        for i in range(N):
            text = rand_text(r) if i % 2 else mutate(r, mutate(r, valid))
            with self.subTest(i=i, text=text):
                reg = ds.registry_parse(text)
                if reg is not None:  # accepted => the strict grammar holds
                    self.assertEqual(reg['crewbook-registry'], '1')
                    self.assertIn('session', reg)
                    self.assertRegex(text, r'(?m)^Resume: [\x20-\x7e]+\r?$')

    def test_valid_state_round_trips(self):
        r = rng_for('registry-roundtrip')
        for i in range(N):
            text, expected = rand_registry(r)
            with self.subTest(i=i, text=text):
                self.assertEqual(ds.registry_parse(text), expected)
                crlf = text.replace('\n', '\r\n')
                self.assertEqual(ds.registry_parse(crlf), expected)

    def test_malformed_state_is_rejected(self):
        r = rng_for('registry-malformed')
        for i in range(N):
            text, reg = rand_registry(r)
            lines = text.rstrip('\n').split('\n')
            first_block = next((j for j, l in enumerate(lines)
                                if l.startswith('## ')), None)
            resume = len(lines) - 1
            cases = {
                'no resume': '\n'.join(lines[:resume]),
                'after resume': '\n'.join(lines + ['## late']),
                'two resumes': '\n'.join(lines + ['Resume: again']),
                'wrong version': text.replace('crewbook-registry: 1',
                                              'crewbook-registry: 2', 1),
                'no session': '\n'.join(l for l in lines
                                        if not l.startswith('session: ')),
                'dup header': 'mode: a\n' + text if 'mode' in reg
                else 'session: x\n' + text,
                'unknown header': 'bogus: 1\n' + text,
                'empty header value': 'mode: \n' + text,
                'empty': '',
                'non-grammar line': text.replace('Resume:', 'Resumeé:'),
            }
            if first_block is not None:
                name = lines[first_block]
                cases['dup block'] = '\n'.join(
                    lines[:resume] + ['', name, 'owner: x', '', lines[-1]])
                cases['unknown field'] = '\n'.join(
                    lines[:first_block + 1] + ['bogus: x'] + lines[first_block + 1:])
                cases['dup field'] = '\n'.join(
                    lines[:first_block + 1] + ['owner: x', 'owner: y']
                    + lines[first_block + 1:])
            for label, case in cases.items():
                with self.subTest(i=i, case=label, text=case):
                    got = ds.registry_parse(case)
                    self.assertIsNone(got)

    def test_file_limits(self):
        good = rand_registry(rng_for('registry-file'))[0]
        with tempfile.TemporaryDirectory() as d:
            def load(raw):
                path = os.path.join(d, 'registry.md')
                with open(path, 'wb') as fh:
                    fh.write(raw)
                try:
                    return ds.registry_data('.', path)
                except ds.Unavailable as exc:
                    return str(exc)
            self.assertIsInstance(load(good.encode()), dict)
            # one byte over the 262144 limit is damaged, however valid
            big = good.rstrip('\n') + '\n' * (262145 - len(good.rstrip('\n')))
            self.assertEqual(len(big), 262145)
            self.assertEqual(load(big.encode()), 'damaged or foreign')
            exact = good.rstrip('\n') + '\n' * (262144 - len(good.rstrip('\n')))
            self.assertIsInstance(load(exact.encode()), dict)
            self.assertEqual(load(good.replace('session', 'sessé').encode()),
                             'damaged or foreign')
            self.assertEqual(load(b'\xff\xfe' + good.encode()),
                             'damaged or foreign')
            self.assertEqual(load(b' \t\r\n'), 'no registry file')
            self.assertEqual(load(b''), 'no registry file')
            self.assertEqual(load(good.encode() + b'\x00'),
                             'damaged or foreign')

    def test_rendered_output_is_bounded_and_clean(self):
        r = rng_for('registry-render')
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'registry.md')
            for i in range(30):
                text = rand_registry(r)[0]
                extra = ''.join('## t%d\nowner: o%d\n\n' % (j, j)
                                for j in range(r.randint(0, 40)))
                text = text.replace('Resume:', extra + 'Resume:', 1)
                with open(path, 'w') as fh:
                    fh.write(text)
                with self.subTest(i=i):
                    out = ds.section('registry', ds.registry, '.', path)
                    self.assertLessEqual(len(out), ds.LIMIT + 1)

    def test_clean_never_passes_unsafe_text(self):
        r = rng_for('clean')
        for i in range(N):
            value = r.choice([rand_text(r), r.randint(0, 99), None, b'x'])
            for pattern in (ds.TOKEN, ds.LABEL, ds.PATH_TOKEN):
                out = ds.clean(value, pattern)
                with self.subTest(value=value):
                    self.assertTrue(out == '?' or pattern.match(out))
                    self.assertNotIn('\n', out)


if __name__ == '__main__':
    unittest.main()
