"""Shared vectors for the confirmation record v1 codec (second implementation).

Go (workharbor internal/confirm) is authoritative. These cases port its
TestGolden, TestEncodeEscapes, TestDecodeRejects, TestValidateRejects,
TestDigestChangesPerField, TestDigestDomainSeparation and
TestDecodeSyntaxReason, plus checks of the pinned fixture bytes and of
Python-only edge cases (nesting depth, int64 bound, -0, UTF-16 input, year
0000) that are NOT shared vectors and not verified against Go by any committed
test.
"""
import hashlib
import json
import unittest
from pathlib import Path

import confirmrecord as c

FIXTURES = Path(__file__).resolve().parent / 'confirm-fixtures' / 'v1'
PINS = json.loads((FIXTURES / 'pins.json').read_text(encoding='utf-8'))
LAND = 'land-cli'
BASE_COMMIT = '4f1c2ab9e0d3c5a7b18f6e2d4c0a9b8e7f6d5c4b'


def raw_file(name):
    return (FIXTURES / (name + '.json')).read_bytes()


def fixture(name):
    """Record bytes: the file minus exactly one final newline, like Go."""
    if name == 'escapes':  # decision-relay with a non-ASCII question
        r = c.decode(fixture('decision-relay'))
        r.ext = {'crewbook.answered': 'H97:y'}
        r.question = 'd\u00e9j\u00e0 \U0001F600'
        return c.encode(r)
    b = raw_file(name)
    return b[:-1] if b.endswith(b'\n') else b


def rep(name, old, new):
    s = fixture(name).decode('utf-8')
    assert old in s, old
    return s.replace(old, new, 1).encode('utf-8')


class PinTests(unittest.TestCase):
    def test_fixture_bytes_and_digests_are_pinned(self):
        self.assertEqual(PINS['source']['commit'],
                         'fcbf2a365805c3a4acc3b5fd1e535041117b97ad')
        self.assertEqual(sorted(PINS['files']), ['decision-relay.json', 'land-cli.json'])
        for name, want in PINS['files'].items():
            data = (FIXTURES / name).read_bytes()
            self.assertTrue(data.endswith(b'\n'), name)  # newline is part of the pin
            self.assertEqual(hashlib.sha256(data).hexdigest(), want, name)
        for name, want in PINS['digests'].items():
            self.assertEqual(c.digest_of(fixture(name)), want, name)
        # Independent of the module's own prefix constant.
        raw = fixture(LAND)
        self.assertEqual(
            hashlib.sha256(b'workharbor-confirm-v1\x00' + raw).hexdigest(),
            PINS['digests'][LAND])


class GoldenTests(unittest.TestCase):
    def test_golden_decode_reencode_digest(self):  # vector 1
        for name, want in PINS['digests'].items():
            raw = fixture(name)
            r = c.decode(raw)
            self.assertEqual(c.encode(r), raw)
            self.assertEqual(c.digest_of(raw), want)
            self.assertEqual(r.digest(), want)

    def test_round_trip_is_stable(self):
        for name in PINS['digests']:
            b = c.encode(c.decode(fixture(name)))
            self.assertEqual(c.encode(c.decode(b)), b)

    def test_escapes_match_go_writer(self):  # vector 2
        r = c.decode(fixture('decision-relay'))
        r.question = 'd\u00e9j\u00e0 \U0001F600 "q" \\ \n'
        b = c.encode(r)
        self.assertTrue(all(0x20 <= x < 0x7f for x in b))
        self.assertIn(rb'"question":"d\u00e9j\u00e0 \ud83d\ude00 \"q\" \\ \u000a"', b)
        self.assertEqual(c.decode(b).question, r.question)

    def test_other_control_and_del_escapes(self):
        r = c.decode(fixture('decision-relay'))
        r.question = '\t\r\x00\x7f\u2028'
        self.assertIn(rb'"question":"\u0009\u000d\u0000\u007f\u2028"', c.encode(r))

    def test_keys_sorted_by_utf8_bytes_not_utf16(self):
        r = c.decode(fixture('decision-relay'))
        r.ext = {'x.\U0001F600': 1, 'x.\uffff': 2, 'x.a': True}
        b = c.encode(r)
        self.assertLess(b.index(rb'"x.a"'), b.index(rb'"x.\uffff"'))
        self.assertLess(b.index(rb'"x.\uffff"'), b.index(rb'"x.\ud83d\ude00"'))
        self.assertIn(rb'"x.a":true', b)  # bool is not written as 1
        self.assertEqual(c.decode(b).ext, r.ext)


class DecodeRejectTests(unittest.TestCase):
    def check(self, data, want):
        with self.assertRaises(want):
            c.decode(data)

    def test_decode_rejects(self):  # vectors 3-4, same classes as Go
        cases = [
            ('unknown v', rep(LAND, '"v":1', '"v":2'), c.ErrUnknownVersion),
            ('unknown top-level field', rep(LAND, '{"action"', '{"zzz":"x","action"'), c.ErrUnknownField),
            ('unknown action', rep(LAND, '"action":"land"', '"action":"merge"'), c.ErrUnknownAction),
            ('unknown channel', rep(LAND, '"channel":"cli"', '"channel":"sms"'), c.ErrUnknownChannel),
            ('short commit', rep(LAND, BASE_COMMIT, '4f1c2ab'), c.ErrBadSubject),
            ('uppercase commit', rep(LAND, BASE_COMMIT, BASE_COMMIT.upper()), c.ErrBadSubject),
            ('at offset', rep(LAND, '2026-10-06T09:12:00Z', '2026-10-06T11:12:00+02:00'), c.ErrBadTime),
            ('at fractional', rep(LAND, '2026-10-06T09:12:00Z', '2026-10-06T09:12:00.5Z'), c.ErrBadTime),
            ('at lowercase z', rep(LAND, '2026-10-06T09:12:00Z', '2026-10-06T09:12:00z'), c.ErrBadTime),
            ('ai evidence', rep(LAND, '"kind":"base"', '"kind":"ai-summary"'), c.ErrAIEvidence),
            ('unknown evidence kind', rep(LAND, '"kind":"base"', '"kind":"vibes"'), c.ErrBadEvidence),
            ('evidence unsorted', rep(
                LAND,
                '{"kind":"check","name":"check-local","result":"pass"},{"kind":"check","name":"commitlint","result":"pass"}',
                '{"kind":"check","name":"commitlint","result":"pass"},{"kind":"check","name":"check-local","result":"pass"}'),
             c.ErrEvidenceOrder),
            ('evidence duplicate', rep(
                LAND, '{"kind":"check","name":"commitlint","result":"pass"}',
                '{"kind":"check","name":"check-local","result":"pass"}'), c.ErrEvidenceOrder),
            ('keys unsorted', rep(LAND, '"by":"human","channel":"cli"', '"channel":"cli","by":"human"'), c.ErrNotCanonical),
            ('whitespace', rep(LAND, '"v":1', '"v": 1'), c.ErrSyntax),
            ('raw non-ASCII', rep(LAND, 'feat/example', 'feat/\u00e9x'), c.ErrNotCanonical),
            ('uppercase escape', rep('escapes', r'\u00e9', r'\u00E9'), c.ErrNotCanonical),
            ('short newline escape', rep('escapes', '"question":"', '"question":"' + r'\n'), c.ErrNotCanonical),
            ('float', rep(LAND, '"v":1', '"v":1.0'), c.ErrSyntax),
            ('exponent', rep(LAND, '"v":1', '"v":1e0'), c.ErrSyntax),
            ('leading zero', rep(LAND, '"v":1', '"v":01'), c.ErrSyntax),
            ('null', rep(LAND, '"by":"human"', '"by":null'), c.ErrSyntax),
            ('duplicate key', rep(LAND, '{"action"', '{"at":"x","action"'), c.ErrSyntax),
            ('duplicate key same', rep(LAND, '"by":"human"', '"by":"human","by":"human"'), c.ErrSyntax),
            ('trailing bytes', fixture(LAND) + b'\n', c.ErrSyntax),
            ('invalid UTF-8', rep(LAND, 'feat/example', 'feat/').replace(b'feat/', b'feat/\xff', 1), c.ErrSyntax),
            ('lone surrogate', rep('escapes', r'\ud83d\ude00', r'\ud83d'), c.ErrSyntax),
            ('empty', b'', c.ErrSyntax),
            ('not object', b'[]', c.ErrSyntax),
            ('missing at', rep(LAND, '"at":"2026-10-06T09:12:00Z",', ''), c.ErrMissingRequired),
            ('unknown answer key', rep(LAND, '"answer":{', '"answer":{"x":"y",'), c.ErrBadAnswer),
            ('unknown subject key', rep(LAND, '"subject":{', '"subject":{"x":"y",'), c.ErrBadSubject),
            ('email by', rep(LAND, '"by":"human"', '"by":"w@example.org"'), c.ErrBadBy),
            ('bad assurance', rep(LAND, '"assurance":"local"', '"assurance":"strong"'), c.ErrBadAssurance),
            ('typed_sha not prefix', rep(LAND, '"value":"4f1c2ab"', '"value":"4f1c2ac"'), c.ErrBadAnswer),
            ('typed_sha too short', rep(LAND, '"value":"4f1c2ab"', '"value":"4f1c2a"'), c.ErrBadAnswer),
            ('ext not namespaced', rep('escapes', 'crewbook.answered', 'answered'), c.ErrBadExt),
            ('wrong schema', rep(LAND, 'workharbor.confirmation', 'other'), c.ErrBadSchema),
        ]
        for name, data, want in cases:
            with self.subTest(name):
                self.check(data, want)

    def test_check_order(self):  # vector 5: parse, field, required, v, version, types, canonical, validate
        # unknown field wins over a missing required field
        self.check(rep(LAND, '"at":"2026-10-06T09:12:00Z",', '').replace(b'{"action"', b'{"zzz":"x","action"', 1),
                   c.ErrUnknownField)
        # unknown version wins over a bad later field and over non-canonical form
        self.check(rep(LAND, '"v":1', '"v":2').replace(b'"by":"human"', b'"by":5'), c.ErrUnknownVersion)
        # v must be an integer: a bool is not
        self.check(rep(LAND, '"v":1', '"v":true'), c.ErrSyntax)
        self.check(rep(LAND, '"v":1', '"v":"1"'), c.ErrSyntax)
        # field type errors precede canonical comparison
        self.check(rep(LAND, '"by":"human"', '"by":5'), c.ErrSyntax)
        # canonical comparison precedes validation
        self.check(rep(LAND, '"by":"human","channel":"cli"', '"channel":"sms","by":"human"'), c.ErrNotCanonical)

    def test_syntax_reasons(self):  # vector 6
        bs = chr(92)
        cases = [
            ('null', 'null not allowed', rep(LAND, '"by":"human"', '"by":null')),
            ('float', 'floats not allowed', rep(LAND, '"v":1', '"v":1.0')),
            ('utf8', 'invalid UTF-8', rep(LAND, 'feat/example', 'feat/').replace(b'feat/', b'feat/\xff', 1)),
            ('surrogate', 'lone surrogate', rep('escapes', bs + 'ud83d' + bs + 'ude00', bs + 'ud83d')),
            ('low surrogate', 'lone surrogate', rep('escapes', bs + 'ud83d' + bs + 'ude00', bs + 'ude00')),
        ]
        for name, msg, data in cases:
            with self.subTest(name):
                with self.assertRaises(c.ErrSyntax) as cm:
                    c.decode(data)
                self.assertIn(msg, str(cm.exception))

    def test_python_only_edge_cases(self):  # vector 9, not verified against Go
        land = fixture(LAND).decode('ascii')
        cases = {
            'nan': land.replace('"v":1', '"v":NaN'),
            'infinity': land.replace('"v":1', '"v":Infinity'),
            'negative zero': land.replace('"v":1', '"v":-0'),
            'int64 overflow': land.replace('"v":1', '"v":9223372036854775808'),
            'int64 underflow': land.replace('"v":1', '"v":-9223372036854775809'),
            'huge integer': land.replace('"v":1', '"v":' + '9' * 5000),
            'newline whitespace': land + '\n',
            'leading whitespace': ' ' + land,
            'nesting': land.replace('"v":1', '"v":' + '[' * 100 + ']' * 100),
            'deep ext': land.replace('"v":1', '"v":1,"ext":' + '{"a.b":' * 20 + '1' + '}' * 20),
        }
        for name, text in cases.items():
            with self.subTest(name):
                self.check(text.encode('ascii'), c.ErrSyntax)
        # int64 bounds are accepted by the parser (then rejected as a version).
        self.check(land.replace('"v":1', '"v":9223372036854775807').encode(), c.ErrUnknownVersion)
        self.check(land.replace('"v":1', '"v":-9223372036854775808').encode(), c.ErrUnknownVersion)
        # No BOM, no UTF-16/32 autodetect.
        self.check(b'\xef\xbb\xbf' + land.encode(), c.ErrSyntax)
        self.check(land.encode('utf-16'), c.ErrSyntax)
        self.check(land.encode('utf-16-le'), c.ErrSyntax)
        self.check(land.encode('utf-32'), c.ErrSyntax)
        with self.assertRaises(TypeError):
            c.decode(land)

    def test_nesting_depth_boundary(self):
        # Go: a value deeper than 16 fails. Top is depth 0, ext 1, its first array 2.
        def ext(n):  # n nested arrays below ext's value
            return '"v":1,"ext":{"a.b":' + '[' * n + ']' * n + '}'
        land = fixture(LAND).decode('ascii')
        ok = land.replace('"v":1', ext(15))  # empty innermost array at depth 16
        with self.assertRaises(c.ErrNotCanonical):  # parses; key order makes it non-canonical
            c.decode(ok.encode())
        with self.assertRaises(c.ErrSyntax):
            c.decode(land.replace('"v":1', ext(16)).encode())
        # A scalar one level below the deepest allowed container also fails.
        leaf = '"v":1,"ext":{"a.b":' + '[' * 15 + '1' + ']' * 15 + '}'
        with self.assertRaises(c.ErrSyntax):
            c.decode(land.replace('"v":1', leaf).encode())

    def test_ext_values_round_trip(self):
        r = c.decode(fixture('decision-relay'))
        r.ext = {'a.b': {'c': [1, -2, True, False, 'x', {}, []]}}
        self.assertEqual(c.decode(c.encode(r)).ext, r.ext)
        r.ext = {'a.b': None}
        with self.assertRaises(c.ErrSyntax):
            c.encode(r)
        r.ext = {'a.b': 1.5}
        with self.assertRaises(c.ErrSyntax):
            c.encode(r)


class ValidateRejectTests(unittest.TestCase):
    def base(self):
        return c.decode(fixture(LAND))

    def test_public_validate_requires_integer_version(self):
        # Python equality makes True and 1.0 equal to 1, but neither is a
        # v1 integer record version at the decode boundary.
        for version in (True, 1.0):
            with self.subTest(version=version, type=type(version).__name__):
                r = self.base()
                r.v = version
                with self.assertRaises(c.ErrUnknownVersion):
                    r.validate()
        r = self.base()
        r.validate()
        self.assertEqual(c.decode(c.encode(r)).v, 1)

    def test_validate_rejects(self):  # vector 7
        def set_subject(r):
            r.subject = c.Subject(issue='o/r#1')

        def mut(field, value):
            def f(r):
                setattr(r, field, value)
            return f

        def deep(path, value):
            def f(r):
                obj = r
                for p in path[:-1]:
                    obj = obj[int(p)] if isinstance(obj, list) else getattr(obj, p)
                setattr(obj, path[-1], value)
            return f

        cases = [
            ('land without commit', set_subject, c.ErrBadSubject),
            ('empty subject', mut('subject', c.Subject()), c.ErrBadSubject),
            ('yn bad value', mut('answer', c.Answer('yn', 'maybe')), c.ErrBadAnswer),
            ('deny with value', mut('answer', c.Answer('deny', 'x')), c.ErrBadAnswer),
            ('unknown mode', mut('answer', c.Answer('shrug')), c.ErrBadAnswer),
            ('option empty', mut('answer', c.Answer('option')), c.ErrBadAnswer),
            ('unknown version', mut('v', 2), c.ErrUnknownVersion),
            ('evidence kind only', mut('evidence', [c.Evidence(kind='check')]), c.ErrBadEvidence),
            ('evidence short object', mut('evidence', [c.Evidence(kind='base', object='0a1b')]), c.ErrBadEvidence),
            ('issue zero', deep(['subject', 'issue'], 'o/r#0'), c.ErrBadSubject),
            ('bad issue', deep(['subject', 'issue'], '#53'), c.ErrBadSubject),
            ('issue trailing newline', deep(['subject', 'issue'], 'o/r#1\n'), c.ErrBadSubject),
            ('commit trailing newline', deep(['subject', 'commit'], BASE_COMMIT + '\n'), c.ErrBadSubject),
            ('empty by', mut('by', ''), c.ErrBadBy),
            ('by space', mut('by', 'a b'), c.ErrBadBy),
            ('by tab', mut('by', 'a\tb'), c.ErrBadBy),
            ('by cr', mut('by', 'a\rb'), c.ErrBadBy),
            ('by lf', mut('by', 'a\nb'), c.ErrBadBy),
            ('at trailing newline', mut('at', '2026-10-06T09:12:00Z\n'), c.ErrBadTime),
            ('at month 13', mut('at', '2026-13-06T09:12:00Z'), c.ErrBadTime),
            ('at feb 30', mut('at', '2026-02-30T09:12:00Z'), c.ErrBadTime),
            ('at second 60', mut('at', '2026-10-06T09:12:60Z'), c.ErrBadTime),
            ('at non-ASCII digit', mut('at', '2026-10-06T09:12:0\u0660Z'), c.ErrBadTime),
            ('ext dot suffix', mut('ext', {'a.': 'x'}), c.ErrBadExt),
            ('ext dot prefix', mut('ext', {'.a': 'x'}), c.ErrBadExt),
            ('typed_sha trailing newline', mut('answer', c.Answer('typed_sha', '4f1c2ab\n')), c.ErrBadAnswer),
        ]
        for name, f, want in cases:
            with self.subTest(name):
                r = self.base()
                f(r)
                with self.assertRaises(want):
                    r.validate()
        # Accepted forms stay accepted.
        r = self.base()
        r.answer = c.Answer('yn', 'yes')
        r.subject.commit = 'a' * 64
        r.validate()
        r = self.base()
        r.answer = c.Answer('deny')
        r.validate()
        for ok in ('2024-02-29T00:00:00Z', '0000-02-29T23:59:59Z'):
            r = self.base()
            r.at = ok
            r.validate()

    def test_evidence_order_is_by_encoded_bytes(self):
        r = self.base()
        r.evidence = [c.Evidence(kind='audit', ref='b'), c.Evidence(kind='audit', ref='a')]
        with self.assertRaises(c.ErrEvidenceOrder):
            r.validate()
        r.evidence = [c.Evidence(kind='audit', ref='a'), c.Evidence(kind='audit', ref='b')]
        r.validate()
        # a prefix of another encoding is not "smaller" than a longer one by key order alone
        r.evidence = [c.Evidence(kind='audit', ref='a'), c.Evidence(kind='audit', ref='a', name='n')]
        with self.assertRaises(c.ErrEvidenceOrder):  # b'..."name"' < b'..."ref"'
            r.validate()


class DigestTests(unittest.TestCase):
    def test_digest_changes_per_field(self):  # vector 8
        base = c.decode(fixture(LAND))
        want = base.digest()

        def ev(i, **kw):
            def f(r):
                for k, v in kw.items():
                    setattr(r.evidence[i], k, v)
            return f

        def attr(obj, k, v):
            def f(r):
                setattr(getattr(r, obj) if obj else r, k, v)
            return f

        muts = {
            'v': attr('', 'v', 2),
            'schema': attr('', 'schema', base.schema + 'x'),
            'action': attr('', 'action', 'push'),
            'subject.commit': attr('subject', 'commit', 'b' * 40),
            'subject.branch': attr('subject', 'branch', 'other'),
            'subject.issue': attr('subject', 'issue', 'o/r#2'),
            'subject.decision': attr('subject', 'decision', 'H1'),
            'subject.ref': attr('subject', 'ref', 'r'),
            'question': attr('', 'question', 'other?'),
            'answer.mode': attr('answer', 'mode', 'yn'),
            'answer.value': attr('answer', 'value', '4f1c2ac'),
            'at': attr('', 'at', '2026-10-06T09:12:01Z'),
            'channel': attr('', 'channel', 'web'),
            'by': attr('', 'by', 'other'),
            'assurance': attr('', 'assurance', 'passkey'),
            'evidence kind': ev(1, kind='audit'),
            'evidence name': ev(1, name='x'),
            'evidence result': ev(1, result='fail'),
            'evidence object': ev(0, object='c' * 40),
            'evidence ref': ev(1, ref='x'),
            'evidence value': ev(1, value='x'),
            'evidence add': lambda r: r.evidence.append(c.Evidence(kind='audit', ref='z')),
            'evidence gone': attr('', 'evidence', []),
            'ext': attr('', 'ext', {'a.b': 'c'}),
        }
        seen = {}
        for name, mut in muts.items():
            r = base.copy()
            mut(r)
            got = r.digest()
            self.assertNotEqual(got, want, name)
            self.assertNotIn(got, seen, '%s collides with %s' % (name, seen.get(got)))
            seen[got] = name
        self.assertEqual(base.digest(), want)  # the copies never touched base

    def test_domain_separation(self):  # vector 8b
        raw = fixture(LAND)
        self.assertNotEqual(c.digest_of(raw), c.digest_of(b'x' + raw))
        self.assertEqual(c.DIGEST_PREFIX, b'workharbor-confirm-v1\x00')
        self.assertNotEqual(c.digest_of(raw), hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    unittest.main()
