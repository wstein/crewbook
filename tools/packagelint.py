"""Optional lint: shared agent preamble and duplicated rule paragraphs (warnings only)."""
from collections import Counter
import re

MIN_WORDS = 20      # a paragraph this long or longer counts as rule text
PREAMBLE_LINES = 2  # lines after the title that form the shared preamble
AGENTS = re.compile(r'\.agents/crewbook-[^/]+\.md\Z')


def norm(text):
    return ' '.join(text.split())


def lint(content):
    """Return warning strings for the {path: bytes} package content."""
    texts = {n: b.decode('utf-8', 'replace').split('\n') for n, b in content.items()
             if AGENTS.match(n) or n == 'docs/team.md'}
    agents = sorted(n for n in texts if AGENTS.match(n))
    pre = {n: norm(' '.join(texts[n][2:2 + PREAMBLE_LINES])) for n in agents}
    warnings = []
    if pre:
        shared = Counter(pre.values()).most_common(1)[0][0]
        for n in agents:
            if pre[n] != shared:
                warnings.append('%s:3: preamble differs from the shared one' % n)
    seen = {}
    for n in sorted(texts):
        lines = list(texts[n])
        if n in pre:
            lines[2:2 + PREAMBLE_LINES] = [''] * PREAMBLE_LINES
        start, para = None, []
        for i, line in enumerate(lines + ['']):
            if line.strip():
                if not para:
                    start = i + 1
                para.append(line)
                continue
            text = norm(' '.join(para))
            if para and len(text.split()) >= MIN_WORDS:
                if text in seen:
                    warnings.append('%s:%d: rule paragraph duplicates %s:%d; link instead'
                                    % (n, start, seen[text][0], seen[text][1]))
                else:
                    seen[text] = (n, start)
            para = []
    return warnings
