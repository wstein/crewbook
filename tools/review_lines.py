"""Model of the registry review-line grammar and the pre-land model gate (no I/O)."""
import re

SEPARATOR = '; '
LINE = re.compile(r'(review started|CLEAR|NOT CLEAR) ([0-9a-f]{40}) model=(?!model=)([!-:<-~]+)')
CLAUDE_ID = re.compile(r'claude-(opus|sonnet|haiku)-\d+(?:-\d+)*(?:-\d{8})?')


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
    return value.split(SEPARATOR) if value else []


def join_evidence(lines):
    return SEPARATOR.join(lines)


def _blocks_by_not_clear(loose, sha):
    """A malformed NOT CLEAR blocks unless it clearly names a different revision: it blocks when it
    names no sha (no hex run of 7+ chars) or any hex run is a prefix of sha (or extends it)."""
    runs = re.findall(r'\b[0-9a-f]{7,}\b', re.sub(r'model=\S*', ' ', loose))
    return not runs or any(sha.startswith(r) or r.startswith(sha) for r in runs)


def gate(lines, sha, tiers, required=1):
    """Gaps (NEEDS YOU items) for `required` CLEAR stamps on sha; empty list means a landing line may be shown.

    required is the project policy's CLEAR count (an int >= 1; docs/team.md: 1 when policy is silent).
    tiers is the set of canonical tokens the project's tier rule accepts (a bare string is one value).
    A line "names" sha when it contains it (case-insensitive, whitespace-collapsed). Any NOT CLEAR
    naming sha blocks, even malformed; a malformed NOT CLEAR that names no sha, or only a prefix
    (7+ hex chars) of sha, also blocks. Any other unparsable line naming sha is a gap.
    Counting key: (sha, canonical model); `opus` and `claude-opus-5-5` are one stamp. Reviewer
    identity is not modelled, so two reviewers recording the same model count once. Fail-closed:
    any CLEAR on sha whose canonical model is outside tiers is a gap, counted or not."""
    if isinstance(required, bool) or not isinstance(required, int) or required < 1:
        raise ValueError('required must be an int >= 1')
    tiers = {tiers} if isinstance(tiers, str) else set(tiers)
    gaps, models = [], set()
    for line in lines:
        loose = ' '.join(line.split()).lower()
        p = parse(line)
        if p and p[1] == sha:
            if p[0] == 'NOT CLEAR':
                gaps.append('NOT CLEAR recorded on %s' % sha)
            elif p[0] == 'CLEAR':
                models.add(canonical(p[2]))
        elif p:
            if sha.lower() in p[2].lower():
                gaps.append('review line for another sha carries %s inside its model token' % sha)
        elif re.search(r'\bnot clear\b', loose):
            if sha.lower() in loose or _blocks_by_not_clear(loose, sha):
                gaps.append('malformed NOT CLEAR blocks %s' % sha)
        elif sha.lower() in loose:
            gaps.append('unparsable review line names %s' % sha)
    if len(models) < required:
        gaps.append('need %d distinct CLEAR models on %s, found %d' % (required, sha, len(models)))
    for model in sorted(models - tiers):
        gaps.append('CLEAR model %s does not satisfy tier rule %s' % (model, ', '.join(sorted(tiers))))
    return gaps
