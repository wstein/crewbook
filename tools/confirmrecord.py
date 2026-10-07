"""Confirmation record v1: canonical encoder, strict decoder, validator, digest.

This is a second implementation of the neutral record defined by workharbor
(internal/confirm: record.go, canonical.go, decode.go). The Go code is
authoritative; this module is held to the shared fixtures in
tools/confirm-fixtures/v1 and to the vectors in tools/test_confirm.py. It does
no Markdown parsing and no I/O.

Python's json module differs from the Go encoder and parser, so the canonical
writer is custom (Go writes a newline as \\u000a, never \\n; keys sorted by
UTF-8 bytes; lowercase hex escapes; surrogate pairs for non-BMP; no floats or
null; bool is tested before int) and decoding adds strict checks around
json.loads: strict UTF-8 first (no UTF-16/32 autodetect, no BOM), duplicate
keys, floats, NaN/Infinity, null, lone surrogates, whitespace outside strings,
integers within int64 and a nesting cap of 16.

Python-only edge cases (the nesting-depth cap, the int64 bound, "-0", UTF-16
input, BOM and the year-0000 handling in the `at` rule) are NOT part of the
shared vectors and are not verified by any committed test against Go. They
were spot-checked once by hand against the Go decoder with a throwaway
harness that is not in this repository; error classes agreed, messages differ.

Python 3.9, standard library only.
"""
import dataclasses
import datetime
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

VERSION = 1
SCHEMA = 'workharbor.confirmation'
DIGEST_PREFIX = b'workharbor-confirm-v1\x00'
MAX_DEPTH = 16
_INT64_MIN = -(1 << 63)
_INT64_MAX = (1 << 63) - 1

ACTIONS = ('land', 'push', 'change.confirm', 'tokens.revoke', 'decision')
CHANNELS = ('cli', 'web', 'relay')
ASSURANCES = ('none', 'local', 'passkey')
EVIDENCE_KINDS = ('review-note', 'check', 'path-class', 'base', 'audit',
                  'passkey-assertion', 'decision-log')


class ConfirmError(ValueError):
    """Base of every error below; match the subclass like Go's errors.Is."""
    prefix = 'confirm'

    def __init__(self, detail=''):
        text = self.prefix + (': ' + detail if detail else '')
        super().__init__(text)


class ErrUnknownVersion(ConfirmError):
    prefix = 'confirm: unknown record version'


class ErrUnknownField(ConfirmError):
    prefix = 'confirm: unknown top-level field'


class ErrUnknownAction(ConfirmError):
    prefix = 'confirm: unknown action'


class ErrUnknownChannel(ConfirmError):
    prefix = 'confirm: unknown channel'


class ErrBadSchema(ConfirmError):
    prefix = 'confirm: bad schema name'


class ErrBadSubject(ConfirmError):
    prefix = 'confirm: bad subject'


class ErrBadAnswer(ConfirmError):
    prefix = 'confirm: bad answer'


class ErrBadTime(ConfirmError):
    prefix = 'confirm: at is not RFC 3339 UTC whole seconds with Z'


class ErrBadBy(ConfirmError):
    prefix = 'confirm: bad by'


class ErrBadAssurance(ConfirmError):
    prefix = 'confirm: bad assurance'


class ErrBadEvidence(ConfirmError):
    prefix = 'confirm: bad evidence'


class ErrAIEvidence(ConfirmError):
    prefix = 'confirm: ai evidence kind not accepted'


class ErrEvidenceOrder(ConfirmError):
    prefix = 'confirm: evidence not sorted by canonical bytes'


class ErrBadExt(ConfirmError):
    prefix = 'confirm: bad ext'


class ErrNotCanonical(ConfirmError):
    prefix = 'confirm: not canonical encoding'


class ErrSyntax(ConfirmError):
    prefix = 'confirm: invalid encoding'


class ErrMissingRequired(ConfirmError):
    prefix = 'confirm: missing required field'


@dataclass
class Subject:
    commit: str = ''
    branch: str = ''
    issue: str = ''
    decision: str = ''
    ref: str = ''


@dataclass
class Answer:
    mode: str = ''
    value: str = ''


@dataclass
class Evidence:
    kind: str = ''
    name: str = ''
    object: str = ''
    ref: str = ''
    result: str = ''
    value: str = ''


@dataclass
class Record:
    v: int = 0
    schema: str = ''
    action: str = ''
    subject: Subject = field(default_factory=Subject)
    question: str = ''
    answer: Answer = field(default_factory=Answer)
    at: str = ''
    channel: str = ''
    by: str = ''
    assurance: str = ''
    evidence: List[Evidence] = field(default_factory=list)
    ext: Dict[str, Any] = field(default_factory=dict)

    def copy(self):
        """Independent deep copy, for mutation in tests."""
        return dataclasses.replace(
            self, subject=dataclasses.replace(self.subject),
            answer=dataclasses.replace(self.answer),
            evidence=[dataclasses.replace(e) for e in self.evidence],
            ext=json.loads(json.dumps(self.ext)))

    def digest(self):
        return digest_of(encode(self))

    def validate(self):
        validate(self)


# ---------------------------------------------------------------- encoding

def encode(record):
    """Canonical bytes of record. Does not validate."""
    m = {
        'v': record.v, 'schema': record.schema, 'action': record.action,
        'subject': _subject_map(record.subject),
        'answer': _answer_map(record.answer), 'at': record.at,
        'channel': record.channel, 'by': record.by,
        'assurance': record.assurance,
    }
    if record.question:
        m['question'] = record.question
    if record.evidence:
        m['evidence'] = [_evidence_map(e) for e in record.evidence]
    if record.ext:
        m['ext'] = record.ext
    out = []
    _write_value(out, m)
    return ''.join(out).encode('ascii')


def digest_of(canonical):
    """Lowercase hex sha256 of DIGEST_PREFIX and already-canonical bytes."""
    return hashlib.sha256(DIGEST_PREFIX + bytes(canonical)).hexdigest()


def _subject_map(s):
    return {k: v for k, v in (
        ('commit', s.commit), ('branch', s.branch), ('issue', s.issue),
        ('decision', s.decision), ('ref', s.ref)) if v != ''}


def _answer_map(a):
    m = {'mode': a.mode}
    if a.value != '':
        m['value'] = a.value
    return m


def _evidence_map(e):
    m = {'kind': e.kind}
    for k, v in (('name', e.name), ('object', e.object), ('ref', e.ref),
                 ('result', e.result), ('value', e.value)):
        if v != '':
            m[k] = v
    return m


def _encode_evidence(e):
    out = []
    _write_value(out, _evidence_map(e))
    return ''.join(out).encode('ascii')


def _write_value(out, v):
    if isinstance(v, str):
        _write_string(out, v)
    elif isinstance(v, bool):  # before int: bool is an int subclass
        out.append('true' if v else 'false')
    elif isinstance(v, int):
        if not _INT64_MIN <= v <= _INT64_MAX:
            raise ErrSyntax('integer out of range')
        out.append(str(v))
    elif isinstance(v, list):
        out.append('[')
        for i, e in enumerate(v):
            if i:
                out.append(',')
            _write_value(out, e)
        out.append(']')
    elif isinstance(v, dict):
        for k in v:
            if not isinstance(k, str):
                raise ErrSyntax('unsupported key %s' % type(k).__name__)
        out.append('{')
        for i, k in enumerate(sorted(v, key=_utf8_key)):
            if i:
                out.append(',')
            _write_string(out, k)
            out.append(':')
            _write_value(out, v[k])
        out.append('}')
    else:
        raise ErrSyntax('unsupported value %s (no null, no floats)'
                        % type(v).__name__)


def _utf8_key(s):
    try:
        return s.encode('utf-8')
    except UnicodeEncodeError:
        raise ErrSyntax('invalid UTF-8') from None


def _write_string(out, s):
    _utf8_key(s)  # rejects lone surrogates like Go's utf8.ValidString
    out.append('"')
    for ch in s:
        r = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == '\\':
            out.append('\\\\')
        elif r < 0x20 or r > 0x7e:
            if r > 0xffff:
                r -= 0x10000
                out.append('\\u%04x\\u%04x' % (0xd800 + (r >> 10),
                                               0xdc00 + (r & 0x3ff)))
            else:
                out.append('\\u%04x' % r)
        else:
            out.append(ch)
    out.append('"')


# ---------------------------------------------------------------- decoding

def decode(data):
    """Parse data strictly and return a validated Record.

    Check order: parse, unknown field, missing required, v type, version,
    field types, re-encode byte equality (ErrNotCanonical), then validate.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError('decode needs bytes')
    data = bytes(data)
    top = _parse(data)
    if not isinstance(top, dict):
        raise ErrSyntax('not an object')
    r = _from_tree(top)
    if r.v != VERSION:  # version first, so an unknown v is reported as such
        raise ErrUnknownVersion(str(r.v))
    if encode(r) != data:
        raise ErrNotCanonical()
    validate(r)
    return r


def _reject_float(text):
    raise ErrSyntax('floats not allowed')


def _reject_constant(text):
    raise ErrSyntax('floats not allowed (%s)' % text)


def _parse_int(text):
    if text == '-0':
        raise ErrSyntax('non-canonical integer')
    if len(text) > 20:  # also keeps int() away from huge digit strings
        raise ErrSyntax('integer out of range')
    n = int(text)
    if not _INT64_MIN <= n <= _INT64_MAX:
        raise ErrSyntax('integer out of range')
    return n


def _pairs(pairs):
    m = {}
    for k, v in pairs:
        if k in m:
            raise ErrSyntax('duplicate key %s' % json.dumps(k))
        m[k] = v
    return m


def _scan(text):
    """Reject whitespace outside strings and runaway nesting, without
    recursing. Go's parser has no insignificant whitespace."""
    in_str = False
    esc = False
    depth = 0
    for ch in text:
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in ' \t\r\n':
            raise ErrSyntax('unexpected character')
        elif ch in '{[':
            depth += 1
            if depth > MAX_DEPTH + 1:
                raise ErrSyntax('nesting too deep')
        elif ch in '}]':
            depth -= 1


def _walk(v, depth):
    """Go's value(depth) fails for any value deeper than MAX_DEPTH, null
    and lone surrogates (valid pairs were already combined by json)."""
    if depth > MAX_DEPTH:
        raise ErrSyntax('nesting too deep')
    if v is None:
        raise ErrSyntax('null not allowed')
    if isinstance(v, str):
        _check_surrogates(v)
    elif isinstance(v, list):
        for e in v:
            _walk(e, depth + 1)
    elif isinstance(v, dict):
        for k, e in v.items():
            _check_surrogates(k)
            _walk(e, depth + 1)


def _check_surrogates(s):
    for ch in s:
        if '\ud800' <= ch <= '\udfff':
            raise ErrSyntax('lone surrogate')


def _parse(data):
    try:
        text = data.decode('utf-8')  # strict; no BOM strip, no autodetect
    except UnicodeDecodeError:
        raise ErrSyntax('invalid UTF-8') from None
    _scan(text)
    try:
        v = json.loads(text, object_pairs_hook=_pairs, parse_float=_reject_float,
                       parse_constant=_reject_constant, parse_int=_parse_int)
    except ConfirmError:
        raise
    except RecursionError:
        raise ErrSyntax('nesting too deep') from None
    except ValueError as e:
        raise ErrSyntax(str(e)) from None
    _walk(v, 0)
    return v


_TOP_FIELDS = frozenset((
    'v', 'schema', 'action', 'subject', 'question', 'answer', 'at',
    'channel', 'by', 'assurance', 'evidence', 'ext'))
_REQUIRED = ('v', 'schema', 'action', 'subject', 'answer', 'at', 'channel',
             'by', 'assurance')


def _from_tree(top):
    for k in top:
        if k not in _TOP_FIELDS:
            raise ErrUnknownField(json.dumps(k))
    for k in _REQUIRED:
        if k not in top:
            raise ErrMissingRequired(k)
    v = top['v']
    if type(v) is not int:  # bool is not an integer here
        raise ErrSyntax('v must be an integer')
    r = Record(v=v)
    if v != VERSION:
        return r  # decode reports the unknown version
    for key in ('schema', 'action', 'at', 'channel', 'by', 'assurance',
                'question'):
        if key in top:
            if not isinstance(top[key], str):
                raise ErrSyntax('%s must be a string' % key)
            setattr(r, key, top[key])
    r.subject = _subject_from(top['subject'])
    am = top['answer']
    if not isinstance(am, dict):
        raise ErrBadAnswer('answer must be an object')
    _only_keys(am, ErrBadAnswer, ('mode', 'value'))
    r.answer = Answer(mode=_str(am, 'mode', ErrBadAnswer),
                      value=_str(am, 'value', ErrBadAnswer))
    if 'evidence' in top:
        items = top['evidence']
        if not isinstance(items, list) or not items:
            raise ErrBadEvidence('evidence must be a non-empty array when present')
        for item in items:
            if not isinstance(item, dict):
                raise ErrBadEvidence('item must be an object')
            _only_keys(item, ErrBadEvidence,
                       ('kind', 'name', 'object', 'ref', 'result', 'value'))
            r.evidence.append(Evidence(**{
                k: _str(item, k, ErrBadEvidence) for k in (
                    'kind', 'name', 'object', 'ref', 'result', 'value')}))
    if 'ext' in top:
        em = top['ext']
        if not isinstance(em, dict) or not em:
            raise ErrBadExt('ext must be a non-empty object when present')
        r.ext = em
    return r


def _subject_from(x):
    if not isinstance(x, dict):
        raise ErrBadSubject('not an object')
    keys = ('commit', 'branch', 'issue', 'decision', 'ref')
    _only_keys(x, ErrBadSubject, keys)
    return Subject(**{k: _str(x, k, ErrBadSubject) for k in keys})


def _only_keys(m, err, allowed):
    for k in m:
        if k not in allowed:
            raise err('unknown key %s' % json.dumps(k))


def _str(m, key, err):
    if key not in m:
        return ''
    if not isinstance(m[key], str):
        raise err('%s must be a string' % key)
    return m[key]


# -------------------------------------------------------------- validation

_HEX_RE = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})')
_ISSUE_RE = re.compile(r'[A-Za-z0-9._-]+/[A-Za-z0-9._-]+#[1-9][0-9]*')
_SHORT_HEX_RE = re.compile(r'[0-9a-f]{7,64}')
_AT_RE = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})T'
                    r'([0-9]{2}):([0-9]{2}):([0-9]{2})Z')


def validate(r):
    """Check every v1 rule. A record that fails is not a confirmation."""
    if r.v != VERSION:
        raise ErrUnknownVersion(str(r.v))
    if r.schema != SCHEMA:
        raise ErrBadSchema(json.dumps(r.schema))
    if r.action not in ACTIONS:
        raise ErrUnknownAction(json.dumps(r.action))
    if r.channel not in CHANNELS:
        raise ErrUnknownChannel(json.dumps(r.channel))
    _validate_subject(r)
    _validate_answer(r)
    _validate_at(r.at)
    if r.by == '' or any(c in r.by for c in '@ \t\r\n'):
        raise ErrBadBy('need a name, never an email')
    if r.assurance not in ASSURANCES:
        raise ErrBadAssurance(json.dumps(r.assurance))
    _validate_evidence(r)
    for k in r.ext:
        if '.' not in k or k.startswith('.') or k.endswith('.'):
            raise ErrBadExt('key %s is not namespaced' % json.dumps(k))


def _validate_subject(r):
    s = r.subject
    if s == Subject():
        raise ErrBadSubject('empty')
    if s.commit != '' and not _HEX_RE.fullmatch(s.commit):
        raise ErrBadSubject('commit must be a full lowercase hex id')
    if s.issue != '' and not _ISSUE_RE.fullmatch(s.issue):
        raise ErrBadSubject('issue must be owner/repo#n')
    if r.action in ('land', 'push') and s.commit == '':
        raise ErrBadSubject('%s needs subject.commit' % r.action)


def _validate_answer(r):
    a = r.answer
    if a.mode == 'yn':
        if a.value not in ('yes', 'no'):
            raise ErrBadAnswer('yn value must be yes or no')
    elif a.mode == 'typed_sha':
        if not _SHORT_HEX_RE.fullmatch(a.value) or \
                not r.subject.commit.startswith(a.value):
            raise ErrBadAnswer(
                'typed_sha must be a prefix (7+ hex) of subject.commit')
    elif a.mode == 'option':
        if a.value == '':
            raise ErrBadAnswer('option needs a value')
    elif a.mode == 'deny':
        if a.value != '':
            raise ErrBadAnswer('deny has no value')
    else:
        raise ErrBadAnswer('mode %s' % json.dumps(a.mode))


def _validate_at(at):
    """Go: parse RFC 3339, reformat as UTC with Z, compare. The only strings
    that survive are YYYY-MM-DDTHH:MM:SSZ with a real calendar time."""
    m = _AT_RE.fullmatch(at)
    if m:
        year, mon, day, hh, mm, ss = (int(g) for g in m.groups())
        try:
            # Go accepts year 0000 (a leap year); datetime starts at 1. 2000
            # has the same calendar.
            datetime.datetime(year or 2000, mon, day, hh, mm, ss)
            return
        except ValueError:
            pass
    raise ErrBadTime(json.dumps(at))


def _validate_evidence(r):
    prev = None
    for i, e in enumerate(r.evidence):
        if e.kind.startswith('ai-'):
            raise ErrAIEvidence(json.dumps(e.kind))
        if e.kind not in EVIDENCE_KINDS:
            raise ErrBadEvidence('kind %s' % json.dumps(e.kind))
        if not any((e.name, e.object, e.ref, e.result, e.value)):
            raise ErrBadEvidence('%s carries nothing but its kind' % e.kind)
        if e.object != '' and not _HEX_RE.fullmatch(e.object):
            raise ErrBadEvidence('object must be a full lowercase hex id')
        cur = _encode_evidence(e)
        if i > 0 and prev >= cur:
            raise ErrEvidenceOrder()
        prev = cur
