"""Model of the registry review-line grammar and the pre-land model gate (no I/O)."""
import re

SEPARATOR = '; '
LINE = re.compile(r'(review started|CLEAR|NOT CLEAR) ([0-9a-f]{40}) model=(?!model=)([!-:<-~]+)')
CLAUDE_ID = re.compile(r'claude-(opus|sonnet|haiku)-[0-9a-z.-]+')


def parse(line):
    """Return (kind, sha, model) or None; a missing or empty model= is invalid."""
    m = LINE.fullmatch(line)
    return m.groups() if m else None


def canonical(model):
    """Canonical token for a reported id: a concrete Claude id maps to its family
    (claude-opus-5-5 -> opus); a token such as gpt-6.1-sol/medium is kept as is."""
    m = CLAUDE_ID.fullmatch(model)
    return m.group(1) if m else model


def split_evidence(value):
    """The registry stores review lines append-only in one `evidence` value, joined by '; '."""
    return [part for part in value.split(SEPARATOR)] if value else []


def join_evidence(lines):
    return SEPARATOR.join(lines)


def gate(lines, sha, tiers, required=1):
    """Gaps (NEEDS YOU items) for `required` CLEAR stamps on sha; empty list means a landing line may be shown.

    required is the project policy's CLEAR count (an int >= 1; docs/team.md: 1 when policy is silent).
    tiers is the set of canonical tokens the project's tier rule accepts (a bare string is one value).
    Any NOT CLEAR naming sha blocks, even malformed (loose, case-insensitive match); any other
    unparsable line naming sha is a gap. Identical CLEAR lines count once; the count is of distinct
    lines/models, not of reviewers (reviewer identity is not modelled)."""
    if isinstance(required, bool) or not isinstance(required, int) or required < 1:
        raise ValueError('required must be an int >= 1')
    tiers = {tiers} if isinstance(tiers, str) else set(tiers)
    gaps, stamps = [], set()
    for line in lines:
        loose = ' '.join(line.split()).lower()
        if sha.lower() not in loose:
            continue
        p = parse(line)
        if p and p[1] == sha:
            if p[0] == 'NOT CLEAR':
                gaps.append('NOT CLEAR recorded on %s' % sha)
            elif p[0] == 'CLEAR':
                stamps.add(p)
        elif re.search(r'\bnot clear\b', loose):
            gaps.append('malformed NOT CLEAR names %s' % sha)
        else:
            gaps.append('unparsable review line names %s' % sha)
    stamps = sorted(stamps)
    if len(stamps) < required:
        gaps.append('need %d CLEAR stamps with model= on %s, found %d' % (required, sha, len(stamps)))
    for _, _, model in stamps:
        if canonical(model) not in tiers:
            gaps.append('CLEAR model %s does not satisfy tier rule %s' % (model, '/'.join(sorted(tiers))))
    return gaps
