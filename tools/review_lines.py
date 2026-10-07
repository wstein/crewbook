"""Model of the registry review-line grammar and the pre-land model gate (no I/O)."""
import re
import unicodedata

SEPARATOR = '; '
LINE = re.compile(r'(review started|CLEAR|NOT CLEAR) ([0-9a-f]{40})(?: role=[a-z][a-z0-9-]*)? model=(?!model=)([!-:<-~]+)')
CLAUDE_ID = re.compile(r'claude-(opus|sonnet|haiku)-[0-9]+(?:-[0-9]+)*')
FULL_SHA = re.compile(r'(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])')
NOT_CLEAR = re.compile(r'\bnot[\W_]*clear\b')
INVISIBLE = dict.fromkeys(map(ord, '\u200b\u200c\u200d\u200e\u200f\u2060\ufeff\u00ad'))


def parse(line):
    """Return (kind, sha, model) or None; a missing or empty model= is invalid.
    An optional `role=<role>` (note lines and registry evidence) sits between sha and model and is not returned."""
    m = LINE.fullmatch(line)
    return m.groups() if m else None


def split_note(text):
    """A refs/notes/review note holds one entry per line (appended); blank lines are dropped."""
    return [l.strip('\r') for l in text.split('\n') if l.strip()]


def canonical(model):
    """Canonical token for a reported id: a concrete Claude id maps to its family
    (claude-opus-5-5 -> opus); a token such as gpt-6.1-sol/medium is kept as is."""
    m = CLAUDE_ID.fullmatch(model)
    return m.group(1) if m else model


def split_evidence(value):
    """The registry stores review lines append-only in one `evidence` value, joined by '; '."""
    return value.split(SEPARATOR) if value else []


def join_evidence(lines):
    return SEPARATOR.join(lines)


def gate(lines, sha, tiers, required=1):
    """Gaps (NEEDS YOU items) for `required` CLEAR stamps on sha; empty list means a landing line may be shown.

    required is the project policy's CLEAR count (an int >= 1; docs/team.md: 1 when policy is silent).
    tiers is the set of canonical tokens the project's tier rule accepts (a bare string is one value).
    A line "names" sha when it contains it (case-insensitive, whitespace-collapsed). Any NOT CLEAR
    naming sha blocks, even malformed; a malformed NOT CLEAR blocks unless it contains a different
    full 40-hex sha. Any other unparsable line naming sha is a gap.
    Counting key: (sha, canonical model); `opus` and `claude-opus-5-5` are one stamp. Reviewer
    identity is not modelled, so two reviewers recording the same model count once. Fail-closed:
    any CLEAR on sha whose canonical model is outside tiers is a gap, counted or not."""
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('sha must be 40 lowercase hex characters')
    if tiers is None:
        raise ValueError('tiers is required')
    if isinstance(required, bool) or not isinstance(required, int) or required < 1:
        raise ValueError('required must be an int >= 1')
    tiers = {canonical(t) for t in ([tiers] if isinstance(tiers, str) else tiers)}
    gaps, models = [], set()
    # callers pass split_evidence()/split_note() output: one entry per item, no further splitting here
    for line in (l.strip('\r') for l in lines):
        loose = ' '.join(unicodedata.normalize('NFKC', line).translate(INVISIBLE).split()).lower()
        p = parse(line)
        if p and p[1] == sha:
            if p[0] == 'NOT CLEAR':
                gaps.append('NOT CLEAR recorded on %s' % sha)
            elif p[0] == 'CLEAR':
                models.add(canonical(p[2]))
        elif p:
            if sha in loose:
                gaps.append('review line for another sha carries %s inside its role or model token' % sha)
        elif NOT_CLEAR.search(loose):
            if sha in loose or not FULL_SHA.search(loose):
                gaps.append('malformed NOT CLEAR blocks %s' % sha)
        elif sha in loose:
            gaps.append('unparsable review line names %s' % sha)
    if len(models) < required:
        gaps.append('need %d distinct CLEAR models on %s, found %d' % (required, sha, len(models)))
    for model in sorted(models - tiers):
        gaps.append('CLEAR model %s does not satisfy tier rule %s' % (model, ', '.join(sorted(tiers))))
    return gaps
